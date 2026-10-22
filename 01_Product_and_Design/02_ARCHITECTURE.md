# Architecture

Browser → Next.js web/proxy → FastAPI → PostgreSQL, Blob Storage, SQL jobs.

Worker → Document Intelligence → Azure OpenAI → unreviewed fields and evidence → AI Search (optional retrieval).

Human actions → versioned case and audit records → immutable assessment → independent review → delegated human decision.

LOS → API Management (optional) → same authorised API. Transactional event outbox → HMAC callback → LOS/simulator.

## Consistency
SQL is the source of truth for jobs, workflow and events. Service Bus is a wake-up channel, not a second workflow database. Worker polls SQL if a notification is lost. Claims use compare-and-swap with a fifteen-minute lease, three attempts and backoff. One worker replica is configured for the pilot. Restarting a crashed worker recovers expired leases. No bank data enters logs.

OCR plus extracted fields commits in one database transaction. Optional indexing failures do not discard OCR; local authorised evidence retrieval remains available. Blob writes precede SQL commits; an interrupted commit may leave an orphan blob. The runbook requires periodic orphan review, with no automatic deletion of retained evidence.

Optimistic record versions reject concurrent changes. Assessment snapshots contain reviewed input IDs/values, document hashes, notes, clearance records, policy configuration and model/deployment identifiers. File hashes identify bytes; they do not establish document authenticity.

## AI boundaries
Documents are untrusted data. They cannot issue tool calls or change policy. AI fields must have an allow-listed name and verbatim quote on the cited page. Unsupported evidence is rejected. All extracted fields remain unreviewed. Financial arithmetic and authority checks never depend on generative text. Narrative remains draft until a human confirms it. Retrieved answers are assistive and sources are displayed; a cited answer is not automatically verified.

Search uses lexical multilingual retrieval and a server-applied case filter. Vector embeddings/rerankers are intentionally not required for v0.1. This avoids implying an unevaluated semantic retrieval quality level. Users can inspect all source text directly.

## Scale baseline
10 concurrent internal users; single API and worker replica; asynchronous document processing; configurable 50 MB / 200 PDF pages; 80,000 characters for a single AI extraction request. Oversize AI content is not silently truncated: it enters manual review. Table and statement layouts must be benchmarked separately. Search/SLA/throughput and cost are not benchmarked in the delivered environment.
