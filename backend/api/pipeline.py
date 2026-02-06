"""
Pipeline API endpoints for generating discussions.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from services.firebase_service import firebase_service
from services.pipeline_service import pipeline_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


# Mock sections for testing (same as frontend mockData)
MOCK_SECTIONS = [
    {
        "sectionId": "section_0",
        "title": "Abstract",
        "content": "This study investigates the challenges undergraduate students face when engaging with academic texts. Through a mixed-methods approach involving 45 participants, we examine how students approach critical reading tasks and identify key barriers to deep comprehension. Our findings reveal that students often struggle with critical analysis of academic texts, tending to focus on surface-level understanding rather than engaging with the underlying arguments and assumptions. We propose a framework for scaffolded reading instruction that addresses these challenges.",
        "order": 0
    },
    {
        "sectionId": "section_1",
        "title": "Introduction",
        "content": "Academic reading is a fundamental skill for success in higher education. However, many undergraduate students enter university unprepared for the demands of scholarly texts. Previous research has shown that effective academic reading requires not only comprehension of content but also the ability to critically evaluate arguments, identify assumptions, and connect ideas across texts.\n\nOur study reveals that students often struggle with critical analysis of academic texts. This difficulty manifests in several ways: students may accept claims without questioning evidence, fail to recognize implicit assumptions, or struggle to synthesize information from multiple sources. These challenges are particularly acute for first-generation college students and those from non-English speaking backgrounds.\n\nThe purpose of this study is to understand the specific barriers students face and to develop interventions that support deeper engagement with academic texts. We adopt a sociocultural perspective that views reading as a situated practice shaped by disciplinary norms and expectations.",
        "order": 1
    },
    {
        "sectionId": "section_2",
        "title": "Methods",
        "content": "We recruited 45 participants from undergraduate courses across three disciplines: psychology, biology, and history. Participants ranged from first-year to senior students, with a mean age of 20.3 years. The sample included 28 female and 17 male students, with 12 identifying as first-generation college students.\n\nData collection involved three components: (1) think-aloud protocols during reading tasks, (2) semi-structured interviews about reading strategies, and (3) analysis of annotated texts. Participants were asked to read and respond to two academic articles typical of their discipline.\n\nQualitative data were analyzed using thematic analysis following Braun and Clarke's six-phase approach. Two researchers independently coded transcripts, achieving an inter-rater reliability of 0.85. Quantitative measures of reading comprehension were analyzed using descriptive statistics and correlation analysis.",
        "order": 2
    },
    {
        "sectionId": "section_3",
        "title": "Results",
        "content": "Our analysis revealed three primary themes related to students' reading challenges:\n\nTheme 1: Surface-Level Processing\nThe majority of students (78%) demonstrated a tendency toward surface-level processing, focusing on extracting facts rather than evaluating arguments. Students frequently reported feeling overwhelmed by academic vocabulary and complex sentence structures.\n\nTheme 2: Limited Critical Questioning\nOnly 23% of students spontaneously questioned the claims or evidence presented in the texts. When prompted, many students expressed uncertainty about what constitutes valid criticism of academic work, with comments such as \"Who am I to question the expert?\"\n\nTheme 3: Disconnected Reading\nStudents rarely connected reading to their own experiences or prior knowledge. Reading was often viewed as a task to complete rather than an opportunity for intellectual engagement. This was particularly evident in students' annotations, which tended to focus on definitions rather than reactions or questions.\n\nCorrelation analysis revealed significant relationships between critical reading behaviors and academic performance (r = 0.67, p < 0.001), suggesting that reading skills are indeed predictive of broader academic success.",
        "order": 3
    },
    {
        "sectionId": "section_4",
        "title": "Discussion",
        "content": "Our findings highlight the need for explicit instruction in critical reading strategies. The prevalence of surface-level processing suggests that students may not understand what deeper engagement looks like or may lack the strategies to achieve it.\n\nThe reluctance to question academic texts points to broader issues of academic identity and authority. Students may need support in developing the confidence to position themselves as legitimate participants in scholarly discourse.\n\nSeveral limitations should be noted. First, our sample was drawn from a single institution, limiting generalizability. Second, the think-aloud methodology may have altered natural reading behaviors. Third, disciplinary differences in reading practices were not fully explored.\n\nFuture research should investigate the effectiveness of specific interventions, including collaborative reading activities, explicit strategy instruction, and the use of AI-assisted tools to scaffold critical analysis. Longitudinal studies tracking the development of reading skills across the undergraduate years would also be valuable.",
        "order": 4
    }
]


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

        # Phase 1: Annotations
        start_time = time.time()
        print("[Phase 1] Generating annotations from all agents...")
        annotations_by_agent = await pipeline_service._phase1_annotations(
            MOCK_SECTIONS, max_per_agent=8
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

        # Phase 1: Annotations
        start_time = time.time()
        print("[Phase 1] Generating annotations from all agents...")
        annotations_by_agent = await pipeline_service._phase1_annotations(
            sections, max_per_agent=request.maxAnnotationsPerAgent
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
