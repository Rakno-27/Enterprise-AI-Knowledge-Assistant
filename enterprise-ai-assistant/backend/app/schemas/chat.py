from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "gpt-4o-mini"
    stream: bool = False
    temperature: Optional[float] = 0.7
    use_rag: bool = True
    session_id: Optional[str] = None

class DocumentSource(BaseModel):
    id: str
    title: str
    snippet: str
    score: float

class ChatCompletionResponse(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    model: str
    created: datetime = Field(default_factory=datetime.utcnow)
    sources: Optional[List[DocumentSource]] = []

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)

class SearchResponse(BaseModel):
    query: str
    results: List[DocumentSource]

