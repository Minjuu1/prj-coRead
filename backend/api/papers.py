import asyncio
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, Response, StreamingResponse

from pipeline.ingestion import run_ingestion
from pipeline.agent_gen import generate_agents
from pipeline.agent_reading import run_agent_reading
from pipeline.cross_reading import find_contested_excerpts
from pipeline.discussion_formation import form_discussions
from db.vector_store import add_chunks
from db.firestore import (
    save_chunks, save_paper_meta, get_paper_meta, save_threads, get_threads_by_paper,
    save_agents, get_agents_by_paper, save_annotations, get_papers_by_user,
)
from db import storage

logger = logging.getLogger(__name__)

# Fallback local storage (used when Firebase Storage is unavailable)
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
# paper_id → list of SSE events (appended by pipeline thread, read by SSE endpoint)
_progress: dict[str, list[str]] = {}


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _local_pdf_path(paper_id: str) -> str:
    return os.path.join(DATA_DIR, f"{paper_id}.pdf")


def _write_temp_pdf(paper_id: str, contents: bytes) -> str:
    """PDF bytes를 임시 파일로 저장하고 경로를 반환."""
    tmp = tempfile.NamedTemporaryFile(
        suffix=f"_{paper_id}.pdf", delete=False, dir=tempfile.gettempdir()
    )
    tmp.write(contents)
    tmp.close()
    return tmp.name


# ──────────────────────────────────────────────
# Background pipeline
# ──────────────────────────────────────────────

def _emit(paper_id: str, stage: str, **kwargs) -> None:
    """파이프라인 스레드에서 SSE 이벤트를 진행 큐에 추가."""
    event = json.dumps({"stage": stage, **kwargs})
    _progress.setdefault(paper_id, []).append(event)


def _run_pipeline(paper_id: str, pdf_path: str, cleanup: bool = False) -> None:
    try:
        _status[paper_id] = "processing"
        _progress[paper_id] = []
        logger.info(f"[pipeline] starting for {paper_id}")

        chunks, metadata = run_ingestion(paper_id, pdf_path)
        _chunks[paper_id] = chunks
        if chunks:
            add_chunks(paper_id, chunks)
            save_chunks(paper_id, chunks)
        _emit(paper_id, "ingestion", count=len(chunks))

        logger.info(f"[pipeline] generating agents for {paper_id}")
        agents = generate_agents(paper_id, chunks)
        _agents[paper_id] = agents
        if agents:
            save_agents(paper_id, agents)
        _emit(paper_id, "agents", count=len(agents))

        logger.info(f"[pipeline] agent reading for {paper_id}")
        annotations = run_agent_reading(agents, chunks)
        if annotations:
            save_annotations(paper_id, annotations)
        _emit(paper_id, "reading", count=len(annotations))

        logger.info(f"[pipeline] cross-reading contested excerpts for {paper_id}")
        contested_excerpts = find_contested_excerpts(annotations, chunks)
        _emit(paper_id, "cross_reading", count=len(contested_excerpts))

        logger.info(f"[pipeline] forming discussions for {paper_id}")
        threads = form_discussions(paper_id, contested_excerpts, agents)
        _threads[paper_id] = threads
        if threads:
            save_threads(paper_id, threads)
        _emit(paper_id, "discussions", count=len(threads))

        save_paper_meta(paper_id, {
            "status": "ready",
            "title": metadata.get("title", ""),
            "authors": metadata.get("authors", []),
            "abstract": metadata.get("abstract", ""),
            "chunkCount": len(chunks),
            "agentCount": len(agents),
            "threadCount": len(threads),
        })
        _status[paper_id] = "ready"
        _emit(paper_id, "done", status="ready")
        logger.info(
            f"[pipeline] done — {len(chunks)} chunks, {len(agents)} agents, "
            f"{len(threads)} threads for {paper_id}"
        )
    except Exception as e:
        logger.error(f"[pipeline] error for {paper_id}: {e}", exc_info=True)
        _status[paper_id] = "error"
        _emit(paper_id, "done", status="error", message=str(e))
    finally:
        if cleanup and os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info(f"[pipeline] cleaned up temp file {pdf_path}")


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.get("")
async def list_papers(userId: str = Query(...)):
    """유저의 논문 라이브러리 목록 반환"""
    papers = get_papers_by_user(userId)
    return {"papers": papers}


