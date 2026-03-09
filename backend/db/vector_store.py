"""
Chroma 벡터 스토어 래퍼.

- 임베딩: Chroma 기본값 (all-MiniLM-L6-v2, 로컬, 무료)
- 저장 위치: backend/chroma_db/
"""
import os
import logging
from typing import List, Optional

import chromadb

logger = logging.getLogger(__name__)

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
_client: Optional[chromadb.PersistentClient] = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=_DB_PATH)
    return _client


def _collection(paper_id: str):
    return _get_client().get_or_create_collection(
        name=f"paper_{paper_id.replace('-', '_')}",
        metadata={"hnsw:space": "cosine"},
    )


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def add_chunks(paper_id: str, chunks: List[dict]) -> None:
    """chunk 리스트를 Chroma에 저장."""
    if not chunks:
        return
    col = _collection(paper_id)
    col.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["content"] for c in chunks],
        metadatas=[
            {
                "section": c.get("section", ""),
                "pageStart": c.get("pageStart", 1),
                "pageEnd": c.get("pageEnd", 1),
                "position": c.get("position", 0.0),
            }
            for c in chunks
        ],
    )
    logger.info(f"[vector_store] upserted {len(chunks)} chunks for paper {paper_id}")


def query(paper_id: str, text: str, n_results: int = 5) -> List[dict]:
    """
    텍스트 쿼리 → 관련 chunk 반환.
    Returns list of {"content", "section", "pageStart", "distance"}
    """
    col = _collection(paper_id)
    try:
        results = col.query(
            query_texts=[text],
            n_results=n_results,
            include=["documents", "metadatas", "distances", "ids"],
        )
    except Exception as e:
        logger.error(f"[vector_store] query error: {e}")
        return []

    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    return [
        {
            "id": chunk_id,
            "content": doc,
            "section": meta.get("section", ""),
            "pageStart": meta.get("pageStart", 1),
            "distance": dist,
        }
        for chunk_id, doc, meta, dist in zip(ids, docs, metas, dists)
    ]


def delete_paper(paper_id: str) -> None:
    try:
        _get_client().delete_collection(f"paper_{paper_id.replace('-', '_')}")
        logger.info(f"[vector_store] deleted collection for paper {paper_id}")
    except Exception as e:
        logger.warning(f"[vector_store] delete failed: {e}")
