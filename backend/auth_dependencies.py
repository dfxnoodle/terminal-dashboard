"""
FastAPI dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, User, UserRole
from auth_service import AuthService
from typing import Optional

# Security scheme
security = HTTPBearer(auto_error=False)

# Auth service instance
auth_service = AuthService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = auth_service.verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Get user from database
        user = await auth_service.get_user_by_username(db, username)
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
    
    except Exception as e:
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: UserRole):
    """Dependency factory to require specific role or higher"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not auth_service.has_permission(current_user.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

# Specific role dependencies
require_admin = require_role(UserRole.ADMIN)
require_operator = require_role(UserRole.OPERATOR)
require_executive = require_role(UserRole.EXECUTIVE)
require_visitor = require_role(UserRole.VISITOR)

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if token is provided (optional authentication)"""
    if not credentials:
        return None
    
    try:
        payload = auth_service.verify_token(credentials.credentials)
        if payload is None:
            return None
        
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = await auth_service.get_user_by_username(db, username)
        if user is None or not user.is_active:
            return None
        
        return user
    
    except Exception:
        return None
