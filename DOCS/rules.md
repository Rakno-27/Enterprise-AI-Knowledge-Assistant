# Development & Engineering Rules — Enterprise AI Knowledge Assistant

> This document answers **WHAT RULES** developers and AI coding agents must follow. Rules are derived directly from explicit statements, warnings, and recommendations in the source document. Rules marked **[Inference]** are reasonable organizational safeguards not explicitly stated in the source but consistent with it; they carry lower authority than sourced rules.

## 1. Architecture Rules

- Developers MUST preserve the 7-layer architecture separation (Presentation, API Gateway, Application, AI/ML Pipeline, Vector Store, Data Layer, Infrastructure) — layers MUST remain independently scalable and replaceable.
- Developers MUST NOT bypass the API Gateway for client-facing requests; all traffic routes through Kong (or the configured gateway) for auth, rate limiting, and routing.
- The system MUST follow the phased roadmap order in `phases.md`. Features from a later phase MUST NOT be implemented ahead of their phase unless a phase dependency explicitly requires it.
- Teams SHOULD build the MVP stack first, validate with real users, and only then incrementally adopt enterprise-tier components — do not build all components at once.

## 2. RAG / AI / LLM Rules

- The system MUST NOT use semantic-only search in production. Hybrid search (dense + sparse/BM25 with Reciprocal Rank Fusion) is mandatory per the source's explicit "Never use semantic-only in production" guidance.
- The system MUST apply re-ranking (Cohere Rerank v3 or equivalent) between initial retrieval (top-20) and LLM context injection (top-5).
- The system MUST NOT use a single chunking strategy for all document types. Use Parent-Child chunking for reports, Semantic chunking for technical documentation, Structural chunking for HTML/Markdown.
- The LLM MUST be instructed to answer only from provided/retrieved context (grounded prompting) — this is the primary hallucination-prevention control and MUST NOT be omitted.
- Every factual claim in an LLM answer MUST include a source citation (`[Source: doc_id]` or equivalent).
- The system MUST enforce a retrieval quality gate: if no chunk meets the minimum similarity threshold, the system MUST refuse to answer rather than fabricate a response.
- Engineering priority MUST follow the source's stated sequence: (1) hybrid search + re-ranking, (2) parent-child/semantic chunking, (3) glossary + query expansion, (4) conversation memory + citations, (5) multi-client RBAC + audit logging, (6) LangGraph agents + Graph RAG.
- For at least the first 6 months of development, teams SHOULD prioritize retrieval quality over chatbot feature breadth — a reliable retrieval system is stated to be more valuable than a feature-rich but occasionally-hallucinating chatbot.
- Retrieval quality MUST be measured against a fixed evaluation set (source specifies 50 representative queries) with a target of 90%+ top-3 relevance, evaluated weekly once in production.

## 3. Multi-Tenancy & Data Isolation Rules

- The system MUST guarantee that a user authenticated for one client can never retrieve another client's documents, under any query, including crafted/adversarial queries.
- Each client's vectors MUST be isolated via a dedicated Qdrant collection (or, for the filter-per-client strategy, a `client_id` payload filter applied to every query) — collection-per-client is required for high-security/compliance clients.
- Every JWT MUST carry a `client_id` claim, and this claim MUST be validated at every service boundary.
- All PostgreSQL tables containing client-scoped data MUST have Row Level Security enabled and a policy filtering by `client_id`.
- S3 access MUST be restricted by client-prefixed bucket policy.
- Redis cache keys MUST be prefixed with `client_id` to prevent cross-client cache contamination.

## 4. Authentication, Authorization & Secrets

