# 5. Acceptance test plan

| Test | Expected result |
|---|---|
| English digital financial PDF | Text and fields match source; period/units reviewed |
| Arabic scanned registration | OCR readable; Arabic identity preserved; uncertain fields reviewed |
| Mixed-language document | Original text preserved; no automatic entity merge based on translation |
| Unsupported/spoofed/malicious file | Rejected or scanner blocks it |
| Unavailable scanner | Upload fails closed in Azure |
| Duplicate upload | Same document reference returned; no duplicate analysis |
| Missing AI configuration | No fabricated fields; explicit manual-review route |
| Hallucinated field quote | Rejected by source-page substring validation |
| Arabic numeric separators | Reviewed values normalise correctly |
| Missing/zero/negative denominator | Unavailable ratio with warning, not false zero |
| Wrong reporting period/units | Human correction required; source retained |
| Non-operating credits | Classified separately from receipts; not treated as sales |
| Pending/failed hard policy rule | Submission blocked |
| Permitted exception | Correct authority only; evidence/policy-specific; reassessment required |
| Unassigned user/other case | 404/no disclosure; retrieval and document routes enforce same scope |
| Same preparer/reviewer/approver | Separation checks reject prohibited action |
| Approver above delegation | Decision rejected |
| Open blocking clarification | Submission blocked |
| Concurrent change | 409; refresh required |
| New evidence after assessment | Assessment invalidated and review reset |
| Evidence after final decision | Mutation blocked; existing snapshot retained |
| Conditional approval | Conditions recorded, no automatic disbursement |
| LOS duplicate create/event | Idempotent case/event handling |
| Callback failure | Retry/backoff; durable failure visible; no lost decision |
| Worker restart | Expired lease recovery; no duplicate extracted fields |
| Word/HTML reports | Correct snapshot, reviewed narrative and safe output escaping |
| Real-data pilot load | Measure 10 concurrent users and representative page counts; targets agreed after benchmark |
| Restore exercise | Case, documents/hashes, policy and decision recover consistently |

## Evaluation dataset
Obtain authorised, representative English and Arabic samples covering registration, constitutional records, audited/management financial statements, bank statements and low-quality scans. Label critical fields and evidence, independently check calculations and test across sectors/document layouts. Do not use the same cases for prompt tuning and final acceptance.

Measure critical-field exact match, unsupported-claim rate, missed material flags, human correction rate, processing failures, turnaround and cost per case. Set separate Arabic/English and document-type acceptance criteria with bank owners before pilot acceptance. No accuracy percentage is claimed before this benchmark.
