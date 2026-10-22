# 2. Azure deployment

This package is not already deployed. No Azure subscription, tenant, credentials, permitted geography or deployment quota was available in the authoring environment.

## Required decisions and access
- Subscription/resource group and permitted data/AI-processing geography.
- Region supporting Container Apps, PostgreSQL, Document Intelligence, AI Search and the approved Azure OpenAI model/version/deployment type.
- Azure CLI with Bicep and Container Apps extension; permission to create resources, private endpoints and scoped role assignments.
- Entra administrator support for API/SPA registrations, scopes and role assignments.
- Representative authorised English/Arabic documents and approved retention rules.
- Confirm Azure costs first. This foundation includes a **Premium Service Bus namespace** to support private connectivity, dedicated PostgreSQL and always-on containers. It is not a free-tier deployment. No cost figure has been invented.

## A. Identity configuration
Create separate API and SPA registrations in the approved tenant. API: accepted access token version 2; expose delegated scope `api://<API-client-id>/access_as_user`; create app-role values RM, Analyst, Reviewer, Approver, Admin, LOS. Assign human roles through enterprise application users/groups. Assign LOS to the integration service principal as an application permission. Require assignment where appropriate. Configure SPA delegated API permission and consent. Register the final web origin as an SPA redirect URI after deployment. Entra audience is the API client ID for v2 tokens; verify the issued token rather than assuming the Application ID URI is the audience.

Assign case membership separately through the Admin UI using Entra object IDs. Approver identity must also exist in the approved policy authorities with an amount limit. Admin role is not an approval bypass. Specialist clearances use Reviewer/Admin in v0.1; split Compliance/Legal/Fraud roles before broader rollout.

## B. Deploy foundation and application
Run from an authenticated, connected PowerShell 7 terminal:
```powershell
az login
az account set --subscription '<subscription-id>'
pwsh -File 06_Azure_Infrastructure/04_deploy.ps1 `
  -ResourceGroup '<resource-group>' -Location '<approved-region>' `
  -ModelName '<approved-supported-model>' -ModelVersion '<supported-version>' `
  -EntraTenantId '<tenant-id>' -ApiAudience '<API-client-id>' `
  -SpaClientId '<SPA-client-id>' -ApiScope 'api://<API-client-id>/access_as_user' `
  -ImageTag 'pilot-001'
```
Script builds Bicep, provisions data/network services, creates runtime role assignments, builds containers in ACR and deploys API/worker/web/scanner. Model SKU defaults to **Standard**, not GlobalStandard; verify allowed processing geography and regional quota. Service/model availability is a preflight dependency; do not switch silently to Global for convenience.

Review the infrastructure through `az deployment group what-if` in your deployment process before applying it. Use a new image tag for every release. The script generates a new database password on a foundation redeploy, which is an intentional rotation and requires coordinated app rollout. Preserve the existing secret through a controlled release process if you are not rotating it.

## C. Initialise and verify
1. Complete redirect URI and Entra assignments.
2. Confirm private DNS resolution and managed-identity permissions; initial RBAC propagation can take time.
3. Execute `python /app/init_search.py` inside the worker console using `az containerapp exec`. The file is included in the API image. The runtime currently has Search Service Contributor to bootstrap the index; remove that role after bootstrap if index management is delegated to deployment identity.
4. Verify API health, worker logs and ClamAV readiness. Upload scanning fails closed if scanner/signatures are unavailable.
5. Sign in as Analyst; create an authorised pilot case. Upload representative English/Arabic scans; review source-linked extraction.
6. Run all tests, browser workflow, authority checks, retrieval isolation and restore exercises. See acceptance guide.

## D. LOS gateway and live adapter
`03_gateway.bicep` is an optional APIM gateway. Its backendUrl should be the API origin, so `/vca/api/v1/...` forwards to `/api/v1/...`. Deploy it separately with publisher email, tenant/audience and backend URL. The API validates Entra independently; the gateway is not assumed to be the only reachable endpoint. The default API has authenticated public HTTPS ingress; sensitive data services are private. If the bank requires private-only ingress, implement the approved private gateway/VPN topology before real-data use.

Live callback URL/secret must be configured server-side using Container Apps secret/Key Vault references; the template intentionally does not connect the local simulator to Azure. HTTPS is required for a live callback. No source documents are embedded in events.

## Observability and recovery

The optional gateway uses APIM Developer tier so the supplied key-based rate limit is supported; it adds a separate ongoing cost and is not a production gateway tier. Confirm your organisation's gateway design before enabling it.
Container logs are collected in Log Analytics. An Application Insights resource is provisioned but custom distributed tracing is not instrumented in v0.1. Add approved OpenTelemetry instrumentation after defining redaction and tracing rules. PostgreSQL backup retention defaults to 7 days, Blob versioning/soft deletion to 7 days. These are pilot defaults, not accepted bank retention/recovery commitments. No HA/DR failover is claimed.

## Deployment gates
All Bicep must compile; model and quota available; actual package dependencies resolved/scanned; Entra tested; private endpoint and scanner health verified; real OCR benchmark passed; approved policy configured; access/authority and backup/restore tests passed. This authoring environment did not execute Azure deployment or Bicep compilation.