- RBAC MUST be enforced at all three levels simultaneously: API Gateway (JWT/role claims), Application (per-endpoint permission checks), and Database (Row Level Security). Relying on a single layer is explicitly disallowed ("never rely on a single layer").
- JWTs MUST be RS256-signed with a 15-minute expiry and use refresh token rotation.
- MFA MUST be enforced for all admin-tier roles.
- Passwords MUST meet a minimum 12-character complexity policy and MUST be checked against breach databases (e.g., Have I Been Pwned) at creation/change time.
- API keys and other secrets MUST be stored in a secrets manager (Vault/HashiCorp) and rotated at least every 90 days. Secrets MUST NOT be hardcoded or committed to source control. **[Inference — general engineering safeguard, consistent with the source's Vault requirement]**
- Session data MUST be Redis-backed, and administrators MUST be able to force-invalidate all sessions for a user instantly.

## 5. Security Rules

- All data in transit MUST use TLS 1.3.
- All data at rest (S3, PostgreSQL, vector payloads) MUST be encrypted with AES-256.
- PII MUST be detected (via AWS Macie or equivalent + custom NLP patterns) and classified before or during ingestion.
- LLM providers used in production MUST contractually guarantee no training on customer data (e.g., OpenAI Enterprise / Azure OpenAI terms).
- Every user query, document access event, admin action, failed auth attempt, and data export MUST be written to the immutable audit log.
- Audit logs MUST be retained for 7 years in an immutable (Object Lock) store.
- Repeated failed authentication (5+ attempts) MUST trigger an automatic block.

## 6. Document Processing Rules

- Ingestion MUST be asynchronous and queue-based (Kafka); the ingestion pipeline MUST NOT block the upload request.
- Each document type MUST be routed to its designated parser (see `architecture.md` §8.1) — a generic/naive text extraction MUST NOT be substituted for the specified parser.
- Scanned documents MUST be routed through the OCR pipeline before chunking.
- Uploaded files MUST be hashed (SHA-256) on upload; identical hashes MUST be deduplicated rather than reprocessed.
- Only changed or new files SHOULD be reprocessed on each sync cycle (incremental indexing); full reprocessing SHOULD be reserved for reconciliation jobs.

## 7. API & Backend Rules

- Backend services MUST be built with FastAPI (Python), consistent with the selected stack; introducing a different backend framework requires an explicit architecture decision update.
- Services MUST be designed as independently deployable microservices with a single responsibility (see `architecture.md` §11) and MUST scale according to their designated strategy (horizontal/stateless, horizontal+GPU, etc.).
- Non-real-time operations (ingestion, embedding generation, notifications, analytics events) MUST go through Kafka rather than synchronous calls.
- Failed async messages MUST be captured in a dead-letter queue, alerted, and support manual reprocessing — MUST NOT be silently dropped.

## 8. Database Rules

- Schema changes MUST preserve the core tables defined in `architecture.md` §10 (`clients`, `users`, `documents`, `conversations`, `messages`, `audit_logs`) and their RLS policies.
- `audit_logs` MUST remain partitioned by month for performance.
- Indexes on `client_id` and other high-cardinality filter columns (as shown in the schema) MUST be preserved when the schema evolves.

## 9. Testing Rules

- LLM output quality MUST be tested against a fixed, repeatable evaluation query set (per the source's 50-query weekly benchmark).
- E2E and performance testing are QA Engineer responsibilities from Phase 3 onward (pytest, Playwright, k6, LLM eval frameworks per the source's team requirements table).
- Beyond this, detailed unit/integration test coverage requirements are **not specified in the source documentation**; teams SHOULD apply standard test coverage practices. **[Inference]**

## 10. Backward Compatibility & Phase Discipline

- Features MUST NOT be marked or documented as "implemented" unless they are actually built and verified — this applies equally to project documentation and to `memory.md` specifically.
- New phases MUST NOT be added, and the existing five-phase order MUST NOT be changed, without updating the source-of-truth planning document first.
- Alternative technologies listed in comparison tables (e.g., Pinecone, Weaviate, ChromaDB, pgvector) MUST NOT be treated as the selected implementation; only the technology explicitly marked "Selected"/"RECOMMENDED"/"selected" in `architecture.md` is authoritative for a given context (general stack vs. budget tier — see `architecture.md` §12.5 note).

## 11. Documentation Rules

- Any change to architecture, phases, or rules MUST keep `prd.md`, `architecture.md`, `phases.md`, `rules.md`, `design.md`, and `memory.md` mutually consistent — a change in one MUST be reflected in the others where relevant.
- Missing information MUST be marked "Not specified in the source documentation" rather than invented, in all six project-control documents.

## 12. UI/UX & Frontend Rules

- Frontend MUST be built in React + TypeScript (Vite for MVP tooling; shadcn/ui + Tailwind CSS for production-tier UI components) per the selected stack.
- Frontend MUST support real-time token streaming for chat responses (Phase 3 requirement) once that phase is reached.
- Detailed visual/interaction rules are governed by `design.md`; where `design.md` states a requirement is unspecified, engineers SHOULD default to accessible, conventional patterns rather than inventing a bespoke design system. **[Inference]**

## 13. Production Readiness Rules

- A feature MUST NOT be considered production-ready without: hybrid search + re-ranking (if it touches retrieval), RLS-enforced client isolation (if it touches client data), and audit logging (if it touches user or admin actions).
- Before enabling SSO/SAML, RBAC across all three enforcement layers MUST already be verified working (Phase 4 depends on Phase 2's RBAC foundation).
- Compliance-sensitive features (SOC 2, HIPAA, GDPR erasure) MUST NOT be marked complete without corresponding audit/penetration testing evidence, per Phase 4's stated deliverables.
