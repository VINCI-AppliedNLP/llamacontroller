"""
Database basic configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/llamacontroller.db"
)

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Set to True to see SQL statements
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base class
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency injection function for database session
    
    For FastAPI dependency injection:
    ```python
    @app.get("/")
    def read_root(db: Session = Depends(get_db)):
        ...
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database (create all tables)
    """
    # Import all models to ensure they are registered
    from llamacontroller.db import models  # noqa: F401
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    """
    Reset database (drop and recreate all tables)
    
    Warning: This will delete all data! For development/testing only
    """
    from llamacontroller.db import models  # noqa: F401
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
