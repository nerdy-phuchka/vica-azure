# Latest front-end revision — ViCA

Open `04_Frontend/public/vica-review.html` directly in a browser to view the updated front end without installing Node, Docker or Python. If the Next.js application is running, open `/design`.

The standalone review implements:
- ViCA® wordmark and Deloitte green/black/white palette.
- Powered by Deloitte at the lower left.
- Acquisition dashboard with month, quarter, year and custom date selection.
- Separate monthly sales funnel with stage drill-through.
- Separate commercial credit queue with borrower search and filters.
- Single-borrower cockpit, evidence, financial spread, sensitivities and committee review.
- Detailed 20-section AI-authored sample Credit Assessment Memo, section editing, saved versions, consolidated view and HTML export.
- Policy Configuration directly on the left panel: editable thresholds, document checklist, delegation settings, draft testing, saved drafts, review state and JSON export.

All records are synthetic. Interactions and saved edits in this review use browser/session state. It makes no Azure/LOS calls and does not change server policy. Real AI generation, persistence, authentication and authority checks remain responsibilities of the connected FastAPI application. The existing live-service workspace remains at `/`; `/design` is the revised visual review route. Do not treat a local draft save or simulated review submission as an authorised credit or policy decision.

Source: `04_Frontend/review/vica-v2.js` and `memo-factory.js`. The full provided design reference is retained as non-executing text for traceability. The revised HTML is self-contained and does not depend on Tailwind, Chart.js, or external font downloads.

## Configurable cockpit sections

Every borrower-cockpit tab now has a contextual **Configure →** control. The same six configuration entry points are available in **Policy Configuration → Cockpit sections**.

| Section | Editable settings | Effect in the preview |
| --- | --- | --- |
| Borrower 360 | Summary metrics, profile fields, additional checkpoint | Changes the displayed profile and readiness checklist |
| Documents & evidence | Required categories, maximum age, English/Arabic acceptance | Updates the requirements shown against each evidence item |
| Financial spreading | Historical periods, SAR display units, financial metrics | Rebuilds the spread without changing the underlying source figures |
| Risk & stress | Default and maximum shocks, selected risks, additional mitigant | Recalculates stressed DSCR and updates the risk register |
| Credit Assessment Memo | Included chapters, titles, order | Updates draft structure while preserving analyst text and excluded chapters |
| Committee decision | Distinct roles, referral limit, specialist clearances, required conditions | Updates the displayed review route and conditions |

**Save configuration draft** retains an unapplied draft. **Apply to preview** updates the browser-local SME portfolio template for all synthetic dossiers. Templates, memo edits and version history persist in browser local storage when supported; otherwise they last for the current session. Section settings do not activate server policies, run OCR, execute live AI generation, or authorise loan decisions. The existing policy-rule editor remains separate.

Configuration implementation: `04_Frontend/review/section-configuration.js` and `section-configuration.css`. Browser verification: `07_Tests/frontend_configuration.cjs`; results in `10_Verification/frontend-configuration-results.json`.

After editing a review module, run `python 04_Frontend/review/build-review.py` from the package root to regenerate the standalone page. Browser tests require Playwright; optional `VICA_PLAYWRIGHT_MODULE` and `VICA_CHROME` environment variables select the module/browser on the host. Run `node 07_Tests/frontend_configuration.cjs`. Test screenshots are internal verification output, not application assets.
