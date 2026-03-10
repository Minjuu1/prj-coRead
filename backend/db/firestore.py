"""
Firebase Firestore 연결 + 청크/annotation 저장/조회.

스키마:
  papers/{paperId}
    chunks/{chunkId}
    annotations/{annotationId}
    threads/{threadId}

Firebase credentials 없거나 권한 에러가 나면 모든 작업을 no-op/빈값으로 처리 (in-memory only mode).
"""
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

_CRED_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firebase-credentials.json")
_db = None
_firebase_available: Optional[bool] = None  # None = not checked yet


def _get_db():
    global _db, _firebase_available
    if _firebase_available is False:
        return None
    if _db is not None:
        return _db
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore as fs
        if not os.path.exists(_CRED_PATH):
            logger.warning("[firestore] credentials not found — running in-memory only mode")
            _firebase_available = False
            return None
        if not firebase_admin._apps:
            cred = credentials.Certificate(_CRED_PATH)
            firebase_admin.initialize_app(cred)
        _db = fs.client()
        _firebase_available = True
        logger.info("[firestore] connected")
        return _db
    except Exception as e:
        logger.warning(f"[firestore] init failed ({e}) — running in-memory only mode")
        _firebase_available = False
        return None


def _disable(e: Exception) -> None:
    """권한/네트워크 에러 시 Firestore를 비활성화하고 경고 로그."""
    global _firebase_available
    _firebase_available = False
    logger.warning(f"[firestore] disabled due to error: {type(e).__name__}: {e}")


# ──────────────────────────────────────────────
# Chunks
# ──────────────────────────────────────────────

def save_chunks(paper_id: str, chunks: List[dict]) -> None:
    db = _get_db()
    if db is None:
        return
    try:
        batch = db.batch()
        col = db.collection("papers").document(paper_id).collection("chunks")
        for chunk in chunks:
            batch.set(col.document(chunk["id"]), chunk)
        batch.commit()
        logger.info(f"[firestore] saved {len(chunks)} chunks for paper {paper_id}")
    except Exception as e:
        _disable(e)


def get_chunks(paper_id: str) -> List[dict]:
    db = _get_db()
    if db is None:
        return []
    try:
        docs = db.collection("papers").document(paper_id).collection("chunks").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        _disable(e)
        return []


def get_chunk(paper_id: str, chunk_id: str) -> Optional[dict]:
    db = _get_db()
    if db is None:
        return None
    try:
        doc = db.collection("papers").document(paper_id).collection("chunks").document(chunk_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        _disable(e)
        return None


# ──────────────────────────────────────────────
# Paper metadata
# ──────────────────────────────────────────────

def save_paper_meta(paper_id: str, data: dict) -> None:
    db = _get_db()
    if db is None:
        return
    try:
        db.collection("papers").document(paper_id).set(data, merge=True)
    except Exception as e:
        _disable(e)


def get_paper_meta(paper_id: str) -> Optional[dict]:
    db = _get_db()
    if db is None:
        return None
    try:
        doc = db.collection("papers").document(paper_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        _disable(e)
        return None


# ──────────────────────────────────────────────
# Threads
# ──────────────────────────────────────────────

def save_threads(paper_id: str, threads: List[dict]) -> None:
    db = _get_db()
    if db is None or not threads:
        return
    try:
        batch = db.batch()
        col = db.collection("papers").document(paper_id).collection("threads")
        for thread in threads:
            batch.set(col.document(thread["id"]), thread)
        batch.commit()
        logger.info(f"[firestore] saved {len(threads)} threads for paper {paper_id}")
    except Exception as e:
        _disable(e)


def get_threads_by_paper(paper_id: str) -> List[dict]:
    db = _get_db()
    if db is None:
        return []
    try:
        docs = db.collection("papers").document(paper_id).collection("threads").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        _disable(e)
        return []


# ──────────────────────────────────────────────
# Dynamic Agents
# ──────────────────────────────────────────────

def save_agents(paper_id: str, agents: List[dict]) -> None:
    db = _get_db()
    if db is None or not agents:
        return
    try:
        batch = db.batch()
        col = db.collection("papers").document(paper_id).collection("agents")
        for agent in agents:
            batch.set(col.document(agent["id"]), agent)
        batch.commit()
        logger.info(f"[firestore] saved {len(agents)} agents for paper {paper_id}")
    except Exception as e:
        _disable(e)


def get_agents_by_paper(paper_id: str) -> List[dict]:
    db = _get_db()
    if db is None:
        return []
    try:
        docs = db.collection("papers").document(paper_id).collection("agents").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        _disable(e)
        return []


# ──────────────────────────────────────────────
# Agent Annotations
# ──────────────────────────────────────────────

def save_annotations(paper_id: str, annotations: List[dict]) -> None:
    db = _get_db()
    if db is None or not annotations:
        return
    try:
        batch = db.batch()
        col = db.collection("papers").document(paper_id).collection("agent_annotations")
        for ann in annotations:
            batch.set(col.document(ann["id"]), ann)
        batch.commit()
        logger.info(f"[firestore] saved {len(annotations)} annotations for paper {paper_id}")
    except Exception as e:
        _disable(e)
