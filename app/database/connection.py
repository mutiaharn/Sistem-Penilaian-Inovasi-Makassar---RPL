import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger("idp.database")
Base = declarative_base()

def init_engine():
    """Attempt connecting to PostgreSQL, with graceful fallback to SQLite for local development."""
    url = settings.DATABASE_URL
    try:
        # Fast 2-second timeout so offline startup doesn't lag
        engine = create_engine(
            url, 
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2} if "postgres" in url else {}
        )
        with engine.connect() as conn:
            logger.info("Connected successfully to primary database (PostgreSQL).")
        return engine, "postgresql"
    except Exception as e:
        logger.warning(f"PostgreSQL at {url} not currently available: {e}")
        logger.info(f"Using local development database: {settings.SQLITE_FALLBACK_URL}")
        sqlite_engine = create_engine(
            settings.SQLITE_FALLBACK_URL, 
            connect_args={"check_same_thread": False}
        )
        return sqlite_engine, "sqlite"

engine, DB_DIALECT = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all registered database tables."""
    # Import domain tambahan supaya model-nya terdaftar di Base.metadata
    from app.database import assessment_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
