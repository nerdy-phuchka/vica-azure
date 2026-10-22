# 3. User guide

## Analyst
Create case → upload documents → wait for processing → select a document → inspect original and extracted text → confirm type → review extracted fields. Click a quote to navigate/highlight its evidence when OCR coordinates are available. Local text extraction lacks graphical line coordinates; source text remains available.

Financial fields: confirm values in base currency. AI may extract a figure in thousands; edit to base units with a rationale before confirmation. Only one active field per name is used; prior confirmed values remain historical. The prototype does not automatically choose the correct year across multiple statements. Confirm the selected period yourself. Do not mix parent/group accounts or reporting periods.

Manual fields without source documents are labelled assumptions and retain rationale. They are not independently verified. For source-linked manual fields, provide the exact quote on the selected page. Financial assumptions such as proposed debt service need a documented calculation/rationale; the prototype does not silently manufacture a loan repayment schedule from an amount alone.

Statement CSV/XLSX requires date, description, debit, credit (optional balance), or the Arabic headers in the sample. Categorise transactions individually. Net movements are not assumed to equal sales. Scanned bank statements can be OCRed, but bank-format-specific row mapping needs evaluation/customisation; use the schedule template initially.

## Reviewer
Admin adds you to the case. Record legal/compliance/fraud/field-visit conclusions with evidence/rationale. Assign clarification tasks to members, set a due date and resolve with evidence. Open blocking tasks prevent submission. A preparing officer cannot provide their own specialist clearance after preparation has been assigned. Follow organisational independence requirements beyond these prototype role gates.

## Assessment and reports
Run assessment with period and currency confirmation. Inspect missing information, policy outcomes, financial warnings and assumptions. Pending policy blocks submission. Draft a narrative using Azure AI or enter one manually; review it before it appears in the report. Export Word or HTML; use the browser's Print to PDF for the latter. Report language option changes direction/header, while source text and human content remain in their original language; fully translated standard report labels require a further approved translation pass.

## Decision
Preparing Analyst submits. A different Reviewer accepts. A third Approver records a decision within the configured delegation. Conditional approval requires conditions. Reviewer/Admin records fulfilment evidence separately. No disbursement takes place. Final cases are immutable for underwriting inputs; a new application is needed for renewal/reassessment.

## Evidence changes
Uploads, field confirmation, transaction changes, notes, clearances and tasks reset assessment readiness. Run assessment again and repeat review. Unreviewed narrative drafts do not change approved calculations; confirming a narrative resets independent review. Errors appear visibly; refresh after a concurrency conflict rather than forcing old data through.

## Case chat
Questions retrieve only authorised case evidence. Answers are advisory, show source excerpts and must be checked. Without Azure AI, the system displays evidence for manual review and explicitly says AI is not configured.
