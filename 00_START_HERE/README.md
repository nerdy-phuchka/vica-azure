# Virtual Credit Analyst — working prototype

Read this file first. Backend version 0.1.0, revised front-end review v0.2, 22 October 2026.

**Latest visual review:** open `04_Frontend/public/vica-review.html` directly, or `/design` in the Next.js application. See `02_LATEST_FRONTEND.md` for the revised navigation and editable memo.

## Folder order
1. `01_Product_and_Design`: scope, architecture, policy gaps and data dictionary.
2. `02_Configuration`: environment template and policy configuration.
3. `03_Backend`: FastAPI API, durable database jobs, human review, Azure adapters and reports.
4. `04_Frontend`: Next.js bilingual case workspace.
5. `05_LOS_Integration`: executable LOS simulator and interface guidance.
6. `06_Azure_Infrastructure`: Bicep, Container Apps deployment and provisioning scripts.
7. `07_Tests`: calculation, workflow, access control and integration tests.
8. `08_Sample_Data`: synthetic bilingual documents and input fixtures.
9. `09_Operations_and_Guides`: local setup, Azure deployment, user guide and security/runbook.
10. `10_Verification`: actual verification results and release limitations.

## Start locally
Install Python 3.12+, Node.js 22+, and Docker Desktop (optional). See `09_Operations_and_Guides/01_LOCAL_SETUP.md`.

The default local mode uses SQLite, filesystem storage, local PDF text extraction and manually reviewed fields. It genuinely processes text PDFs, DOCX, TXT, CSV and XLSX. Scanned PDFs and images need Azure Document Intelligence configuration. Azure OpenAI enables schema-constrained field interpretation. There are no simulated AI successes: missing cloud configuration is reported explicitly.

For the complete Azure processing path configure `02_Configuration/.env.example`, deploy the infrastructure, and follow the Azure guide. Real documents must be used only in an authorised environment. Local dev identity is restricted to loopback and cannot be used in Azure mode.

## What is implemented
Persistent applications; English/Arabic interface; document upload and authenticated source viewing; OCR adapter; structured AI extraction; evidence validation; manual field confirmation; decimal financial calculations; versioned policy checks; field visits; comments; maker/checker review and explicit delegation limits; decisions and conditions; HTML/DOCX reports; evidence-based case queries; LOS APIs, idempotency and signed event outbox; audit history; background worker with leases/retries; Azure Blob, managed identities, Service Bus notification, AI Search and database adapters.

## Important boundaries
This is a working underwriting prototype, not a validated lending decision system. SME-EL-001 through SME-EL-010 are preserved as pending because the photographed thresholds could not be confirmed. A formally approved policy configuration is required before a positive recommendation can progress to credit review. For synthetic walkthroughs use the separately labelled demonstration policy. No production rating model is invented. Final credit approval is human; the package never releases funds.

Run tests using `python -m pytest 07_Tests -q` from this package directory after installing backend requirements. Use `docker compose up --build` for the UI, API, worker and LOS simulator.
