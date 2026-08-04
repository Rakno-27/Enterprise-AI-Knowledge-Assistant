from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: str
    size_bytes: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    chunks_count: int = 0

class DocumentUploadResponse(BaseModel):
    success: bool
    document: DocumentMetadata
    message: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]
    total: int
