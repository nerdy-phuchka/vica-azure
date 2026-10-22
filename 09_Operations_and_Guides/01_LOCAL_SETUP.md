# 1. Local setup

## Recommended: Docker Compose
Prerequisites: Docker Desktop with Linux containers and Compose v2, internet access to package registries, PowerShell 7+ (Windows) or Python 3.12+ and bash (Linux/macOS).

1. Extract the ZIP into a short path, e.g. `C:\VCA`.
2. Open a terminal in `VCA-Full-Package`.
3. Run `pwsh -File 00_START_HERE/01_Setup_Local.ps1`, or `bash 00_START_HERE/02_setup_local.sh`.
4. Open `http://127.0.0.1:3000`.
5. Read the locally generated `.env` privately and use its DEV_AUTH_TOKEN. Choose Analyst and subject demo-analyst.
6. Create a Synthetic demonstration case and follow `08_Sample_Data/README.md`.

Ports are bound to localhost. The browser sends development identity through a Next proxy; a separate server-side proxy secret allows that trusted local hop. These identities are deliberately selectable for a synthetic walkthrough and are forbidden in Azure mode. Do not expose the local development stack to the internet or use it as the real-data pilot.

Commands:
```text
docker compose logs --tail=100 api worker
docker compose ps
docker compose stop
docker compose up -d
```
Stopping preserves named data volumes. Do not run volume-removal commands unless you intend to delete local cases/documents.

## Enable actual Azure OCR and AI
Deploy Azure resources and use the real-data Azure application for borrower files. For developer testing of Azure adapters from a workstation, configure AZURE_DOCUMENT_ENDPOINT, AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT, sign in using `az login`, grant least-privilege service roles, and use an approved network route to the private endpoints. Containerised local credentials are not automatically inherited from host `az login`; either use an explicitly approved environment-based service principal in the local container or run the backend on the authenticated host. Never copy Azure credentials into frontend code.

## Without Docker
1. Create/activate a Python 3.12 virtual environment.
2. From package root: `python -m pip install -r 03_Backend/requirements.txt`.
3. Create root `.env` from the template, generate independent secrets, and change POLICY_FILE to `./02_Configuration/policy.pending.json`.
4. Terminal A, root: `python -m uvicorn app.main:app --app-dir 03_Backend --host 127.0.0.1 --port 8000 --no-access-log`.
5. Terminal B, root: set PYTHONPATH to the absolute `03_Backend` directory, then `python -m app.worker`.
6. In `04_Frontend`, create `.env.local` with `NEXT_PUBLIC_AUTH_MODE=local`, `API_INTERNAL_URL=http://127.0.0.1:8000` and the same DEV_PROXY_SECRET as root `.env`.
7. Terminal C, frontend: `npm install`, `npm run typecheck`, `npm run dev`.

The API/worker read root `.env` when started from root. The frontend reads its own `.env.local`. Default database/storage paths are relative to the backend working directory; use identical directories for API and worker.

## Validation
```text
python 07_Tests/offline_checks.py
python -m pytest 07_Tests -q
python 07_Tests/export_openapi.py
```
Then run `npm run typecheck` and `npm run build` inside frontend. Docker build resolves dependencies on the connected machine. Capture generated lockfiles, scan dependencies and pin image digests before a real-data release.
