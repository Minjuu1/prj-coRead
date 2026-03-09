"""
Firebase Firestore 연결 + 청크/annotation 저장/조회.

스키마:
  papers/{paperId}
    chunks/{chunkId}
    annotations/{annotationId}
    threads/{threadId}

Firebase credentials 없으면 모든 작업을 no-op/빈값으로 처리 (in-memory only mode).
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


# ──────────────────────────────────────────────
# Chunks
# ──────────────────────────────────────────────

def save_chunks(paper_id: str, chunks: List[dict]) -> None:
    db = _get_db()
    if db is None:
        return
    batch = db.batch()
    col = db.collection("papers").document(paper_id).collection("chunks")
    for chunk in chunks:
        batch.set(col.document(chunk["id"]), chunk)
    batch.commit()
    logger.info(f"[firestore] saved {len(chunks)} chunks for paper {paper_id}")


def get_chunks(paper_id: str) -> List[dict]:
    db = _get_db()
    if db is None:
        return []
    docs = db.collection("papers").document(paper_id).collection("chunks").stream()
    return [doc.to_dict() for doc in docs]


def get_chunk(paper_id: str, chunk_id: str) -> Optional[dict]:
    db = _get_db()
    if db is None:
        return None
    doc = db.collection("papers").document(paper_id).collection("chunks").document(chunk_id).get()
    return doc.to_dict() if doc.exists else None


# ──────────────────────────────────────────────
# Paper metadata
# ──────────────────────────────────────────────

def save_paper_meta(paper_id: str, data: dict) -> None:
    db = _get_db()
    if db is None:
        return
    db.collection("papers").document(paper_id).set(data, merge=True)


def get_paper_meta(paper_id: str) -> Optional[dict]:
    db = _get_db()
    if db is None:
        return None
    doc = db.collection("papers").document(paper_id).get()
    return doc.to_dict() if doc.exists else None


# ──────────────────────────────────────────────
# Threads
# ──────────────────────────────────────────────

def save_threads(paper_id: str, threads: List[dict]) -> None:
    db = _get_db()
    if db is None or not threads:
        return
    batch = db.batch()
    col = db.collection("papers").document(paper_id).collection("threads")
    for thread in threads:
        batch.set(col.document(thread["id"]), thread)
    batch.commit()
    logger.info(f"[firestore] saved {len(threads)} threads for paper {paper_id}")


def get_threads_by_paper(paper_id: str) -> List[dict]:
    db = _get_db()
    if db is None:
        return []
    docs = db.collection("papers").document(paper_id).collection("threads").stream()
    return [doc.to_dict() for doc in docs]
