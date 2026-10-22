# Synthetic walkthrough data

No real borrower data is bundled. Create a case marked **Synthetic demonstration**; requested amount SAR 250,000; add `demo-reviewer` and `demo-approver` using the Admin role. Upload 01–03, wait for processing, review document categories registration / financial_statements / bank_statement. Review the six statement transactions. Add and confirm the required fields from the financial fixture; use verbatim quotes when source-linked.

In local text mode the application genuinely extracts source text but deliberately does not pretend to infer fields without Azure AI. Add them through the manual field form. Each new field needs a separate confirmation.

Reviewer records legal, compliance, fraud and field_visit clearances with synthetic rationale. Analyst runs FY2025 assessment using base SAR and annual cash/service values. Expected DSCR 1.5; downside 1.2; demonstration revenue rule passes; demonstration DSCR rule passes. Independent Reviewer accepts submission; demo-approver can conditionally approve up to the explicitly synthetic limit in policy.demo.json.

This demonstration does not validate actual legal status, external compliance screening, collateral or bank policy. For a real pilot, use Entra authentication and confirmed policy/authority settings in your authorised Azure environment.
