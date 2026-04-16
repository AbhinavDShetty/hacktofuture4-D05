import os
import json
import re
from typing import Dict, Any, TypedDict
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_community.embeddings import OllamaEmbeddings
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

# Configured to use external/cloud Ollama endpoint
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-oss:120b-cloud")
API_BASE = os.getenv("LLM_API_BASE", "http://localhost:11434")  # Set this to the cloud URL
API_KEY = os.getenv("LLM_API_KEY", "EMPTY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Configure custom Http Headers to forcefully inject the Ollama API key
ollama_headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY != "EMPTY" else {}

try:
    embeddings_model = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)
except Exception as e:
    print("Warning: Could not load embeddings.", e)
    embeddings_model = None


# --- STATE SCHEMA ---
class AgenticState(TypedDict):
    error_logs: str
    git_diff: str
    context_str: str
    
    detective_summary: str
    proposed_patch: str
    security_score: int
    security_reasoning: str


# --- LANGGRAPH NODES ---

async def detective_node(state: AgenticState):
    """Parses raw error logs and historical context into a clean summary."""
    print("-> Detective Agent thinking...")
    llm = ChatOllama(model=MODEL_NAME, base_url=API_BASE, temperature=0.1, client_kwargs={"headers": ollama_headers})
    prompt = f"""You are the Detective Agent. Analyze these error logs and historical context to determine the root cause of the CI/CD failure. Return ONLY a 1-3 sentence summary explaining why it failed.
    
Logs:
{state['error_logs']}

Context:
{state['context_str']}"""
    response = await llm.ainvoke(prompt)
    return {"detective_summary": response.content}


async def developer_node(state: AgenticState):
    """Generates the code patch based on Detective's summary."""
    print("-> Developer Agent drafting fix...")
    llm = ChatOllama(model=MODEL_NAME, base_url=API_BASE, temperature=0.2, client_kwargs={"headers": ollama_headers})
    prompt = f"""You are the Developer Agent. Based on this root cause analysis:
{state['detective_summary']}

And the original Git Diff:
{state['git_diff']}

Generate ONLY the valid unified diff patch needed to fix this exact issue. 
You MUST provide standard unified diff context headers containing the precise original and new line coordinates (e.g., @@ -34,5 +34,5 @@). Do not just output '@@'. Patches missing line coordinates will be heavily rejected.
Do not include markdown codeblocks or explanations outside the patch itself. Output pure diff."""
    response = await llm.ainvoke(prompt)
    
    # Strip markdown formatting occasionally outputted by LLMs
    patch_code = response.content.replace("```diff", "").replace("```", "").strip()
    return {"proposed_patch": patch_code}


class SecurityEvaluation(BaseModel):
    risk_score: int = Field(description="Risk score from 1-100 (100 being extreme risk) assessing stability, sql-injection, dependencies, etc.")
    risk_reasoning: str = Field(description="Why you assigned this score.")

async def security_node(state: AgenticState):
    """Reviews the patch and yields a security risk score."""
    print("-> Security Agent analyzing risks...")
    llm = ChatOllama(model=MODEL_NAME, base_url=API_BASE, temperature=0.0, format="json", client_kwargs={"headers": ollama_headers})
    
    prompt = f"Review this proposed fix patch for vulnerabilities, scope bleed, and stability:\n{state['proposed_patch']}\n\nYou MUST respond entirely in pure JSON format containing exactly two keys: 'risk_score' (integer 1-100) and 'risk_reasoning' (string)."
    try:
        response = await llm.ainvoke(prompt)
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        return {"security_score": int(data.get("risk_score", 50)), "security_reasoning": str(data.get("risk_reasoning", "Risk evaluated correctly."))}
    except Exception as e:
        print(f"Failed structured security parsing: {e}")
        return {"security_score": 50, "security_reasoning": "Could not parse JSON schema natively. Applying fallback neutral assessment."}


# --- GRAPH ORCHESTRATION ---
builder = StateGraph(AgenticState)
builder.add_node("detective", detective_node)
builder.add_node("developer", developer_node)
builder.add_node("security", security_node)

builder.set_entry_point("detective")
builder.add_edge("detective", "developer")
builder.add_edge("developer", "security")
builder.add_edge("security", END)

agentic_graph = builder.compile()


async def run_repair_pipeline(error_logs: str, git_diff: str, context_str: str = "") -> Dict[str, Any]:
    """Runs the 3-Stage LangGraph Agentic Pipeline."""
    print(f"\n[*] Booting LangGraph CI/CD Repair Pipeline on {MODEL_NAME} (Cloud Hosted)...")
    try:
        state = {
            "error_logs": error_logs,
            "git_diff": git_diff,
            "context_str": context_str
        }
        final_state = await agentic_graph.ainvoke(state)
        return {
            "root_cause": final_state.get("detective_summary", "Unknown Error"),
            "patch_code": final_state.get("proposed_patch", "No patch available."),
            "risk_score": final_state.get("security_score", 0),
            "risk_reasoning": final_state.get("security_reasoning", "No evaluation.")
        }
    except Exception as e:
        print(f"[!] LangGraph Agentic Pipeline execution failed: {e}")
        
        # Return the authentic error dynamically so the user sees exactly what the Cloud API failed on
        return {
            "root_cause": f"CRITICAL PIPELINE FAILURE: The AI Provider declined the generation. Error details: {str(e)}",
            "patch_code": "# The multi-agent system could not generate a patch due to an API rejection.",
            "risk_score": 100,
            "risk_reasoning": "Failed to invoke LangGraph agents securely."
        }
