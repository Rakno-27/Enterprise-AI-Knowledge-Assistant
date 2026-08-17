from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    HealthResponse,
    SearchRequest,
    SearchResponse,
)
from app.schemas.document import DocumentUploadResponse, DocumentListResponse
from app.services.chat_service import chat_service
from app.services.rag_service import rag_service
from app.core.database import get_db
from app.core.auth import get_current_user, RequireRole, UserClaims


router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment="development"
    )

@router.get("/models", tags=["LLM"])
async def list_models():
    return {
        "models": [
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Fast & Lightweight)", "context_window": 128000},
            {"id": "gpt-4o", "name": "GPT-4o (High Precision & Vision)", "context_window": 128000},
            {"id": "claude-3-5-sonnet", "name": "Claude 3.5 Sonnet (Reasoning)", "context_window": 200000}
        ]
    }

@router.post("/chat/completions", response_model=ChatCompletionResponse, tags=["Chat"])
async def chat_completions(request: ChatCompletionRequest, db: Session = Depends(get_db), user: UserClaims = Depends(get_current_user)):
    try:
        if request.stream:
            return StreamingResponse(
                chat_service.generate_stream(db, request),
                media_type="text/plain"
            )
        return await chat_service.generate_response(db, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating chat completion: {str(e)}"
        )

@router.get("/chat/history/{session_id}", tags=["Chat"])
async def get_chat_history(session_id: str, db: Session = Depends(get_db), user: UserClaims = Depends(get_current_user)):
    try:
        return await chat_service.get_session_history(db, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/upload", response_model=DocumentUploadResponse, tags=["Knowledge Base"])
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), user: UserClaims = Depends(RequireRole(["admin"]))):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    file_type = file.filename.split(".")[-1].lower() if "." in file.filename else "txt"

    doc_metadata = await rag_service.ingest_document(
        db=db,
        filename=file.filename,
        content=content,
        file_type=file_type
    )

    return DocumentUploadResponse(
        success=True,
        document=doc_metadata,
        message=f"Successfully ingested {file.filename} into RAG Knowledge Base."
    )

@router.get("/documents", response_model=DocumentListResponse, tags=["Knowledge Base"])
async def list_documents(db: Session = Depends(get_db), user: UserClaims = Depends(get_current_user)):
    docs = await rag_service.list_documents(db)
    return DocumentListResponse(documents=docs, total=len(docs))

@router.delete("/documents/{doc_id}", tags=["Knowledge Base"])
async def delete_document(doc_id: str, db: Session = Depends(get_db), user: UserClaims = Depends(RequireRole(["admin"]))):
    success = await rag_service.delete_document(db, doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "message": f"Document {doc_id} deleted."}

@router.post("/search", response_model=SearchResponse, tags=["Search"])
async def semantic_search(request: SearchRequest, user: UserClaims = Depends(get_current_user)):
    try:
        results = await rag_service.retrieve_context(request.query, top_k=request.top_k)
        return SearchResponse(
            query=request.query,
            results=results
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing semantic search: {str(e)}"
        )
