"""
Pipeline API endpoints for generating discussions.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from services.firebase_service import firebase_service
from services.pipeline_service import pipeline_service
from services.memory_service import memory_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


# Mock sections for testing - loaded from joseph.pdf parsing result
import json
import os

_mock_sections_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "joseph_sections.json")
if os.path.exists(_mock_sections_path):
    with open(_mock_sections_path, "r", encoding="utf-8") as f:
        _parsed_data = json.load(f)
        MOCK_SECTIONS = _parsed_data.get("sections", [])
        MOCK_DOCUMENT_TITLE = _parsed_data.get("title", "Untitled Document")
else:
    # Fallback if file doesn't exist
    MOCK_SECTIONS = []
    MOCK_DOCUMENT_TITLE = "Untitled Document"


class GenerateRequest(BaseModel):
    maxAnnotationsPerAgent: int = 12
    targetSeeds: int = 5
    turnsPerDiscussion: int = 4


class GenerateResponse(BaseModel):
    status: str
    message: str
    threadCount: Optional[int] = None


# Store for tracking generation status (in production, use Redis or similar)
generation_status = {}


@router.post("/documents/{document_id}/generate", response_model=GenerateResponse)
async def generate_discussions(
    document_id: str,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start the full pipeline to generate discussions for a document.
    This runs in the background and updates the document when complete.
    """
    # Get document
    document = firebase_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    sections = document.get("parsedContent", {}).get("sections", [])
    if not sections:
        raise HTTPException(status_code=400, detail="Document has no parsed sections")

    # Check if already generating
    if generation_status.get(document_id) == "running":
        return GenerateResponse(
            status="running",
            message="Generation already in progress for this document"
        )

    # Start background generation
    generation_status[document_id] = "running"

    background_tasks.add_task(
        run_pipeline_background,
        document_id,
        sections,
        request.maxAnnotationsPerAgent,
        request.targetSeeds,
        request.turnsPerDiscussion,
    )

    return GenerateResponse(
        status="started",
        message="Discussion generation started. Poll /status endpoint to check progress."
    )


@router.get("/documents/{document_id}/status")
async def get_generation_status(document_id: str):
    """Check the status of discussion generation for a document."""
    status = generation_status.get(document_id, "not_started")
    return {"documentId": document_id, "status": status}


