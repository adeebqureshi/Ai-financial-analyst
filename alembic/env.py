from __future__ import annotations
import os
import sys
from logging.config import fileConfig
from pathlib import Path
from alembic import context
from sqlalchemy import engine_from_config, pool
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
from app.auth.database import Base as AuthBase
from app.chat.database import Base as ChatBase
from app.auth import models as auth_models
from app.chat import models as chat_models
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
database = context.get_x_argument(as_dictionary=True).get("database", "auth")
if database == "auth":
    target_metadata = AuthBase.metadata
    version_table = "auth_alembic_version"
    section = "alembic_auth"
elif database == "chat":
    target_metadata = ChatBase.metadata
    version_table = "chat_alembic_version"
    section = "alembic_chat"
else:
    raise ValueError(f"Unknown database: {database}. Use 'auth' or 'chat'.")
def get_database_url() -> str:
    if database == "auth":
        url = os.getenv("AUTH_DATABASE_URL")
        if not url:
            url = config.get_section_option(section, "sqlalchemy.url", None)
    else:
        url = os.getenv("CHAT_DATABASE_URL")
        if not url:
            url = config.get_section_option(section, "sqlalchemy.url", None)
    if not url:
        raise RuntimeError(
            f"Database URL not configured. Set {database.upper()}_DATABASE_URL "
            f"environment variable or configure [{section}] in alembic.ini"
        )
    return url
def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        version_table=version_table,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()
def run_migrations_online() -> None:
    configuration = config.get_section(section, {})
    configuration["sqlalchemy.url"] = get_database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=version_table,
            compare_type=True,
            compare_server_default=True,
            include_schemas=False,
        )
        with context.begin_transaction():
            context.run_migrations()
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()