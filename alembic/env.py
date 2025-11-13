from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import asyncio
import sys
import os

# Add your project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import your Base and other models
from app.db.base import Base
from app.models.business import Business
#from app.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = "postgresql+asyncpg://postgres:success8085.com@localhost:8085/new_db_shop"

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online2():
    """Run migrations in 'online' mode."""
    url = "postgresql+asyncpg://postgres:success8085.com@localhost:8085/new_db_shop"
    connectable = create_async_engine(url)

    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda sync_conn: context.configure(
                connection=sync_conn, 
                target_metadata=target_metadata
            )
        )

        async with connection.begin():
            await connection.run_sync(context.run_migrations)

async def run_migrations_online():
    url = "postgresql+asyncpg://postgres:success8085.com@localhost:8085/new_db_shop"
    connectable = create_async_engine(url)

    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda sync_conn: context.configure(
                connection=sync_conn, 
                target_metadata=target_metadata
            )
        )

        async with connection.begin():
            await connection.run_sync(context.run_migrations)

def main():
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())

if __name__ == '__main__':
    main()