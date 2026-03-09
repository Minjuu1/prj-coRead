from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from models import Paper

router = APIRouter()


@router.post("/upload")
async def upload_paper(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """PDF 업로드 → Phase 1 파이프라인 비동기 시작"""
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다")

    # TODO: Firebase Storage에 저장 후 paper 생성
    # TODO: background_tasks.add_task(run_pipeline, paper_id)
    return {"paperId": "TODO", "status": "processing"}


@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    """논문 메타데이터 + status 조회"""
    # TODO: Firestore에서 조회
    raise HTTPException(status_code=404, detail="Not implemented")


@router.get("/{paper_id}/status")
async def get_paper_status(paper_id: str):
    """파이프라인 진행 상태 polling"""
    # TODO: Firestore에서 status 조회
    raise HTTPException(status_code=404, detail="Not implemented")
