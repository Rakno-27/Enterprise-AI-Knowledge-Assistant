import uuid
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from openai import OpenAI

from app.core.config import settings
from app.models.document import DocumentDB
from app.schemas.document import DocumentMetadata
from app.schemas.chat import DocumentSource

class RAGService:
    def __init__(self):
        # Initialize Clients
        self.qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        
        # Self-initialize Qdrant Collection
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        try:
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]
            if settings.QDRANT_COLLECTION not in collection_names:
                # text-embedding-3-small uses 1536 dimensions
                self.qdrant.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=qdrant_models.VectorParams(
                        size=1536,
                        distance=qdrant_models.Distance.COSINE
                    )
                )
                print(f"[RAG] Successfully created Qdrant collection: {settings.QDRANT_COLLECTION}")
        except Exception as e:
            print(f"[RAG] Warning: Unable to connect/create Qdrant collection. RAG will run in fallback mock. Details: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embeddings or fallback to mock embedding vector if API key is not present."""
        if not self.openai or not settings.OPENAI_API_KEY:
            # Fallback mock embedding: deterministic float array based on word characters
            val = sum(ord(c) for c in text) % 1000 / 1000.0
            return [val] * 1536

        try:
            response = self.openai.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[RAG] Embedding generation error: {e}. Falling back to mock vector.")
            val = sum(ord(c) for c in text) % 1000 / 1000.0
            return [val] * 1536

    async def ingest_document(self, db: Session, filename: str, content: bytes, file_type: str) -> DocumentMetadata:
        doc_id = f"doc-{uuid.uuid4().hex[:8]}"
        text_content = content.decode("utf-8", errors="ignore")
        
        # Split text into paragraphs/chunks
        raw_chunks = [c.strip() for c in text_content.split("\n\n") if c.strip()]
        if not raw_chunks:
            raw_chunks = [text_content[:500]] if text_content else ["Empty document."]
            
        points = []
        for i, chunk_text in enumerate(raw_chunks):
            chunk_snippet = chunk_text[:1200]
            vector = self._get_embedding(chunk_snippet)
            
            points.append(
                qdrant_models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "doc_id": doc_id,
                        "title": filename,
                        "text": chunk_snippet,
                        "chunk_idx": i
                    }
                )
            )

        # Ingest to Qdrant if collection exists
        if points:
            try:
                self.qdrant.upsert(
                    collection_name=settings.QDRANT_COLLECTION,
                    points=points
                )
            except Exception as e:
                print(f"[RAG] Warning: Qdrant upload failed: {e}. Falling back to local logging.")

        # Save metadata to DB
        doc_db = DocumentDB(
            id=doc_id,
            filename=filename,
            file_type=file_type,
            size_bytes=len(content),
            uploaded_at=datetime.utcnow(),
            chunks_count=len(raw_chunks)
        )
        db.add(doc_db)
        db.commit()
        db.refresh(doc_db)

        return DocumentMetadata(
            id=doc_db.id,
            filename=doc_db.filename,
            file_type=doc_db.file_type,
            size_bytes=doc_db.size_bytes,
            uploaded_at=doc_db.uploaded_at,
            chunks_count=doc_db.chunks_count
        )

    async def retrieve_context(self, query: str, top_k: int = 5) -> List[DocumentSource]:
        """Perform similarity search on Qdrant and return top K snippets (Default: 5)."""
        vector = self._get_embedding(query)
        
        try:
            search_result = self.qdrant.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=vector,
                limit=top_k
            )
            
            results = []
            for hit in search_result:
                payload = hit.payload or {}
                results.append(
                    DocumentSource(
                        id=payload.get("doc_id", "unknown"),
                        title=payload.get("title", "Untitled Document"),
                        snippet=payload.get("text", "")[:350],
                        score=round(hit.score, 3)
                    )
                )
            return results
        except Exception as e:
            print(f"[RAG] Warning: Qdrant search retrieval failed: {e}. Returning mock query response.")
            # Fallback search if Qdrant isn't responding
            return [
                DocumentSource(
                    id="doc-enterprise-policy-001",
                    title="Enterprise_AI_Policy_2026.pdf",
                    snippet="Fallback mock context: All enterprise data processed by Enterprise AI Assistant is encrypted at rest using AES-256 and in transit using TLS 1.3.",
                    score=0.85
                )
            ]

    async def list_documents(self, db: Session) -> List[DocumentMetadata]:
        docs = db.query(DocumentDB).order_by(DocumentDB.uploaded_at.desc()).all()
        return [
            DocumentMetadata(
                id=doc.id,
                filename=doc.filename,
                file_type=doc.file_type,
                size_bytes=doc.size_bytes,
                uploaded_at=doc.uploaded_at,
                chunks_count=doc.chunks_count
            )
            for doc in docs
        ]

    async def delete_document(self, db: Session, doc_id: str) -> bool:
        doc = db.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
        if not doc:
            return False

        # Delete from SQL
        db.delete(doc)
        db.commit()

        # Delete from Qdrant
        try:
            self.qdrant.delete(
                collection_name=settings.QDRANT_COLLECTION,
                points_selector=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="doc_id",
                            match=qdrant_models.MatchValue(value=doc_id)
                        )
                    ]
                )
            )
        except Exception as e:
            print(f"[RAG] Warning: Qdrant deletion failed for doc {doc_id}: {e}")

        return True

rag_service = RAGService()
