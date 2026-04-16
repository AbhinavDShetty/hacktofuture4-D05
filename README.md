# Agentic CI/CD Repair System

An AI-driven DevOps system leveraging a Multi-Agent architecture to autonomously detect, diagnose, and propose surgical fixes for CI/CD pipeline failures -- heavily gated by human oversight.

Built for HackToFuture 4.0.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Proposed Solution](#proposed-solution)
3. [Features](#features)
4. [Architecture](#architecture)
5. [Tech Stack](#tech-stack)
6. [Project Structure](#project-structure)
7. [Prerequisites](#prerequisites)
8. [Setup and Installation](#setup-and-installation)
9. [Usage](#usage)
10. [API Reference](#api-reference)
11. [Environment Variables](#environment-variables)
12. [GitHub Actions Integration](#github-actions-integration)
13. [Troubleshooting](#troubleshooting)
14. [License](#license)

---

## Problem Statement

Modern CI/CD pipelines fail constantly due to trivial syntax errors, missing dependencies, or breaking upstream changes. Developers spend countless hours context-switching, reading massive unstructured error logs, and hunting down the exact line of code that caused the build to break.

Developer friction and pipeline downtime drastically reduce engineering velocity. Automated fixes are dangerous without oversight, but manually diagnosing every failure is inefficient.

**Target Users:** DevOps Engineers, SREs, and Software Developers working in fast-paced continuous deployment environments.

---

## Proposed Solution

When a GitHub Actions build fails, a native hook in the CI/CD workflow extracts the error logs and the recent `git diff`, then fires them as a JSON payload to the Agentic Repair backend.

Instead of a human reading through raw logs, a **Multi-Agent AI Pipeline** (Detective -> Developer -> Security Reviewer) processes the failure context, retrieves historical context using vector search (RAG), pinpoints the root cause, and generates a unified diff patch to fix the repository.

**What makes this solution unique:**

1. **Multi-Agent Architecture:** Three specialized LangGraph agents (Detective, Developer, Security Reviewer) operate in sequence rather than relying on a single prompt.
2. **Immutable Human Oversight:** The AI-generated risk score and git patch are held in a holding area until a human clicks "Approve" on the web dashboard, at which point a Pull Request is automatically generated. No code is pushed without human authorization.

---

## Features

- **Automated Webhook Triggers:** GitHub Actions workflow detects failures and sends structured payloads (error logs, git diff, commit hash) to the backend webhook endpoint.
- **Three-Stage LangGraph Pipeline:** Detective Agent (root cause analysis) -> Developer Agent (patch generation) -> Security Reviewer Agent (risk scoring).
- **RAG Memory:** Uses PostgreSQL with the `pgvector` extension and HNSW indexing to store error embeddings. The system retrieves historically similar incidents and their approved fixes to provide context to the AI agents.
- **Strict Risk Assessment:** The Security Reviewer Agent scores proposed patches from 1-100 based on heuristics including vulnerability introduction, scope bleed, database alterations, dependency changes, and stability concerns.
- **Human-in-the-Loop Dashboard:** A real-time web UI that displays the raw error logs, git diff, detective summary, proposed patch, and risk score. Developers can approve or reject patches with a single click.
- **Automated Pull Request Generation:** Upon approval, the system clones the repository, applies the patch, pushes a new branch, and creates a Pull Request via the GitHub API using PyGithub.
- **Direct Commit to Main:** An alternative code path (`apply_and_commit_to_main`) allows pushing approved fixes directly to the default branch when a PR-based workflow is not desired.
- **Dockerized Deployment:** The entire stack (FastAPI backend + PostgreSQL with pgvector) runs via Docker Compose for consistent, reproducible environments.

---

## Architecture

```
GitHub Actions (CI/CD Failure)
        |
        | POST /webhook/ci_failure (JSON payload)
        v
+-------------------+
| FastAPI Backend   |
| (app/main.py)     |
+-------------------+
        |
        | 1. Create Incident record in DB
        | 2. Run background AI pipeline
        v
+-------------------------------+
| LangGraph Multi-Agent Pipeline|
| (app/ai_pipeline.py)          |
|                               |
|  [Detective Agent]            |
|       |                       |
|  [Developer Agent]            |
|       |                       |
|  [Security Reviewer Agent]    |
+-------------------------------+
        |
        | Store FixProposal (patch, risk score, root cause)
        v
+-------------------+
| PostgreSQL + pgvector |
| (Incidents, Fixes,   |
|  Error Embeddings)    |
+-------------------+
        |
        v
+-------------------+
| Web Dashboard     |
| (app/static/      |
|  index.html)      |
+-------------------+
        |
        | Human clicks Approve
        v
+-------------------+
| GitHub Integration|
| (app/github_      |
|  integration.py)  |
| Creates PR via    |
| PyGithub + git CLI|
+-------------------+
```

---

## Tech Stack

| Layer       | Technology                                                      |
|-------------|-----------------------------------------------------------------|
| Frontend    | HTML5, CSS3, Vanilla JavaScript                                 |
| Backend     | FastAPI (Python 3.11), Uvicorn, async request handlers          |
| AI / ML     | LangChain, LangGraph, Ollama-compatible LLM, RAG Embeddings    |
| Database    | PostgreSQL 16 with `pgvector` extension, SQLAlchemy async ORM   |
| VCS         | PyGithub, git CLI for patch application and PR creation         |
| Infra       | Docker, Docker Compose                                          |

---

## Project Structure

```
hacktofuture4-D05/
|-- .env                          # Local environment variables (not committed)
|-- .env.example                  # Template for required environment variables
|-- .gitignore
|-- Dockerfile                    # Python 3.11-slim image with git and build tools
|-- docker-compose.yml            # Orchestrates backend + PostgreSQL pgvector
|-- requirements.txt              # Python dependencies
|-- README.md
|
|-- app/
|   |-- __init__.py
|   |-- main.py                   # FastAPI application, routes, background tasks
|   |-- ai_pipeline.py            # LangGraph multi-agent pipeline (Detective, Developer, Security)
|   |-- database.py               # Async SQLAlchemy engine, session, and init_db
|   |-- models.py                 # SQLAlchemy ORM models (Incident, FixProposal)
|   |-- schemas.py                # Pydantic request/response schemas
|   |-- github_integration.py     # Clone, patch, branch, push, and PR creation logic
|   |-- static/
|       |-- index.html            # Human oversight dashboard (single-page app)
|
|-- .github/
|   |-- workflows/
|       |-- agentic-repair.yml    # GitHub Actions workflow with failure hook
|
|-- agentic_repair_cli.py         # CLI tool for manually triggering webhook payloads
|-- test_webhook.py               # Script to send a sample failure payload to the backend
|-- test_llm.py                   # Script to verify LLM API connectivity
|-- dummy/                        # Dummy test files for simulated failures
```

---

## Prerequisites

- **Docker Desktop** (v20.10 or later) and **Docker Compose**
- **Git** (for local development and PR generation)
- **Python 3.11+** (only needed if running outside Docker)
- An **Ollama-compatible LLM endpoint** (local Ollama instance or a cloud-hosted Ollama API)
- A **GitHub Personal Access Token (PAT)** with `repo` scope (required for automated PR creation)

---

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/AbhinavDShetty/hacktofuture4-D05.git
cd hacktofuture4-D05
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
LLM_API_KEY=your_llm_api_key_here
GITHUB_TOKEN=your_github_pat_here
```

See the [Environment Variables](#environment-variables) section for full details.

### 3. Start the Stack with Docker Compose

```bash
docker-compose up --build -d
```

This will start two containers:

- **db**: PostgreSQL 16 with the pgvector extension, listening on port 5432.
- **backend**: FastAPI application served by Uvicorn, listening on port 8000.

### 4. Verify the Backend is Running

```bash
curl http://localhost:8000/docs
```

This should return the auto-generated FastAPI Swagger UI. You can also open `http://localhost:8000/docs` in a browser.

### 5. Open the Dashboard

Open your browser and navigate to:

```
http://localhost:8000/dashboard
```

The dashboard will display "No incidents found" until a failure payload is received.

---

## Usage

### Triggering a Simulated CI/CD Failure (Manual)

Use the included CLI tool to send a mock failure payload to the backend:

```bash
pip install requests
python agentic_repair_cli.py push --endpoint http://localhost:8000/webhook/ci_failure
```

Alternatively, use the `test_webhook.py` script for a more specific test case (requires `requests`):

```bash
python test_webhook.py
```

### Reviewing AI-Generated Patches

1. Open `http://localhost:8000/dashboard` in your browser.
2. The dashboard auto-refreshes every 3 seconds. Once the multi-agent pipeline finishes processing, you will see:
   - **Raw System Logs**: The error output extracted from the CI/CD run.
   - **Git Diff**: The recent code changes that triggered the failure.
   - **Detective Agent Summary**: A 1-3 sentence root cause analysis.
   - **Developer Agent Patch**: A unified diff patch proposed to fix the issue.
   - **Security Reviewer Score**: A risk score from 1 to 100 with reasoning.
3. Click **Approve Patch** to trigger automatic PR creation, or click **Reject** to discard the proposal.

### Automated GitHub Actions Integration

When the provided GitHub Actions workflow is installed in a target repository, failures are automatically detected and sent to the backend. See the [GitHub Actions Integration](#github-actions-integration) section for setup instructions.

---

## API Reference

### POST /webhook/ci_failure

Receives a CI/CD failure payload and triggers the agentic repair pipeline.

**Request Body (JSON):**

| Field         | Type   | Description                                  |
|---------------|--------|----------------------------------------------|
| `repo_name`   | string | Full repository name (e.g., `owner/repo`)    |
| `commit_hash` | string | SHA of the commit that triggered the failure  |
| `error_logs`  | string | Raw error output from the CI/CD pipeline      |
| `git_diff`    | string | Output of `git diff` showing recent changes   |
| `status`      | string | Pipeline status (e.g., `failed`)              |

**Response:**

```json
{
  "message": "Incident received. Agentic pipeline processing.",
  "incident_id": 1
}
```

### GET /api/incidents

Returns all incidents with their associated fix proposals, ordered by most recent.

### POST /api/fixes/{fix_id}/approve

Approves a pending fix proposal. Triggers automatic PR creation via the GitHub API.

**Response:**

```json
{
  "message": "Fix approved. Pull Request created.",
  "status": "approved",
  "pr_url": "https://github.com/owner/repo/pull/1"
}
```

### POST /api/fixes/{fix_id}/reject

Rejects a pending fix proposal.

### GET /dashboard

Serves the human oversight dashboard (HTML page).

### GET /docs

Auto-generated Swagger/OpenAPI documentation provided by FastAPI.

---

## Environment Variables

These variables are configured in the `.env` file (for Docker Compose) or set directly in your environment.

| Variable            | Required | Default                              | Description                                                                 |
|---------------------|----------|--------------------------------------|-----------------------------------------------------------------------------|
| `LLM_API_KEY`       | Yes      | -                                    | API key for the Ollama-compatible LLM endpoint                              |
| `GITHUB_TOKEN`      | Yes      | -                                    | GitHub Personal Access Token with `repo` scope for PR creation              |
| `DATABASE_URL`      | No       | `postgresql+asyncpg://user:password@db:5432/agentic_db` | Async PostgreSQL connection string (auto-configured in Docker Compose)  |
| `LLM_MODEL`         | No       | `gpt-oss:120b-cloud`                | Model name to use with the Ollama-compatible API                            |
| `LLM_API_BASE`      | No       | `https://api.ollama.com`             | Base URL of the Ollama-compatible LLM API                                   |
| `OLLAMA_BASE_URL`   | No       | `http://host.docker.internal:11434`  | Base URL for the local Ollama instance (used for embeddings)                |

---

## GitHub Actions Integration

The repository includes a reusable GitHub Actions workflow at `.github/workflows/agentic-repair.yml`. To integrate it with a target repository:

### 1. Copy the Workflow File

Copy `.github/workflows/agentic-repair.yml` into the target repository's `.github/workflows/` directory.

### 2. Set the Repository Secret

In the target repository, go to **Settings -> Secrets and variables -> Actions** and add:

| Secret Name           | Value                                             |
|-----------------------|---------------------------------------------------|
| `AGENTIC_WEBHOOK_URL` | The public URL of your backend (e.g., an ngrok tunnel like `https://xxxx.ngrok.io`) |

### 3. Expose the Backend Publicly

Since GitHub Actions runs on GitHub's infrastructure, the backend must be reachable from the internet. Use a tunnel service such as ngrok:

```bash
ngrok http 8000
```

Use the generated HTTPS URL as the `AGENTIC_WEBHOOK_URL` secret.

### 4. Workflow Behavior

The workflow triggers on pushes to `main` and `dev` branches, and on pull requests to `main`. It performs the following steps:

1. Checks out the code with full history (`fetch-depth: 0`).
2. Sets up Python 3.11 and installs dependencies from `requirements.txt`.
3. Runs `python -m compileall` for syntax validation and `pytest` for tests.
4. If any step fails, it packages the last 100 lines of logs and the recent git diff into a JSON payload and sends it to the backend endpoint via `curl`.

---

## Troubleshooting

### Backend container fails to start

- Ensure Docker Desktop is running.
- Check container logs: `docker-compose logs backend`
- Verify the `.env` file exists and contains valid values.

### Database connection errors

- Wait for the PostgreSQL health check to pass before the backend starts. Docker Compose handles this via `depends_on` with `condition: service_healthy`.
- Confirm port 5432 is not in use by another process: `docker ps` or `netstat -an | findstr 5432` (Windows).

### LLM API errors or empty patches

- Verify `LLM_API_KEY`, `LLM_MODEL`, and `LLM_API_BASE` are correctly set.
- Test connectivity with: `python test_llm.py`
- If using a local Ollama instance, ensure it is running and the model is pulled: `ollama pull <model_name>`

### Embeddings fail to load

- Embeddings use `nomic-embed-text` via a local Ollama instance at `OLLAMA_BASE_URL`.
- If Ollama is not running locally, the embedding step will be skipped gracefully and RAG context will not be available.

### GitHub PR creation fails

- Verify `GITHUB_TOKEN` is set and has `repo` scope.
- Ensure the token has write access to the target repository.
- Check backend logs for git errors: `docker-compose logs backend`

### Webhook not reaching the backend from GitHub Actions

- Confirm the `AGENTIC_WEBHOOK_URL` secret is set in the target repository.
- Verify the ngrok tunnel (or equivalent) is active and forwarding to port 8000.
- Test locally with: `curl -X POST http://localhost:8000/webhook/ci_failure -H "Content-Type: application/json" -d '{"repo_name":"test","commit_hash":"abc","error_logs":"error","git_diff":"diff","status":"failed"}'`

---

## License

This project was developed as part of the HackToFuture 4.0 hackathon.
