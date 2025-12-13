from sqlalchemy import create_engine, pool, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def create_db_engine():
    """
    Create database engine with configuration based on DATABASE_URL.
    Supports both PostgreSQL (with PostGIS) and SQLite (with SpatiaLite).
    """
    db_url = settings.DATABASE_URL
    
    if db_url.startswith("sqlite"):
        # SQLite configuration for development/testing
        logger.info("Configuring SQLite database engine")
        
        # SQLite-specific connection args
        connect_args = {
            "check_same_thread": False,  # Allow multi-threaded access
        }
        
        engine = create_engine(
            db_url,
            connect_args=connect_args,
            poolclass=pool.StaticPool,  # Use StaticPool for SQLite
        )
        
        # Enable SpatiaLite extension for spatial queries (optional)
        @event.listens_for(engine, "connect")
        def load_spatialite(dbapi_conn, connection_record):
            """Load SpatiaLite extension if available"""
            dbapi_conn.enable_load_extension(True)
            try:
                # Try common SpatiaLite module names
                try:
                    dbapi_conn.load_extension("mod_spatialite")
                    logger.info("SpatiaLite extension loaded successfully")
                except Exception:
                    # Try alternative name
                    dbapi_conn.load_extension("mod_spatialite.so")
                    logger.info("SpatiaLite extension loaded successfully (mod_spatialite.so)")
            except Exception as e:
                # SpatiaLite not available - spatial queries will be limited
                logger.warning(f"SpatiaLite extension not available: {e}. Spatial queries will be limited.")
            finally:
                dbapi_conn.enable_load_extension(False)
        
        return engine
    
    else:
        # PostgreSQL configuration for production
        logger.info("Configuring PostgreSQL database engine")
        return create_engine(
            db_url,
            poolclass=pool.QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using them
            pool_recycle=3600,   # Recycle connections after 1 hour
            connect_args={"connect_timeout": 10}  # Connection timeout
        )

# Create engine
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
