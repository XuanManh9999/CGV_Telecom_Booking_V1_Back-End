from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Kết nối Database (Chỉnh sửa username, password, dbname cho đúng)
# DATABASE_URL = "postgresql+asyncpg://root:root@localhost:5432/db_booking_cgv"
DATABASE_URL = settings.DATABASE_URL

# Tạo engine kết nối với database (async)
engine = create_async_engine(DATABASE_URL, echo=True)

# Tạo session factory để quản lý kết nối DB
async_session_maker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Base cho ORM Models
Base = declarative_base()

# Dependency để inject session vào route
async def get_db():
    async with async_session_maker() as session:
        yield session