@router.get("/{paper_id}/meta")
async def get_paper(paper_id: str):
    """단일 논문 메타데이터 반환 (ReaderPage URL param용)"""
    meta = get_paper_meta(paper_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    meta["paperId"] = paper_id
    return meta


@router.post("/upload")
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    userId: str = Form(default="anonymous"),
):
    """PDF 업로드 → Firebase Storage 저장 → 파이프라인 비동기 실행"""
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다")

    paper_id = str(uuid.uuid4())
    contents = await file.read()

    if storage.is_available():
        # Firebase Storage에 업로드, 파이프라인용 임시 파일 생성
        uploaded = storage.upload_pdf(paper_id, contents)
        pdf_path = _write_temp_pdf(paper_id, contents)
        cleanup = uploaded is not None  # 업로드 실패 시 temp 파일 보존
        if not uploaded:
            logger.warning(f"[upload] Storage upload failed for {paper_id} — keeping local temp file")
    else:
        # Fallback: 로컬 저장
        logger.warning("[upload] Storage unavailable — falling back to local storage")
        os.makedirs(DATA_DIR, exist_ok=True)
        pdf_path = _local_pdf_path(paper_id)
        with open(pdf_path, "wb") as f:
            f.write(contents)
        cleanup = False

    save_paper_meta(paper_id, {
        "status": "processing",
        "filename": file.filename,
        "userId": userId,
        "uploadedAt": datetime.now(timezone.utc).isoformat(),
    })
    background_tasks.add_task(_run_pipeline, paper_id, pdf_path, cleanup)

    return {"paperId": paper_id, "status": "processing"}


@router.get("/{paper_id}/pdf")
async def get_paper_pdf(paper_id: str):
    """PDF 서빙 — Firebase Storage 우선, 없으면 로컬 fallback"""
    if storage.is_available():
        data = storage.download_pdf(paper_id)
        if data:
            return Response(content=data, media_type="application/pdf")
        # Storage에 없으면 로컬 fallback (Storage 설정 전 업로드된 파일)

    file_path = _local_pdf_path(paper_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(file_path, media_type="application/pdf")


@router.get("/{paper_id}/pipeline-stream")
async def stream_pipeline(paper_id: str):
    """파이프라인 진행상황 SSE 스트림."""
    async def generate():
        sent = 0
        while True:
            events = _progress.get(paper_id, [])
            while sent < len(events):
                yield f"data: {events[sent]}\n\n"
                sent += 1
            # done 이벤트가 전송됐으면 종료
            if sent > 0:
                last = json.loads(events[sent - 1])
                if last.get("stage") == "done":
                    break
            # 아직 파이프라인 시작 전이면 error로 처리
            if _status.get(paper_id) == "error" and sent == 0:
                yield f"data: {json.dumps({'stage': 'done', 'status': 'error'})}\n\n"
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
    if _status.get(paper_id) == "processing":
        return {"paperId": paper_id, "status": "processing", "message": "Already running"}

    if storage.is_available():
        data = storage.download_pdf(paper_id)
        if not data:
            raise HTTPException(status_code=404, detail="PDF not found in storage — upload first")
        pdf_path = _write_temp_pdf(paper_id, data)
        cleanup = True
    else:
        pdf_path = _local_pdf_path(paper_id)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF not found — upload first")
        cleanup = False

    _chunks.pop(paper_id, None)
    _threads.pop(paper_id, None)
    _agents.pop(paper_id, None)
    _status[paper_id] = "processing"

    background_tasks.add_task(_run_pipeline, paper_id, pdf_path, cleanup)
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
