import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger("visioninspect.database")

# Primary DATABASE_URL fallback to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./visioninspect.db")

# Handle standard postgres:// protocol mapping
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure database engine
try:
    if "sqlite" in DATABASE_URL:
        engine = create_engine(
            DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL pool configuration
        engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
    # Test connection
    with engine.connect() as conn:
        logger.info("Database connection established successfully.")
except Exception as e:
    logger.error(f"Failed to connect to database {DATABASE_URL}: {e}")
    logger.warning("Falling back to local SQLite database: sqlite:///./visioninspect.db")
    DATABASE_URL = "sqlite:///./visioninspect.db"
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initializes tables in PostgreSQL (or SQLite fallback)"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

def get_db():
    """FastAPI database session generator dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
