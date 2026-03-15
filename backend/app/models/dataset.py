from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    row_count = Column(Integer)
    column_metadata = Column(JSON)  # [{name, dtype, missing_count, unique_count, min, max, mean}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="dataset")
