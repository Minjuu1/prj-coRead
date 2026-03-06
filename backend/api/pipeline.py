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
    MOCK_SECTIONS = []
    MOCK_DOCUMENT_TITLE = "Untitled Document"


class GenerateRequest(BaseModel):
    annotationsPerAgent: int = 7
    turnsPerDiscussion: int = 4


class GenerateResponse(BaseModel):
    status: str
    message: str
    threadCount: Optional[int] = None


# Store for tracking generation status
generation_status = {}


@router.post("/documents/{document_id}/generate", response_model=GenerateResponse)
async def generate_discussions(
    document_id: str,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
):
    """Start the full pipeline to generate discussions for a document."""
    document = firebase_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    sections = document.get("parsedContent", {}).get("sections", [])
    if not sections:
        raise HTTPException(status_code=400, detail="Document has no parsed sections")

    if generation_status.get(document_id) == "running":
        return GenerateResponse(
            status="running",
            message="Generation already in progress for this document"
        )

    generation_status[document_id] = "running"

    background_tasks.add_task(
        run_pipeline_background,
        document_id,
        sections,
        request.annotationsPerAgent,
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
    """Run the full pipeline synchronously (for testing/debugging)."""
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
            annotations_per_agent=request.annotationsPerAgent,
            turns_per_discussion=request.turnsPerDiscussion,
        )

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
    annotations_per_agent: int,
    turns: int,
):
    """Background task to run the pipeline."""
    try:
        result = await pipeline_service.run_full_pipeline(
            document_id=document_id,
            sections=sections,
            annotations_per_agent=annotations_per_agent,
            turns_per_discussion=turns,
        )

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
    """Test the pipeline with mock data (no PDF upload needed)."""
    document_id = "test_doc_001"

    try:
        print("[Test] Starting pipeline with mock data...")
        result = await pipeline_service.run_full_pipeline(
            document_id=document_id,
            sections=MOCK_SECTIONS,
            annotations_per_agent=7,
            turns_per_discussion=3,
        )

        threads = result.get("threads", [])
        for thread in threads:
            firebase_service.save_thread(thread)

        print(f"\n[Test] Generated {len(threads)} threads:")
        for t in threads:
            print(f"  - {t['threadType']}: {len(t['messages'])} messages, participants: {t['participants']}")

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
    reactions: list = []  # Phase 2 cross-reading reactions
    strongReactions: list = []  # Filtered strong reactions
    threads: list
    timings: dict  # {phase: seconds}


@router.post("/test-with-logging", response_model=DetailedPipelineResponse)
async def test_pipeline_with_logging():
    """Test the pipeline with mock data and return all intermediate results."""
    import time

    document_id = "test_doc_001"
    timings = {}

    try:
        print("[Pipeline Dashboard] Starting pipeline with detailed logging...")

        memory_service.initialize_for_document(document_id)

        # Phase 1: Reading
        start_time = time.time()
        print("[Phase 1] Generating annotations from all agents...")
        annotations_by_agent = await pipeline_service._phase1_reading(
            document_id, MOCK_SECTIONS, annotations_per_agent=7
        )
        visible = pipeline_service._store_visible_annotations(
            document_id, annotations_by_agent, MOCK_SECTIONS
        )
        timings["phase1_reading"] = round(time.time() - start_time, 2)
        print(f"[Phase 1] Complete in {timings['phase1_reading']}s")
        for agent_id, anns in annotations_by_agent.items():
            print(f"  - {agent_id}: {len(anns)} annotations")

        # Phase 2: Cross-Reading
        start_time = time.time()
        print("[Phase 2] Cross-reading...")
        all_reactions = await pipeline_service._phase2_cross_reading(
            document_id, annotations_by_agent, MOCK_SECTIONS
        )
        timings["phase2_cross_reading"] = round(time.time() - start_time, 2)
        print(f"[Phase 2] Complete in {timings['phase2_cross_reading']}s - {len(all_reactions)} reactions")

        firebase_service.save_reactions(document_id, all_reactions)

        # Filtering (between Phase 2 → 3)
        strong_reactions = pipeline_service._filter_reactions(all_reactions)
        starters = pipeline_service._select_discussion_starters(
            strong_reactions, annotations_by_agent
        )
        print(f"[Filtering] {len(strong_reactions)}/{len(all_reactions)} strong → {len(starters)} starters")

        # Phase 3: Discussion Generation
        start_time = time.time()
        print("[Phase 3] Generating discussions...")
        threads = await pipeline_service._phase3_discussion_generation(
            document_id, starters, annotations_by_agent, MOCK_SECTIONS, turns_per_discussion=3
        )
        timings["phase3_discussion"] = round(time.time() - start_time, 2)
        print(f"[Phase 3] Complete in {timings['phase3_discussion']}s - {len(threads)} threads")

        for thread in threads:
            firebase_service.save_thread(thread)

        return DetailedPipelineResponse(
            status="complete",
            annotations=annotations_by_agent,
            reactions=all_reactions,
            strongReactions=strong_reactions,
            threads=threads,
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
    """Run the full pipeline on a real document with detailed logging."""
    import time

    document = firebase_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    sections = document.get("parsedContent", {}).get("sections", [])
    if not sections:
        raise HTTPException(status_code=400, detail="Document has no parsed sections")

    timings = {}

    try:
        print(f"[Pipeline Dashboard] Starting pipeline for document: {document_id}")

        memory_service.initialize_for_document(document_id)

        # Phase 1: Reading
        start_time = time.time()
        annotations_by_agent = await pipeline_service._phase1_reading(
            document_id, sections, annotations_per_agent=request.annotationsPerAgent
        )
        visible = pipeline_service._store_visible_annotations(
            document_id, annotations_by_agent, sections
        )
        timings["phase1_reading"] = round(time.time() - start_time, 2)

        # Phase 2: Cross-Reading
        start_time = time.time()
        all_reactions = await pipeline_service._phase2_cross_reading(
            document_id, annotations_by_agent, sections
        )
        timings["phase2_cross_reading"] = round(time.time() - start_time, 2)

        firebase_service.save_reactions(document_id, all_reactions)

        # Filtering (between Phase 2 → 3)
        strong_reactions = pipeline_service._filter_reactions(all_reactions)
        starters = pipeline_service._select_discussion_starters(
            strong_reactions, annotations_by_agent
        )

        # Phase 3: Discussion Generation
        start_time = time.time()
        threads = await pipeline_service._phase3_discussion_generation(
            document_id, starters, annotations_by_agent, sections,
            turns_per_discussion=request.turnsPerDiscussion
        )
        timings["phase3_discussion"] = round(time.time() - start_time, 2)

        for thread in threads:
            firebase_service.save_thread(thread)

        return DetailedPipelineResponse(
            status="complete",
            annotations=annotations_by_agent,
            reactions=all_reactions,
            strongReactions=strong_reactions,
            threads=threads,
            timings=timings,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


@router.get("/documents/{document_id}/annotations")
async def get_document_annotations(document_id: str):
    """Get all visible annotations for a document."""
    annotations = firebase_service.get_document_annotations(document_id)
    return annotations


@router.get("/documents/{document_id}/reactions")
async def get_document_reactions(document_id: str):
    """Get all cross-reading reactions for a document."""
    reactions = firebase_service.get_document_reactions(document_id)
    return reactions
