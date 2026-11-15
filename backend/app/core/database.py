import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("ayucare.database")

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_is_mysql = settings.DATABASE_URL.startswith("mysql")

engine_args: dict = {}
if _is_sqlite:
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    # MySQL / PostgreSQL — tuned connection pool for a small hackathon workload
    engine_args["pool_pre_ping"] = True      # Reconnect if connection was dropped
    engine_args["pool_recycle"] = 1800       # Recycle after 30 min (MySQL wait_timeout safe)
    engine_args["pool_size"] = 5             # Base pool size
    engine_args["max_overflow"] = 10         # Extra connections under burst load

engine = create_engine(settings.DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_compatibility():
    """
    Applies non-destructive schema migrations for columns added after initial deployment.
    Works for both SQLite (PRAGMA-based) and MySQL (INFORMATION_SCHEMA-based).
    Called at application startup via lifespan event.
    """
    try:
        with engine.connect() as conn:
            if _is_sqlite:
                # SQLite: use PRAGMA table_info
                for table, col, col_def in [
                    ("profile_members", "language", "VARCHAR(8) DEFAULT 'en'"),
                    ("profiles", "language", "VARCHAR(8) DEFAULT 'en'"),
                ]:
                    res = conn.execute(text(f"PRAGMA table_info({table})"))
                    existing = [row[1] for row in res.fetchall()]
                    if existing and col not in existing:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}"))
                        conn.commit()
                        logger.info(f"SQLite migration: added {table}.{col}")

            elif _is_mysql:
                # MySQL: use INFORMATION_SCHEMA
                db_name = settings.DATABASE_URL.split("/")[-1].split("?")[0]
                for table, col, col_def in [
                    ("profile_members", "language", "VARCHAR(8) NOT NULL DEFAULT 'en'"),
                    ("profiles", "language", "VARCHAR(8) NOT NULL DEFAULT 'en'"),
                ]:
                    res = conn.execute(text(
                        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA=:db AND TABLE_NAME=:tbl AND COLUMN_NAME=:col"
                    ), {"db": db_name, "tbl": table, "col": col})
                    if res.scalar() == 0:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}"))
                        conn.commit()
                        logger.info(f"MySQL migration: added {table}.{col}")

    except Exception as exc:
        logger.warning(f"Schema compatibility check skipped: {exc}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
