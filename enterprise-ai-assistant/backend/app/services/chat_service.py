import uuid
import asyncio
from typing import AsyncGenerator, List
from datetime import datetime
from sqlalchemy.orm import Session

from openai import OpenAI

from app.core.config import settings
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, DocumentSource, ChatMessage
from app.services.rag_service import rag_service
from app.models.chat import ChatMessageDB

class ChatService:
    def __init__(self):
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    async def generate_response(self, db: Session, request: ChatCompletionRequest) -> ChatCompletionResponse:
        user_message = request.messages[-1].content if request.messages else ""
        sources: List[DocumentSource] = []

        # Retrieve top 5 chunks from Qdrant
        if request.use_rag and user_message:
            sources = await rag_service.retrieve_context(user_message, top_k=5)

        # Store user message in DB if session_id is provided
        if request.session_id:
            user_db_msg = ChatMessageDB(
                session_id=request.session_id,
                role="user",
                content=user_message,
                timestamp=datetime.utcnow()
            )
            db.add(user_db_msg)
            db.commit()

        # Build context prompt
        context_str = ""
        if sources:
            context_str = "\n\nRetrieved context from enterprise knowledge base:\n" + "\n".join(
                [f"[{s.title}]: {s.snippet}" for s in sources]
            )

        system_prompt = (
            "You are an advanced enterprise conversational AI assistant. "
            "You have access to securely indexed internal knowledge bases. "
            "Respond helpfully, objectively, and accurately using the context provided when available."
        )

        assistant_content = ""
        used_model = request.model or settings.DEFAULT_MODEL

        if self.openai and settings.OPENAI_API_KEY:
            try:
                # Prepare conversation history
                messages_payload = [{"role": "system", "content": system_prompt}]
                
                # Append last 10 messages for context window memory
                for msg in request.messages[:-1]:
                    messages_payload.append({"role": msg.role, "content": msg.content})
                
                # Append current user prompt with injected context
                messages_payload.append({
                    "role": "user",
                    "content": f"Query: {user_message}\n{context_str}"
                })

                chat_response = self.openai.chat.completions.create(
                    model=used_model,
                    messages=messages_payload,
                    temperature=request.temperature or 0.7
                )
                assistant_content = chat_response.choices[0].message.content
            except Exception as e:
                print(f"[Chat] OpenAI API exception: {e}. Falling back to mock generator.")
                assistant_content = self._mock_respond(user_message, context_str, used_model)
        else:
            assistant_content = self._mock_respond(user_message, context_str, used_model)

        # Save assistant message to DB
        if request.session_id:
            assistant_db_msg = ChatMessageDB(
                session_id=request.session_id,
                role="assistant",
                content=assistant_content,
                timestamp=datetime.utcnow()
            )
            db.add(assistant_db_msg)
            db.commit()

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            role="assistant",
            content=assistant_content,
            model=used_model,
            created=datetime.utcnow(),
            sources=sources
        )

    async def generate_stream(self, db: Session, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        response = await self.generate_response(db, request)
        words = response.content.split(" ")
        for i, word in enumerate(words):
            await asyncio.sleep(0.02)  # Simulate typing streaming chunk delay
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk

    def _mock_respond(self, query: str, context: str, model: str) -> str:
        query_lower = query.lower()

        if "hello" in query_lower or "hi" in query_lower:
            return "Hello! I am your Enterprise AI Assistant. How can I assist you with your workflows, document retrieval, or analytics today?"

        if context:
            return (
                f"Based on the enterprise knowledge base, here is what I found:\n\n"
                f"{context}\n\n"
                f"Is there anything specific in this documentation you would like me to summarize further?"
            )

        return (
            f"I have processed your query: **\"{query}\"** using `{model}`.\n\n"
            f"As an enterprise assistant, I am connected to your enterprise pipelines and vector indices. "
            f"You can upload internal guidelines, documentation, or reports using the Knowledge Base manager on the sidebar to enable RAG-augmented answers."
        )

    async def get_session_history(self, db: Session, session_id: str) -> List[ChatMessage]:
        messages = db.query(ChatMessageDB).filter(ChatMessageDB.session_id == session_id).order_by(ChatMessageDB.timestamp.asc()).all()
        return [
            ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            )
            for msg in messages
        ]

chat_service = ChatService()
