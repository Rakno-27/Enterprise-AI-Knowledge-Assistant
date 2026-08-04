# Architecture

Frontend:
- React
- TypeScript
- Vite
- Tailwind

Backend:
- FastAPI
- Python 3.11+

Database:
- PostgreSQL

Vector Database:
- Qdrant

LLM:
- GPT-4o-mini

Embeddings:
- text-embedding-3-small

Storage:
- Local filesystem (MVP)

Deployment:
- Docker Compose

RAG Flow:
User Query
→ Embedding
→ Qdrant Search
→ Top 5 Chunks
→ GPT
→ Answer + Sources
