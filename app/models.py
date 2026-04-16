from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
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
    # Changed to 768: HNSW indexing in pgvector is limited to maximum 2000 dimensions.
    error_embedding = Column(Vector(768))

    __table_args__ = (
        Index('hnsw_index_for_error_embedding',
              'error_embedding',
              postgresql_using='hnsw',
              postgresql_with={'m': 16, 'ef_construction': 64},
              postgresql_ops={'error_embedding': 'vector_cosine_ops'}),
    )

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
    pr_url = Column(String, nullable=True)

    incident = relationship("Incident", back_populates="fixes")
