"""
Pydantic models for authentication and user management
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from database import UserRole

# Request models
class LoginRequest(BaseModel):
    username: str
    password: str

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: UserRole
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.replace('_', '').replace('.', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, dots, and underscores')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if not v.replace('_', '').replace('.', '').isalnum():
                raise ValueError('Username can only contain letters, numbers, dots, and underscores')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

# Response models
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    created_by: Optional[int]
    is_system_admin: bool = False
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Custom model validation to handle is_system_admin calculation"""
        if hasattr(obj, '__dict__'):
            data = obj.__dict__.copy()
        else:
            data = dict(obj)
        
        # Calculate is_system_admin based on created_by and role
        data['is_system_admin'] = (
            data.get('created_by') is None and 
            data.get('role') == UserRole.ADMIN
        )
        
        return super().model_validate(data, **kwargs)
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[UserResponse] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None

class UsersListResponse(BaseModel):
    success: bool
    users: List[UserResponse]
    total: int

class UserCreateResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None

class UserUpdateResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None

class MessageResponse(BaseModel):
    success: bool
    message: str