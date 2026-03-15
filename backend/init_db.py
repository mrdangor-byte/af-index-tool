"""Initialize database tables."""
import sys
from pathlib import Path

# Add engine to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from app.database import engine
from app.models import user, project, dataset, configuration, result

def init():
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init()
