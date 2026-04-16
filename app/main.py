from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.database import init_db, get_db
from app.models import Incident, FixProposal
from app.schemas import WebhookPayload, IncidentResponse, FixResponse
from app.ai_pipeline import run_repair_pipeline, embeddings_model

import uvicorn
import os

app = FastAPI(title="Agentic CI/CD Repair System")

# Serve the Dashboard static files
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def on_startup():
    await init_db()

async def bg_process_incident(incident_id: int):
    async for db in get_db():
        result = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = result.scalar_one_or_none()
        if not incident:
            return
            
        context_str = ""
        # 1. RAG Context Retrieval (find past errors that are similar)
        try:
            curr_embedding = embeddings_model.embed_query(incident.error_logs)
            incident.error_embedding = curr_embedding
            
            # Semantic search: get nearest 1 incident that actually has a fix
            past_docs = await db.execute(
                select(Incident, FixProposal)
                .join(FixProposal, FixProposal.incident_id == Incident.id)
                .where(Incident.id != incident_id)
                .where(FixProposal.status == 'approved')
                .order_by(Incident.error_embedding.l2_distance(curr_embedding))
                .limit(1)
            )
            
            for past_inc, past_fix in past_docs:
                context_str += f"- Past Error Log Match: {past_inc.error_logs[:150]}...\n- Past Approved Fix: {past_fix.patch_code}\n\n"
        except Exception as e:
            print(f"Embedding/RAG error (can be ignored if Ollama isn't running): {e}")

        # 2. Run the Multi-Agent Pipeline
        ai_result = await run_repair_pipeline(
            error_logs=incident.error_logs,
            git_diff=incident.git_diff,
            context_str=context_str
        )
        
        # 3. Store the Proposal
        proposal = FixProposal(
            incident_id=incident.id,
            root_cause=ai_result["root_cause"],
            patch_code=ai_result["patch_code"],
            risk_score=ai_result["risk_score"],
            risk_reasoning=ai_result["risk_reasoning"],
            status="pending_approval"
        )
        db.add(proposal)
        await db.commit()
        
        print(f"\n[!] AI REVIEW REQUIRED for Incident #{incident.id}")
        print(f"URL: http://localhost:8000/dashboard\n")
        break


@app.post("/webhook/ci_failure")
async def ci_failure_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # Create the Incident
    new_incident = Incident(
        repo_name=payload.repo_name,
        commit_hash=payload.commit_hash,
        error_logs=payload.error_logs,
        git_diff=payload.git_diff,
        status="pending"
    )
    db.add(new_incident)
    await db.commit()
    await db.refresh(new_incident)
    
    # Run the AI logic in background
    background_tasks.add_task(bg_process_incident, new_incident.id)
    
    return {"message": "Incident received. Agentic pipeline processing.", "incident_id": new_incident.id}

@app.get("/api/incidents", response_model=list[IncidentResponse])
async def get_incidents(db: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Incident).options(selectinload(Incident.fixes)).order_by(desc(Incident.id))
    )
    return result.scalars().all()

@app.post("/api/fixes/{fix_id}/approve")
async def approve_fix(fix_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FixProposal).where(FixProposal.id == fix_id))
    fix_proposal = result.scalar_one_or_none()
    if not fix_proposal:
        raise HTTPException(status_code=404, detail="Fix proposal not found")
        
    fix_proposal.status = "approved"
    
    # Simulate or execute PR resolution
    result = await db.execute(select(Incident).where(Incident.id == fix_proposal.incident_id))
    incident = result.scalar_one_or_none()
    incident.status = "resolved"
    await db.commit()
    
    from app.github_integration import apply_and_commit_to_main
    commit_url = apply_and_commit_to_main(
        repo_name=incident.repo_name,
        base_commit=incident.commit_hash,
        patch_code=fix_proposal.patch_code,
        title=f"Agentic Fix: CI Pipeline Failure ({incident.commit_hash[:7]})",
        description=f"Root Cause:\n{fix_proposal.root_cause}\n\nRisk Reasoning:\n{fix_proposal.risk_reasoning}"
    )

    fix_proposal.pr_url = commit_url  # reusing pr_url column to avoid schema migration
    await db.commit()

    print(f"\n[SUCCESS] Patch applied directly to the repository {incident.repo_name}! Commit URL: {commit_url}\n")
    return {"message": "Fix approved. Patch committed to main branch.", "status": "approved", "pr_url": commit_url}

@app.post("/api/fixes/{fix_id}/reject")
async def reject_fix(fix_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FixProposal).where(FixProposal.id == fix_id))
    fix_proposal = result.scalar_one_or_none()
    if not fix_proposal:
        raise HTTPException(status_code=404, detail="Fix proposal not found")
        
    fix_proposal.status = "rejected"
    await db.commit()
    return {"message": "Fix rejected.", "status": "rejected"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with open("app/static/index.html", "r") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
