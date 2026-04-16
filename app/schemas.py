from pydantic import BaseModel
from typing import Optional, List

class WebhookPayload(BaseModel):
    repo_name: str
    commit_hash: str
    error_logs: str
    git_diff: str
    status: str

class FixResponse(BaseModel):
    id: int
    root_cause: str
    patch_code: str
    risk_score: int
    risk_reasoning: str
    status: str
    pr_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class IncidentResponse(BaseModel):
    id: int
    repo_name: str
    commit_hash: str
    error_logs: str
    status: str
    fixes: List[FixResponse] = []
    
    class Config:
        from_attributes = True
