# Scope and process

Working prototype for Saudi SME working-capital, term-loan and lease assessment. Product selection is captured, but product-specific legal/Islamic-finance structuring is not certified. No real policy thresholds, credit scores or PD values have been inferred from photographs.

## Process
1. RM/Analyst/LOS creates an application with an idempotency key.
2. Admin assigns case members; no automatic portfolio-wide access for reviewers.
3. Uploads are validated and (in Azure) scanned before persistent acceptance.
4. A durable SQL job drives OCR/structure extraction and evidence-constrained field interpretation.
5. Analyst checks the original document, its entity/period and document category.
6. Analyst confirms canonical values; each correction retains original extraction and review history.
7. Supported CSV/XLSX statement schedules produce transactions requiring classification and review.
8. Reviewer records legal/compliance/fraud/field-visit conclusions; external checks are not fabricated.
9. Analyst selects a period, confirms base currency and annual service consistency, and runs assessment.
10. Decimal calculations, approved rule evaluation, missing information and specialist holds produce an assessment snapshot.
11. Draft/edit/review a credit narrative; generate credit note, credit report and field-visit reports.
12. Analyst submits; a different Reviewer accepts; a third Approver decides within a configured amount limit.
13. Conditions are tracked separately. No funding is released.

New evidence/fields/notes/clearances/tasks invalidates the current assessment and resets review. Approved narrative changes reset independent review. Final decision snapshots are locked; create a new case for renewal or reassessment.

## Included versus dependent
Included: persistent end-to-end workflow, real upload/extraction adapters, review, calculations, rule execution, reports, audit and LOS interface.
Dependent: Azure tenant/access, approved processing geography, approved policies, actual rating model, external screening/bureau/registry access, LOS vendor contract and production assurance.

Field visits, business/management assessment and legal conclusions are captured as human evidence and narrative. They are not autonomous site verification or legal opinions. Native bank-statement formats can be OCRed; transaction-level automation initially uses the strict schedule template. Broader bank-specific parsing needs labelled samples and validation.
