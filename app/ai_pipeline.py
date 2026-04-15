import json
import os
import re
from typing import Dict, Any
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.prompts import PromptTemplate

# E.g. "llama3", "deepseek-coder", or "qwen"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Initialize the LLM (using simple Ollama for text completion)
llm = Ollama(model=MODEL_NAME, base_url=OLLAMA_BASE_URL)
embeddings_model = OllamaEmbeddings(model=MODEL_NAME, base_url=OLLAMA_BASE_URL)

DETECTIVE_PROMPT = PromptTemplate(
    input_variables=["error_logs", "git_diff", "context_str"],
    template="""You are a Senior DevOps Detective.
Analyze the following failing CI/CD logs and the recent git diff.
Historical context from similar past errors: {context_str}
Git Diff:
{git_diff}
Error Logs:
{error_logs}

Task: Write a concise, 1-3 sentence plain English summary of exactly why this build failed and what needs to change. Do NOT write code. Respond with the summary only."""
)

DEV_PROMPT = PromptTemplate(
    input_variables=["git_diff", "detective_summary"],
    template="""You are an Expert Developer.
The CI failed. The Detective found the issue: {detective_summary}
The recent Git Diff that likely caused the failure:
{git_diff}

Task: Write the specific code patch (in unified diff format) required to fix the repository based on the Detective's findings. 
Respond ONLY with the code patch, inside markdown ```diff ``` blocks."""
)

REVIEWER_PROMPT = PromptTemplate(
    input_variables=["patch", "detective_summary"],
    template="""You are a Security & Risk Assessor.
Analyze the proposed code patch for a fix:
Issue Context: {detective_summary}
Proposed Patch:
{patch}

Evaluate the patch on a scale of 1-100 (100 being extremely high risk) based on these 5 heuristics:
1. Scope of Change (Lines of Code)
2. Impact on Dependencies/Config
3. Security & Vulnerability exposure (e.g. raw SQL, shell execution)
4. State & Database alterations
5. Presence of fallback/safety mechanisms (e.g. try/catch)

Respond in strictly valid JSON format with keys "risk_score" (integer) and "reasoning" (string).
Example:
{{"risk_score": 25, "reasoning": "Simple 1-line syntax fix, low risk."}}"""
)

def extract_code_block(text: str) -> str:
    matches = re.findall(r"```(?:diff|python)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()
    return text.strip()

def extract_json(text: str) -> dict:
    try:
        # Attempt to grab JSON if there's markdown wrapping it
        matches = re.findall(r"\{.*\}", text, re.DOTALL)
        if matches:
            return json.loads(matches[0])
        return json.loads(text)
    except Exception:
        return {"risk_score": 99, "reasoning": f"Failed to parse AI response: {text}"}

async def run_repair_pipeline(error_logs: str, git_diff: str, context_str: str = "") -> Dict[str, Any]:
    """Runs the 3-agent Multi-Agent Pipeline synchronously."""
    try:
        # Agent 1: Detective
        detective_chain = DETECTIVE_PROMPT | llm
        detective_summary = detective_chain.invoke({
            "error_logs": error_logs, 
            "git_diff": git_diff, 
            "context_str": context_str
        })
        
        # Agent 2: Developer
        dev_chain = DEV_PROMPT | llm
        raw_patch = dev_chain.invoke({
            "detective_summary": detective_summary,
            "git_diff": git_diff
        })
        patch_code = extract_code_block(raw_patch)
        
        # Agent 3: Reviewer
        reviewer_chain = REVIEWER_PROMPT | llm
        raw_review = reviewer_chain.invoke({
            "patch": patch_code,
            "detective_summary": detective_summary
        })
        review_data = extract_json(raw_review)
        
        return {
            "root_cause": detective_summary.strip(),
            "patch_code": patch_code,
            "risk_score": review_data.get("risk_score", 50),
            "risk_reasoning": review_data.get("reasoning", "No reasoning provided.")
        }
    except Exception as e:
        print(f"Pipeline error: {e}")
        return {
            "root_cause": f"Pipeline failed: {str(e)}",
            "patch_code": "",
            "risk_score": 100,
            "risk_reasoning": "Error executing the AI pipeline."
        }
