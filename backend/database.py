"""
Database configuration and models for authentication system
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Enum as SQLEnum, Boolean
from datetime import datetime
from enum import Enum
import os

# Database URL
DATABASE_URL = "sqlite+aiosqlite:///./users.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    EXECUTIVE = "executive"
    VISITOR = "visitor"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.VISITOR)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(nullable=True)  # ID of admin who created this user

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Create tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Initialize database with admin user from .env
async def init_db():
    """Initialize database with admin user from environment variables"""
    from auth_service import AuthService
    
    await create_tables()
    
    # Create admin user from .env if it doesn't exist
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if admin_username and admin_password:
        async with AsyncSessionLocal() as session:
            auth_service = AuthService()
            
            # Check if admin user already exists
            existing_admin = await auth_service.get_user_by_username(session, admin_username)
            if not existing_admin:
                await auth_service.create_user(
                    session,
                    username=admin_username,
                    email=f"{admin_username}@terminal.local",
                    full_name="System Administrator",
                    password=admin_password,
                    role=UserRole.ADMIN,
                    created_by=None  # System created
                )
                print(f"✅ Created admin user: {admin_username}")
            else:
                print(f"ℹ️  Admin user already exists: {admin_username}")