@router.post("/documents/{document_id}/generate-sync", response_model=GenerateResponse)
async def generate_discussions_sync(
    document_id: str,
    request: GenerateRequest,
):
    """
    Run the full pipeline synchronously (for testing/debugging).
    WARNING: This can take 30-60 seconds.
    """
    # Get document
    document = firebase_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    sections = document.get("parsedContent", {}).get("sections", [])
    if not sections:
        raise HTTPException(status_code=400, detail="Document has no parsed sections")

    try:
        result = await pipeline_service.run_full_pipeline(
            document_id=document_id,
            sections=sections,
            max_annotations_per_agent=request.maxAnnotationsPerAgent,
            target_seeds=request.targetSeeds,
            turns_per_discussion=request.turnsPerDiscussion,
        )

        # Save threads
        threads = result.get("threads", [])
        for thread in threads:
            firebase_service.save_thread(thread)

        return GenerateResponse(
            status="complete",
            message=f"Generated {len(threads)} threads",
            threadCount=len(threads),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


async def run_pipeline_background(
    document_id: str,
    sections: list[dict],
    max_annotations: int,
    target_seeds: int,
    turns: int,
):
    """Background task to run the pipeline."""
    try:
        result = await pipeline_service.run_full_pipeline(
            document_id=document_id,
            sections=sections,
            max_annotations_per_agent=max_annotations,
            target_seeds=target_seeds,
            turns_per_discussion=turns,
        )

        # Save threads
        threads = result.get("threads", [])
        for thread in threads:
            firebase_service.save_thread(thread)

        generation_status[document_id] = f"complete:{len(threads)}"
        print(f"[Pipeline] Background generation complete: {len(threads)} threads")

    except Exception as e:
        generation_status[document_id] = f"error:{str(e)}"
        print(f"[Pipeline] Background generation failed: {e}")


@router.post("/test", response_model=GenerateResponse)
async def test_pipeline_with_mock_data():
    """
    Test the pipeline with mock data (no PDF upload needed).
    Uses the built-in mock sections.
    """
    document_id = "test_doc_001"

    try:
        print("[Test] Starting pipeline with mock data...")
        result = await pipeline_service.run_full_pipeline(
            document_id=document_id,
            sections=MOCK_SECTIONS,
            max_annotations_per_agent=8,  # Smaller for faster test
            target_seeds=4,
            turns_per_discussion=3,
        )

        threads = result.get("threads", [])

        # Save threads to in-memory storage
        for thread in threads:
            firebase_service.save_thread(thread)

        # Print sample output for debugging
        print(f"\n[Test] Generated {len(threads)} threads:")
        for t in threads:
            print(f"  - {t['threadType']}: {t['tensionPoint'][:50]}...")
            print(f"    Participants: {t['participants']}")
            print(f"    Messages: {len(t['messages'])}")

        return GenerateResponse(
            status="complete",
            message=f"Test complete! Generated {len(threads)} threads",
            threadCount=len(threads),
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline test failed: {str(e)}")


class DetailedPipelineResponse(BaseModel):
    """Detailed response with all intermediate pipeline results."""
    status: str
    annotations: dict  # {agentId: [annotations]}
    seeds: list
    threads: list
    timings: dict  # {phase: seconds}


@router.post("/test-with-logging", response_model=DetailedPipelineResponse)
async def test_pipeline_with_logging():
    """
    Test the pipeline with mock data and return all intermediate results.
    This is for debugging/dashboard purposes.
    """
    import time

    document_id = "test_doc_001"
    timings = {}

    try:
        print("[Pipeline Dashboard] Starting pipeline with detailed logging...")

        # Initialize memory for all agents
        memory_service.initialize_for_document(document_id)

        # Phase 1: Annotations
        start_time = time.time()
        print("[Phase 1] Generating annotations from all agents...")
        annotations_by_agent = await pipeline_service._phase1_annotations(
            document_id, MOCK_SECTIONS, max_per_agent=8
        )
        timings["phase1"] = round(time.time() - start_time, 2)
        print(f"[Phase 1] Complete in {timings['phase1']}s")
        for agent_id, anns in annotations_by_agent.items():
            print(f"  - {agent_id}: {len(anns)} annotations")

        # Phase 2: Seed Formation
        start_time = time.time()
        print("[Phase 2] Forming discussion seeds...")
        seeds = await pipeline_service._phase2_seed_formation(
            annotations_by_agent, MOCK_SECTIONS, target_count=4
        )
        timings["phase2"] = round(time.time() - start_time, 2)
        print(f"[Phase 2] Complete in {timings['phase2']}s - {len(seeds)} seeds formed")

        # Phase 3-4: Thread Generation
        start_time = time.time()
        print("[Phase 3-4] Generating discussion threads...")
        threads = await pipeline_service._phase3_4_thread_generation(
            document_id, seeds, MOCK_SECTIONS, turns_per_discussion=3
        )
        timings["phase3_4"] = round(time.time() - start_time, 2)
        print(f"[Phase 3-4] Complete in {timings['phase3_4']}s - {len(threads)} threads")

        # Save threads
        for thread in threads:
            firebase_service.save_thread(thread)

        # Return full thread data for frontend
        return DetailedPipelineResponse(
            status="complete",
            annotations=annotations_by_agent,
            seeds=seeds,
            threads=threads,  # Full thread data including anchor, messages, etc.
            timings=timings,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


@router.post("/documents/{document_id}/generate-with-logging", response_model=DetailedPipelineResponse)
async def generate_with_logging(
    document_id: str,
    request: GenerateRequest,
):
    """
    Run the full pipeline on a real document with detailed logging.
    Returns all intermediate results for debugging/dashboard.
    """
    import time

    # Get document
    document = firebase_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    sections = document.get("parsedContent", {}).get("sections", [])
    if not sections:
        raise HTTPException(status_code=400, detail="Document has no parsed sections")

    timings = {}

    try:
        print(f"[Pipeline Dashboard] Starting pipeline for document: {document_id}")
        print(f"[Pipeline Dashboard] Document has {len(sections)} sections")

        # Initialize memory for all agents
        memory_service.initialize_for_document(document_id)

        # Phase 1: Annotations
        start_time = time.time()
        print("[Phase 1] Generating annotations from all agents...")
        annotations_by_agent = await pipeline_service._phase1_annotations(
            document_id, sections, max_per_agent=request.maxAnnotationsPerAgent
        )
        timings["phase1"] = round(time.time() - start_time, 2)
        print(f"[Phase 1] Complete in {timings['phase1']}s")
        for agent_id, anns in annotations_by_agent.items():
            print(f"  - {agent_id}: {len(anns)} annotations")

        # Phase 2: Seed Formation
        start_time = time.time()
        print("[Phase 2] Forming discussion seeds...")
        seeds = await pipeline_service._phase2_seed_formation(
            annotations_by_agent, sections, target_count=request.targetSeeds
        )
        timings["phase2"] = round(time.time() - start_time, 2)
        print(f"[Phase 2] Complete in {timings['phase2']}s - {len(seeds)} seeds formed")

        # Phase 3-4: Thread Generation
        start_time = time.time()
        print("[Phase 3-4] Generating discussion threads...")
        threads = await pipeline_service._phase3_4_thread_generation(
            document_id, seeds, sections, turns_per_discussion=request.turnsPerDiscussion
        )
        timings["phase3_4"] = round(time.time() - start_time, 2)
        print(f"[Phase 3-4] Complete in {timings['phase3_4']}s - {len(threads)} threads")

        # Save threads
        for thread in threads:
            firebase_service.save_thread(thread)

        # Return full thread data for frontend
        return DetailedPipelineResponse(
            status="complete",
            annotations=annotations_by_agent,
            seeds=seeds,
            threads=threads,  # Full thread data including anchor, messages, etc.
            timings=timings,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")
