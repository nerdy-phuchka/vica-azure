# Data dictionary and schema

The prototype uses typed envelopes with JSON payloads in a transactional SQL table. `Record`: id(UUID), kind, case_id, data(JSON serialised UTF-8), version(optimistic lock), created_at(UTC). Separate `Job` and `Idempotency` tables support durable execution and duplicate control. Initial schema is created by `app.migrate`; a formal Alembic evolution scheme is a production hardening item.

| Kind | Core payload |
|---|---|
| application | borrower_name, requested_amount(decimal string), currency, product, purpose, los_reference, tenant, owner, members, synthetic, status, data_revision, current_assessment, clearances, decision, conditions |
| document | filename, mime, sha256, storage_key, scan_status, state, document_type, language, pages, reviewed_by |
| field | name, original_value, value, document_id, page, quote, period/currency/units, origin, active, reviewed, review_history |
| transaction | document_id, source row, date, description, debit, credit, balance, category, reviewed_by |
| assessment | evidence revision, reviewed fields, document hashes, policy, checks, financials, notes, clearances, blockers, recommendation, prepared_by |
| narrative | assessment_id, text, origin, author, reviewed, reviewed_by |
| task | title, assignee, due_date, blocking, status, resolution |
| exception | rule_id, policy_version, data_revision, rationale, approved_by |
| note | category, text, author |
| audit | actor, action, detail |
| event | type, application_id, payload, delivery |

`Job`: id, kind(document/callback), target, state, attempts, available_at(lease/retry), safe error text.
`Idempotency`: principal(tenant+subject), key, digest, result_id with unique principal/key.

Numeric source data is stored as text until reviewed; the calculation module uses Decimal. There is no silent zero-imputation. Reviewer must normalise currency, units, reporting period and Gregorian dates. Units supplied by AI are descriptive until confirmed. Entity translation and transliteration never establish identity automatically.

Case membership is enforced in the API in addition to Entra role validation. Search results require the same authorised case ID. The v0.1 deployment assumes one bank/Entra tenant per environment, not a public multi-bank SaaS service.
