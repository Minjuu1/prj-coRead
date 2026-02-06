from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from services.firebase_service import firebase_service
from services.pdf_parser import pdf_parser_service

router = APIRouter(prefix="/documents", tags=["documents"])


class SectionResponse(BaseModel):
    sectionId: str
    title: str
    content: str
    order: int


class ParsedContentResponse(BaseModel):
    sections: List[SectionResponse]


class DocumentResponse(BaseModel):
    documentId: str
    userId: str
    title: str
    originalPdfUrl: Optional[str]
    parsedContent: ParsedContentResponse
    threads: List[str]
    uploadedAt: str
    lastAccessedAt: str


class DocumentListItem(BaseModel):
    documentId: str
    title: str
    uploadedAt: str


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Upload and parse a PDF document.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Check file size (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    # Check GROBID health
    if not await pdf_parser_service.check_health():
        raise HTTPException(
            status_code=503,
            detail="PDF parsing service is unavailable. Please ensure GROBID is running."
        )

    # Parse PDF
    try:
        parsed = await pdf_parser_service.parse_pdf(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")

    # Generate document ID
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()

    # Upload PDF to storage (if available)
    pdf_url = firebase_service.upload_pdf(doc_id, content)

    # Create document
    document = {
        "documentId": doc_id,
        "userId": user_id,
        "title": parsed["title"],
        "originalPdfUrl": pdf_url,
        "parsedContent": {
            "sections": parsed["sections"]
        },
        "threads": [],
        "uploadedAt": now,
        "lastAccessedAt": now
    }

    # Save document
    firebase_service.save_document(document)

    return DocumentResponse(**document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Get document details.
    """
    document = firebase_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update last accessed time
    document["lastAccessedAt"] = datetime.utcnow().isoformat()

    return DocumentResponse(**document)


@router.get("/{document_id}/sections", response_model=List[SectionResponse])
async def get_sections(document_id: str):
    """
    Get document sections.
    """
    document = firebase_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return [SectionResponse(**s) for s in document["parsedContent"]["sections"]]


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document.
    """
    success = firebase_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document deleted successfully"}


@router.get("/user/{user_id}", response_model=List[DocumentListItem])
async def get_user_documents(user_id: str):
    """
    Get all documents for a user.
    """
    documents = firebase_service.get_user_documents(user_id)
    return [
        DocumentListItem(
            documentId=d["documentId"],
            title=d["title"],
            uploadedAt=d["uploadedAt"]
        )
        for d in documents
    ]
