from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    ANALYZED = "analyzed"
    COMPLETE = "complete"


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    current_step = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    dataset = relationship("Dataset", back_populates="project", uselist=False, cascade="all, delete-orphan")
    configuration = relationship("IndexConfiguration", back_populates="project", uselist=False, cascade="all, delete-orphan")
    results = relationship("AnalysisResult", back_populates="project", uselist=False, cascade="all, delete-orphan")
