"""
Authentication service with JWT tokens and password hashing
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import User, UserRole
import os

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.pwd_context = pwd_context
        self.ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return payload
        except JWTError:
            return None
    
    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def authenticate_user(self, db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = await self.get_user_by_username(db, username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        return user
    
    async def create_user(
        self, 
        db: AsyncSession, 
        username: str, 
        email: str, 
        full_name: str, 
        password: str, 
        role: UserRole,
        created_by: Optional[int] = None
    ) -> User:
        """Create a new user"""
        hashed_password = self.get_password_hash(password)
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            created_by=created_by,
            is_active=True
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def update_user(
        self,
        db: AsyncSession,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> Optional[User]:
        """Update user information"""
        user = await self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if full_name is not None:
            user.full_name = full_name
        if password is not None:
            user.hashed_password = self.get_password_hash(password)
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        """Delete user (soft delete by setting is_active=False)"""
        user = await self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.is_active = False
        await db.commit()
        
        return True
    
    async def get_all_users(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        """Get all users with pagination"""
        result = await db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return result.scalars().all()
    
    def has_permission(self, user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user role has permission for required role"""
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.OPERATOR: 3,
            UserRole.EXECUTIVE: 2,
            UserRole.VISITOR: 1
        }
        
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
