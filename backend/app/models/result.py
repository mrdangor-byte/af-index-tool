from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    H = Column(Float)
    A = Column(Float)
    M0 = Column(Float)
    q = Column(Integer)
    n = Column(Integer)
    dimensional_breakdown = Column(JSON)
    subgroup_decomposition = Column(JSON)
    robustness_results = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="results")
