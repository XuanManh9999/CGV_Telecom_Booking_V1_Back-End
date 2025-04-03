import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.database.models import *  # Import tất cả models
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
# DATABASE_URL = "postgresql+asyncpg://root:root@localhost:5432/db_booking_cgv"
# DATABASE_URL = "postgresql+asyncpg://cgv_root_booking_app:cgv_root@13.229.236.236:5432/db_booking_cgv"
DATABASE_URL = "postgresql+asyncpg://CGV_USER_DB:Cgv@vip2018@172.17.0.1:5432/db_booking_cgv"
connectable = create_async_engine(DATABASE_URL, echo=True, future=True)



def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection):  # ⚠️ Phải là hàm đồng bộ!
    """Hàm chạy migration đồng bộ."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
