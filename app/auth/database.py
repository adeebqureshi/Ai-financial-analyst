from __future__ import annotations
from collections.abc import Iterator
from pathlib import Path
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import Settings
from app.infrastructure.postgres import create_db_engine
class Base(DeclarativeBase):
_engines: dict[str, Engine] = {}
def _engine_for(database_url: str) -> Engine:
    engine = _engines.get(database_url)
    if engine is not None:
        return engine
    if database_url.startswith("sqlite:///"):
        db_path = database_url.removeprefix("sqlite:///")
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_db_engine(database_url)
    _engines[database_url] = engine
    return engine
def get_engine(settings: Settings) -> Engine:
    return _engine_for(settings.auth_database_url)
def dispose_all_engines() -> None:
    engines = list(_engines.values())
    _engines.clear()
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
        alembic_cfg.set_section_option("alembic_auth", "sqlalchemy.url", database_url)
        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        raise RuntimeError(f"Failed to run authentication database migrations: {exc}") from exc
def init_db(settings: Settings) -> None:
    from app.auth import models
    engine = get_engine(settings)
    database_url = settings.auth_database_url
    if _is_postgresql(database_url):
        run_migrations(database_url)
    else:
        Base.metadata.create_all(bind=engine)
def get_db_session(settings: Settings) -> Iterator[Session]:
    init_db(settings)
    factory = sessionmaker(
        bind=get_engine(settings),
        autoflush=False,
        expire_on_commit=False,
    )
    session = factory()
    try:
        yield session
    finally:
        session.close()