from __future__ import annotations
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.infrastructure.postgres import create_db_engine
class ChatPersistenceError(Exception):
class Base(DeclarativeBase):
def _tune_sqlite(engine: Engine, database_url: str) -> Engine:
    if ":memory:" in database_url:
        return engine
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()
    return engine
_engines: dict[str, Engine] = {}
@lru_cache(maxsize=8)
def _engine_for(database_url: str) -> Engine:
    if database_url.startswith("sqlite:///"):
        db_path = database_url.removeprefix("sqlite:///")
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_db_engine(database_url)
    if database_url.startswith("sqlite:///"):
        _tune_sqlite(engine, database_url)
    _engines[database_url] = engine
    return engine
def get_engine(database_url: str) -> Engine:
    return _engine_for(database_url)
def dispose_engine(database_url: str) -> None:
    engine = _engines.pop(database_url, None)
    if engine is not None:
        try:
            engine.dispose()
        except Exception:
            pass
    _engine_for.cache_clear()
def dispose_all_engines() -> None:
    engines = list(_engines.values())
    _engines.clear()
    _engine_for.cache_clear()
    for engine in engines:
        try:
            engine.dispose()
        except Exception:
            pass
def _is_postgresql(database_url: str) -> bool:
    return database_url.startswith("postgresql")
def run_migrations(database_url: str) -> None:
    if not _is_postgresql(database_url):
        return
    try:
        from alembic import command
        from alembic.config import Config
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        alembic_cfg.set_section_option("alembic_chat", "sqlalchemy.url", database_url)
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        raise RuntimeError(f"Failed to run chat database migrations: {exc}") from exc
def init_db(database_url: str) -> None:
    from app.chat import models
    engine = get_engine(database_url)
    if _is_postgresql(database_url):
        run_migrations(database_url)
    else:
        Base.metadata.create_all(bind=engine)
def get_db_session(database_url: str) -> Iterator[Session]:
    init_db(database_url)
    factory = sessionmaker(
        bind=get_engine(database_url),
        autoflush=False,
        expire_on_commit=False,
    )
    session = factory()
    try:
        yield session
    finally:
        session.close()