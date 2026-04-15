from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String, index=True)
    commit_hash = Column(String, index=True)
    error_logs = Column(Text)
    git_diff = Column(Text)
    status = Column(String, default="pending")  # pending, resolved
    
    # Store embedding. (4096 dimensions works for large models, 768 for models like nomic-embed-text)
    # DeepSeek or standard embedders often use 4096. We'll set it flexibly to a big size or just use standard vector
    error_embedding = Column(Vector(4096))

    fixes = relationship("FixProposal", back_populates="incident", cascade="all, delete-orphan")


class FixProposal(Base):
    __tablename__ = "fix_proposals"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    
    root_cause = Column(Text)
    patch_code = Column(Text)
    risk_score = Column(Integer)
    risk_reasoning = Column(Text)
    status = Column(String, default="pending_approval")  # pending_approval, approved, rejected

    incident = relationship("Incident", back_populates="fixes")
