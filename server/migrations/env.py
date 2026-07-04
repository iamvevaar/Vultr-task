"""
Alembic environment.

This runs whenever we generate or apply a migration. Its jobs:
  - point Alembic at OUR database (from settings, not a hardcoded URL), and
  - give it OUR models' metadata so `--autogenerate` can diff models vs the DB.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
# Importing app.models registers every model on Base.metadata. Autogenerate
# compares THIS metadata against the live database to compute the diff.
from app.models import Base

config = context.config

# Inject the real database URL from our Settings.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Set up logging from alembic.ini if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection (rarely used here)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,  # detect column TYPE changes, not just add/drop
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the DB and apply migrations (the normal path)."""
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
