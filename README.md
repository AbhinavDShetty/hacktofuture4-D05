# HackToFuture 4.0 — Agentic CI/CD Repair System

An AI-driven DevOps system leveraging a Multi-Agent architecture to autonomously detect, diagnose, and propose surgical fixes for CI/CD failures, heavily gated by human oversight.

---

## 🛑 Problem Statement / Idea

**What is the problem?**
Modern CI/CD pipelines fail constantly due to trivial syntax errors, missing dependencies, or breaking upstream changes. Developers spend countless hours context-switching, reading massive unstructured error logs, and hunting down the exact line of code that caused the build to break. 

**Why is it important?**
Developer friction and pipeline downtime drastically reduce engineering velocity. Automated fixes are dangerous, but manually diagnosing every failure is inefficient.

**Who are the target users?**
DevOps Engineers, SREs, and Software Developers working in fast-paced continuous deployment environments.

---

## 💡 Proposed Solution

**What are you building?**
We built an **Agentic CI/CD Repair** pipeline. When a GitHub Actions build fails, a native hook extracts the logs and `git diff`, firing them to our backend. 

**How does it solve the problem?**
Instead of a human reading the logs, a **Multi-Agent AI Pipeline** (Detective ➔ Developer ➔ Security Reviewer) parses the logs natively, retrieves historical context using vector search, figures out exactly what broke, and writes the Git Diff patch to fix the repository automatically. 

**What makes your solution unique?**
1. **Multi-Agent Architecture:** We don't rely on a single confused AI. We use 3 specific, specialized LangChain agents operating locally via Ollama.
2. **Immutable Human Oversight:** To completely eliminate the danger of "Agentic AI breaking production," our system is locked. The Risk Score and Git Patch are held in a holding area until a human clicks "Approve" on our custom dashboard, allowing it to generate the fixing Pull Request safely.

---

## 🔥 Features

- **Automated Webhook Triggers:** Native CLI hooks safely bypass Docker-in-Docker Github action limitations.
- **RAG Memory:** Utilizing PostgreSQL with the `pgvector` extension, the AI remembers past bugs and how they were solved.
- **Strict Risk Assessment:** AI mathematically scores its proposed patches based on 5 security heuristics (Vulnerabilities, Scope, Database Alterations, etc).
- **Oversight Dashboard:** Real-time web UI allowing developers to monitor AI telemetry and perform 1-click approvals for patches.
- **Offline & Private AI:** Everything runs locally using `Ollama`, meaning no sensitive corporate source code is ever sent to OpenAI or cloud providers.

---

## 🛠️ Tech Stack

- **Frontend:** HTML5, CSS3, Vanilla JS
- **Backend:** FastAPI (Python), Uvicorn, Async handlers
- **AI & ML:** LangChain, Local Ollama (DeepSeek/LLaMA), RAG Embeddings
- **Database:** PostgreSQL configured with `pgvector` and SQLAlchemy ORM
- **Infra:** Docker, Docker Compose

---

## 🚀 Project Setup Instructions

Follow these steps to run the stack locally. Ensure you have Docker Desktop and [Ollama](https://ollama.com/) installed on your machine.

```bash
# 1. Clone the repository
git clone <repo-link>
cd <repo-folder>

# 2. Start the FastAPI backend and Postgres pgvector Database
docker-compose up --build -d

# 3. View the live CI/CD Monitoring Dashboard
# Open your browser to: http://localhost:8000/dashboard

# 4. Trigger the Mock pipeline failure (simulate a broken CI build)
pip install requests
python agentic_repair_cli.py push --endpoint http://localhost:8000/webhook/ci_failure

# 5. Boom! Watch the dashboard automatically populate with the AI's patch.
```
