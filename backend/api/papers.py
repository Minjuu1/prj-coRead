import logging
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from pipeline.ingestion import run_ingestion
from pipeline.agent_gen import generate_agents
from pipeline.agent_reading import run_agent_reading
from pipeline.cross_reading import find_contested_excerpts
from pipeline.discussion_formation import form_discussions
from db.vector_store import add_chunks
from db.firestore import (
    save_chunks, save_paper_meta, save_threads, get_threads_by_paper,
    save_agents, get_agents_by_paper, save_annotations,
)

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

router = APIRouter()

# paper_id → status ("processing" | "ready" | "error")
_status: dict[str, str] = {}
# paper_id → chunks (for /chunks endpoint)
_chunks: dict[str, list] = {}
# paper_id → threads (in-memory cache)
_threads: dict[str, list] = {}
# paper_id → agents (in-memory cache)
_agents: dict[str, list] = {}


# ──────────────────────────────────────────────
# Background pipeline
# ──────────────────────────────────────────────

def _run_pipeline(paper_id: str, pdf_path: str) -> None:
    try:
        _status[paper_id] = "processing"
        logger.info(f"[pipeline] starting for {paper_id}")

        chunks = run_ingestion(paper_id, pdf_path)
        _chunks[paper_id] = chunks

        if chunks:
            add_chunks(paper_id, chunks)
            save_chunks(paper_id, chunks)

        logger.info(f"[pipeline] generating agents for {paper_id}")
        agents = generate_agents(paper_id, chunks)
        _agents[paper_id] = agents
        if agents:
            save_agents(paper_id, agents)

        logger.info(f"[pipeline] agent reading for {paper_id}")
        annotations = run_agent_reading(agents, chunks)
        if annotations:
            save_annotations(paper_id, annotations)

        logger.info(f"[pipeline] cross-reading contested excerpts for {paper_id}")
        contested_excerpts = find_contested_excerpts(annotations, chunks)

        logger.info(f"[pipeline] forming discussions for {paper_id}")
        threads = form_discussions(paper_id, contested_excerpts, agents)
        _threads[paper_id] = threads
        if threads:
            save_threads(paper_id, threads)

        save_paper_meta(paper_id, {
            "status": "ready",
            "chunkCount": len(chunks),
            "agentCount": len(agents),
            "threadCount": len(threads),
        })
        _status[paper_id] = "ready"
        logger.info(
            f"[pipeline] done — {len(chunks)} chunks, {len(agents)} agents, "
            f"{len(threads)} threads for {paper_id}"
        )
    except Exception as e:
        logger.error(f"[pipeline] error for {paper_id}: {e}", exc_info=True)
        _status[paper_id] = "error"


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.post("/upload")
async def upload_paper(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """PDF 업로드 → 파이프라인 비동기 실행"""
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다")

    os.makedirs(DATA_DIR, exist_ok=True)

    paper_id = str(uuid.uuid4())
    file_path = os.path.join(DATA_DIR, f"{paper_id}.pdf")

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    save_paper_meta(paper_id, {"status": "processing", "url": f"http://localhost:8000/papers/{paper_id}/pdf"})
    background_tasks.add_task(_run_pipeline, paper_id, file_path)

    return {
        "paperId": paper_id,
        "url": f"http://localhost:8000/papers/{paper_id}/pdf",
        "status": "processing",
    }


@router.get("/{paper_id}/pdf")
async def get_paper_pdf(paper_id: str):
    """PDF 파일 서빙"""
    file_path = os.path.join(DATA_DIR, f"{paper_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(file_path, media_type="application/pdf")


@router.get("/{paper_id}/status")
async def get_paper_status(paper_id: str):
    """파이프라인 진행 상태 polling"""
    status = _status.get(paper_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"paperId": paper_id, "status": status}


@router.post("/{paper_id}/reprocess")
async def reprocess_paper(paper_id: str, background_tasks: BackgroundTasks):
    """이미 업로드된 PDF에 대해 파이프라인을 다시 실행"""
    file_path = os.path.join(DATA_DIR, f"{paper_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found — upload first")

    if _status.get(paper_id) == "processing":
        return {"paperId": paper_id, "status": "processing", "message": "Already running"}

    _chunks.pop(paper_id, None)
    _threads.pop(paper_id, None)
    _agents.pop(paper_id, None)
    _status[paper_id] = "processing"

    background_tasks.add_task(_run_pipeline, paper_id, file_path)
    return {"paperId": paper_id, "status": "processing"}


@router.get("/{paper_id}/agents")
async def get_paper_agents(paper_id: str):
    """이 논문의 dynamic agents 반환"""
    if paper_id in _agents:
        return {"paperId": paper_id, "agents": _agents[paper_id]}
    try:
        agents = get_agents_by_paper(paper_id)
    except Exception as e:
        logger.warning(f"[agents] Firestore fallback failed for {paper_id}: {e}")
        agents = []
    _agents[paper_id] = agents
    return {"paperId": paper_id, "agents": agents}


@router.get("/{paper_id}/threads")
async def get_paper_threads(paper_id: str):
    """Thread 목록 반환 (in-memory 우선, 없으면 Firestore fallback)"""
    status = _status.get(paper_id)
    if status == "processing":
        return {"paperId": paper_id, "status": "processing", "threads": []}
    if paper_id in _threads:
        return {"paperId": paper_id, "status": status or "ready", "threads": _threads[paper_id]}
    try:
        threads = get_threads_by_paper(paper_id)
    except Exception as e:
        logger.warning(f"[threads] Firestore fallback failed for {paper_id}: {e}")
        threads = []
    _threads[paper_id] = threads
    return {"paperId": paper_id, "status": status or "ready", "threads": threads}


@router.get("/{paper_id}/chunks")
async def get_paper_chunks(paper_id: str):
    """파싱된 청크 목록 반환"""
    if paper_id not in _chunks:
        status = _status.get(paper_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Paper not found")
        if status == "processing":
            return {"paperId": paper_id, "status": "processing", "chunks": []}
        raise HTTPException(status_code=404, detail="Chunks not available")
    return {"paperId": paper_id, "status": _status.get(paper_id, "ready"), "chunks": _chunks[paper_id]}
