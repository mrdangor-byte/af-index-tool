from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine as db_engine
from .models import User, Project, Dataset, IndexConfiguration, AnalysisResult  # noqa: F401 — ensure all models are registered
from .auth.router import router as auth_router
from .projects.router import router as projects_router
from .data.router import router as data_router
from .configuration.router import router as config_router
from .analysis.router import router as analysis_router
from .export.router import router as export_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (idempotent — safe to run every time)
    Base.metadata.create_all(bind=db_engine)
    yield


app = FastAPI(title="AF Index Tool", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
app.include_router(data_router, prefix="/api", tags=["data"])
app.include_router(config_router, prefix="/api", tags=["configuration"])
app.include_router(analysis_router, prefix="/api", tags=["analysis"])
app.include_router(export_router, prefix="/api", tags=["export"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
