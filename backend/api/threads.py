from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/by-chunk/{chunk_id}")
async def get_threads_by_chunk(chunk_id: str):
    """특정 chunk의 thread 목록 조회"""
    # TODO: Firestore에서 조회
    raise HTTPException(status_code=404, detail="Not implemented")


@router.post("/{thread_id}/reveal")
async def reveal_thread(thread_id: str):
    """Thread unlock (locked → open)"""
    # TODO: Firestore에서 status 업데이트
    raise HTTPException(status_code=404, detail="Not implemented")
