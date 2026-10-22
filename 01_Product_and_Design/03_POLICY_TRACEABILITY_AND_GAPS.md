# Policy traceability and unresolved inputs

Source: user photographs 55929–55936, supplied 22 October 2026. Several table cells were not reliably readable; pictures are not a substitute for the approved original.

| Source | Extracted theme | Implementation | Outstanding |
|---|---|---|---|
| 55929 | Draft Saudi SME configuration baseline | jurisdiction/scope documented; real policy marked pending | approved original/version |
| 55930 | Evidence, assumptions, accountability, explainability, controlled change | source viewing, review history, snapshots and gates | final product applicability |
| 55931 | SME-EL-001–010 and policy timing | ten pending rule IDs retained; task due dates | exact wording, thresholds, SLA values |
| 55932 | Required documents and financial method | category review, baseline checklist, financial input workflow | exact conditional checklist and formulas |
| 55933 | Ratios; Credit Note/Report/Field Visit | deterministic metrics and three report exports | bank templates, conventions and approval |
| 55934–55935 | Detailed requirements unreadable | explicit unresolved requirements | original pages |
| 55936 | Policy/scoring/integration/security/SLA gaps and acceptance | deployment inputs, test suite, readiness checklist | accountable-owner signoff |

## Configuration procedure
1. Obtain the approved policy and original Arabic wording; store a controlled reference and version outside model prompts.
2. Complete each pending rule's description, field, operator, value, hard_stop flag and source_page.
3. Confirm applicability. This prototype's numeric operators are gt/gte/lt/lte/eq on computed metric fields. New nonnumeric eligibility rules need explicit code/schema and tests; do not express them as executable Python or free-form prompts.
4. Configure document categories and authorities with Entra object IDs, amount limits and can_override flags.
5. Record approved_by and set status=approved only after owner review; run regression tests and deploy a new immutable image/policy version.
6. Preserve the old policy and existing assessment snapshots.

No browser endpoint lets an analyst self-approve policy. For v0.1 policy change control is a source/deployment process requiring the organisation's review. A policy JSON approval marker is not a cryptographic signature or evidence of organisational approval by itself.

Hard restrictions, missing evidence and pending rules cannot be overridden. An expressly configured exception authority can authorise an overridable failed rule; the exception is scoped to the exact evidence revision and policy version, then assessment must be rerun.

## Missing before a real lending pilot
Original policy; scope/SME definition; actual scorecard; conditional checklist; delegated authority; specialist role mappings; report templates; verified external-data access; LOS mapping; residency/hosting approval; retention, backup, recovery and SLA values; representative English/Arabic samples; independent model/security assessment.
