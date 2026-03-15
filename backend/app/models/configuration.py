from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class IndexConfiguration(Base):
    __tablename__ = "index_configurations"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    poverty_cutoff_k = Column(Float, nullable=False)
    subgroup_column = Column(String, nullable=True)
    dimensions = Column(JSON)  # [{name, indicators: [{name, source_column, deprivation_cutoff, cutoff_direction, weight, data_type}]}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="configuration")
