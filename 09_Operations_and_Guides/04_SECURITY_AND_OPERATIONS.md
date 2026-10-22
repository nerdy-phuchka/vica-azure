# 4. Security and operations

## Implemented controls
Entra issuer/audience/tenant/signature/expiry checks; role and case membership checks; separate preparer/reviewer/approver; configured amount authority; optimistic concurrency; immutable decision snapshot; file signatures/size checks; Office archive expansion and macro checks; Azure upload malware scanning; private data endpoints; managed identities; Key Vault database credential; authenticated source access; evidence quotes; policy versioning; signed LOS callbacks; no borrower bodies in routine logs.

Local mode is a developer walkthrough with selectable identities and a shared secret. It is not approved for borrower data. Azure mode fails startup when dev auth is enabled, required service identity settings are missing, SQLite is selected or scanning is not configured.

## Limits requiring review before a wider/production rollout
- No production scorecard or fraud model; documents are not authenticated merely by OCR.
- Specialist roles share Reviewer/Admin rather than separate bank entitlements.
- Policy changes are deployment-controlled, not a full policy approval portal.
- No automatic loan booking, funding, security perfection or customer offer release.
- Initial database schema bootstrap, not a full release-to-release migration framework.
- Application audit records are append-only through exposed APIs, but not cryptographically immutable against a database administrator.
- No per-bank multitenancy, data-loss-prevention certification, penetration-test signoff or bank compliance certification.
- Single replica and pilot backup defaults; no measured HA/DR/SLA.
- Public authenticated web/API ingress by default. A private-only bank perimeter requires an approved gateway/network design.
- Dependency lockfiles/images must be resolved, scanned and frozen on a connected build host. They were not downloadable in authoring.
- Azure AI content logging/abuse monitoring, service processing locations, backups, support access and telemetry require the bank's approved data-handling assessment; private endpoints alone do not establish residency.

## Daily checks
Check API/worker/scanner availability; queued/failed jobs; callback delivery backlog; processing latency; storage/database capacity; token usage/quota; expiring credentials and antivirus signatures. Never print secrets or full OCR content into diagnostics.

## Failed documents
Read the safe error in the case. Correct source quality/configuration; Analyst can retry a terminal failed document. Retry does not bypass scanning or review. A worker crash is recovered by job lease expiry. If a crash occurs after processing commits but before job completion, the next worker sees processed state and does not duplicate fields.

## Failed callbacks
Repair endpoint/authentication first. Inspect event IDs and receiver deduplication. From an authorised backend console, locate the failed `Job(kind='callback')`, verify target/event and requeue by setting state=queued, attempts=0, available_at=current UTC. Perform this under operational change control and record an audit note; there is deliberately no public unauthenticated requeue endpoint.

## Backup/restore
Set approved retention. Verify PostgreSQL restore into a separate environment, restore the corresponding Blob versions and validate document hashes/assessment references. Rebuild Search from retained document pages; it is a derived index, not the record of credit decisions. No automatic retention deletion job is enabled because policy values remain unconfirmed.

## Release
Run test suite/build; evaluate English/Arabic accuracy; review policy diffs; scan dependencies and images; deploy new immutable tags; verify managed identities/networking; smoke-test upload/review/report; retain prior image and database backup. Schema changes need an explicit migration and rollback plan. Never overwrite prior decision evidence to simplify a release.
