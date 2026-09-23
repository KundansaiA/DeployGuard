"""Alembic environment configuration for DeployGuard.

Reads the database URL from app.config.settings (which sources it from
the DB_URL environment variable / .env file).  This ensures Alembic and
FastAPI always use the same connection string — there is no separate
hard-coded URL in this file.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ── Load application config & models ──────────────────────────────────────────
# Import settings so the DB URL is available.
from app.config import settings

# Import Base and all ORM models so their metadata is registered.
# Adding new models here makes them visible to autogenerate.
from app.database import Base
import app.models.analysis  # noqa: F401 — registers Analysis + RiskSignalRecord

# ── Alembic Config object ──────────────────────────────────────────────────────
config = context.config

# Inject the application DB URL — overrides the placeholder in alembic.ini
config.set_main_option("sqlalchemy.url", settings.db_url)

# Set up Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata used by autogenerate
target_metadata = Base.metadata


# ── Offline mode (generate SQL without a live DB connection) ──────────────────
def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting to the database."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connect and migrate) ─────────────────────────────────────────
def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
