from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import os
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from odoo_api import OdooAPI
from database import get_db, init_db, User, UserRole
from auth_service import AuthService
from auth_models import (
    LoginRequest, LoginResponse, CreateUserRequest, UpdateUserRequest,
    ChangePasswordRequest, UserResponse, UsersListResponse, 
    UserCreateResponse, UserUpdateResponse, MessageResponse
)
from auth_dependencies import (
    get_current_user, get_current_active_user, require_admin, 
    require_operator, require_executive, require_visitor
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Odoo API globally
odoo_api = OdooAPI()

# Initialize Auth Service
auth_service = AuthService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # Initialize database and create admin user
        await init_db()
        
        if odoo_api.authenticate():
            logger.info("Successfully connected to Odoo")
        else:
            logger.error("Failed to connect to Odoo")
    except Exception as e:
        logger.error(f"Startup error: {e}")
    
    yield
    
    # Shutdown (if needed)
    logger.info("Application shutdown")

app = FastAPI(title="Terminal Dashboard API", version="1.0.0", lifespan=lifespan)

# Remove old authentication models since they're now in auth_models.py

# Manual CORS handling for debugging
@app.middleware("http")
async def cors_handler(request: Request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    
    # Always add CORS headers for debugging
    response.headers["Access-Control-Allow-Origin"] = origin or "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# Handle preflight requests
@app.options("/{path:path}")
async def handle_options(path: str):
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Configure CORS - Allow both localhost and network access
allowed_origins = [
    "http://localhost:3003",
    "http://localhost:5173",
    "http://127.0.0.1:3003",
    "http://127.0.0.1:5173",
    "http://172.16.229.75:3003",
    "https://etihad-rail-dashboard.linus.services"
]

# Add network origins if running in network mode
network_mode = os.getenv("NETWORK_MODE", "false").lower() == "true"
allow_credentials = True

if network_mode:
    # Allow all origins when in network mode
    allowed_origins = ["*"]
    allow_credentials = False  # Can't use credentials with wildcard origins

print(f"🔧 CORS Configuration:")
print(f"   Network Mode: {network_mode}")
print(f"   Allowed Origins: {allowed_origins}")
print(f"   Allow Credentials: {allow_credentials}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Odoo API (moved to top of file)
# odoo_api = OdooAPI()  # Already initialized globally above

class DashboardResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    timestamp: str

@app.get("/")
async def root():
    return {"message": "Terminal Dashboard API", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Odoo connection
        odoo_connected = odoo_api.test_connection()
        return {
            "status": "healthy",
            "odoo_connected": odoo_connected,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user with username/password"""
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(db, request.username, request.password)
        
        if not user:
            logger.warning(f"Failed login attempt for user: {request.username}")
            return LoginResponse(
                success=False,
                message="Invalid credentials"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.username, "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Successful login for user: {request.username}")
        return LoginResponse(
            success=True,
            message="Login successful",
            token=access_token,
            user=UserResponse.model_validate(user)
        )
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# User Management Endpoints (Admin only)
@app.post("/api/auth/users", response_model=UserCreateResponse)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (Admin only)"""
    try:
        # Check if username already exists
        existing_user = await auth_service.get_user_by_username(db, request.username)
        if existing_user:
            return UserCreateResponse(
                success=False,
                message="Username already exists"
            )
        
        # Check if email already exists
        existing_email = await auth_service.get_user_by_email(db, request.email)
        if existing_email:
            return UserCreateResponse(
                success=False,
                message="Email already exists"
            )
        
        # Create user
        new_user = await auth_service.create_user(
            db=db,
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            password=request.password,
            role=request.role,
            created_by=current_user.id
        )
        
        logger.info(f"User created: {request.username} by admin: {current_user.username}")
        return UserCreateResponse(
            success=True,
            message="User created successfully",
            user=UserResponse.model_validate(new_user)
        )
    
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/auth/users", response_model=UsersListResponse)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (Admin only)"""
    try:
        users = await auth_service.get_all_users(db, skip=skip, limit=limit)
        return UsersListResponse(
            success=True,
            users=[UserResponse.model_validate(user) for user in users],
            total=len(users)
        )
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/auth/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (Admin only)"""
    try:
        user = await auth_service.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/auth/users/{user_id}", response_model=UserUpdateResponse)
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user (Admin only)"""
    try:
        # Check if user exists
        user = await auth_service.get_user_by_id(db, user_id)
        if not user:
            return UserUpdateResponse(
                success=False,
                message="User not found"
            )
        
        # Prevent editing system admin username and password
        is_system_admin = user.created_by is None and user.role == UserRole.ADMIN
        if is_system_admin:
            if request.username and request.username != user.username:
                return UserUpdateResponse(
                    success=False,
                    message="Cannot change system administrator username (set via environment)"
                )
            if request.password:
                return UserUpdateResponse(
                    success=False,
                    message="Cannot change system administrator password (set via environment)"
                )
        
        # Check for username conflicts
        if request.username and request.username != user.username:
            existing_user = await auth_service.get_user_by_username(db, request.username)
            if existing_user:
                return UserUpdateResponse(
                    success=False,
                    message="Username already exists"
                )
        
        # Check for email conflicts
        if request.email and request.email != user.email:
            existing_email = await auth_service.get_user_by_email(db, request.email)
            if existing_email:
                return UserUpdateResponse(
                    success=False,
                    message="Email already exists"
                )
        
        # Update user
        updated_user = await auth_service.update_user(
            db=db,
            user_id=user_id,
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            password=request.password,
            role=request.role,
            is_active=request.is_active
        )
        
        logger.info(f"User updated: {user.username} by admin: {current_user.username}")
        return UserUpdateResponse(
            success=True,
            message="User updated successfully",
            user=UserResponse.model_validate(updated_user)
        )
    
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/auth/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (Admin only)"""
    try:
        # Check if user exists
        user = await auth_service.get_user_by_id(db, user_id)
        if not user:
            return MessageResponse(
                success=False,
                message="User not found"
            )
        
        # Prevent deleting yourself
        if user_id == current_user.id:
            return MessageResponse(
                success=False,
                message="Cannot delete yourself"
            )
        
        # Prevent deleting system administrator
        is_system_admin = user.created_by is None and user.role == UserRole.ADMIN
        if is_system_admin:
            return MessageResponse(
                success=False,
                message="Cannot delete system administrator (created via environment)"
            )
            return MessageResponse(
                success=False,
                message="Cannot delete your own account"
            )
        
        # Delete user (soft delete)
        await auth_service.delete_user(db, user_id)
        
        logger.info(f"User deleted: {user.username} by admin: {current_user.username}")
        return MessageResponse(
            success=True,
            message="User deleted successfully"
        )
    
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# User Profile Endpoints
@app.get("/api/auth/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserResponse.model_validate(current_user)

@app.post("/api/auth/refresh-token", response_model=LoginResponse)
async def refresh_token(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Refresh the current user's token"""
    try:
        # Create a new access token
        access_token_expires = timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": current_user.username, "role": current_user.role.value},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Token refreshed for user: {current_user.username}")
        return LoginResponse(
            success=True,
            message="Token refreshed successfully",
            token=access_token,
            user=UserResponse.model_validate(current_user)
        )
    
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password"""
    try:
        # Verify current password
        if not auth_service.verify_password(request.current_password, current_user.hashed_password):
            return MessageResponse(
                success=False,
                message="Current password is incorrect"
            )
        
        # Update password
        await auth_service.update_user(
            db=db,
            user_id=current_user.id,
            password=request.new_password
        )
        
        logger.info(f"Password changed for user: {current_user.username}")
        return MessageResponse(
            success=True,
            message="Password changed successfully"
        )
    
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/dashboard/forwarding-orders", response_model=DashboardResponse)
async def get_forwarding_orders_data(current_user: User = Depends(require_visitor)):
    """1st Item: Get forwarding orders train departure data (Requires at least Visitor role)"""
    try:
        data = odoo_api.get_forwarding_orders_train_data()
        return DashboardResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error fetching forwarding orders data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/first-mile-truck", response_model=DashboardResponse)
async def get_first_mile_truck_data(current_user: User = Depends(require_visitor)):
    """2nd Item: Get first mile truck orders data for NDP terminal (Requires at least Visitor role)"""
    try:
        data = odoo_api.get_first_mile_truck_data()
        return DashboardResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error fetching first mile truck data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/last-mile-truck/{terminal}", response_model=DashboardResponse)
async def get_last_mile_truck_data(terminal: str, current_user: User = Depends(require_visitor)):
    """3rd & 4th Item: Get last mile truck orders data for ICAD/DIC terminal (Requires at least Visitor role)"""
    if terminal not in ['ICAD', 'DIC']:
        raise HTTPException(status_code=400, detail="Terminal must be ICAD or DIC")
    
    try:
        data = odoo_api.get_last_mile_truck_data(terminal)
        return DashboardResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error fetching last mile truck data for {terminal}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stockpiles", response_model=DashboardResponse)
async def get_stockpile_data(current_user: User = Depends(require_executive)):
    """5th Item: Get stockpile utilization data (Requires at least Executive role)"""
    try:
        data = odoo_api.get_stockpile_utilization()
        return DashboardResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error fetching stockpile data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/all")
async def get_all_dashboard_data(current_user: User = Depends(require_visitor)):
    """Get all dashboard data in one request (Requires at least Visitor role)"""
    try:
        data = {
            "forwarding_orders": odoo_api.get_forwarding_orders_train_data(),
            "first_mile_truck": odoo_api.get_first_mile_truck_data(),
            "last_mile_icad": odoo_api.get_last_mile_truck_data("ICAD"),
            "last_mile_dic": odoo_api.get_last_mile_truck_data("DIC"),
        }
        
        # Add stockpiles data only if user has executive+ role
        if auth_service.has_permission(current_user.role, UserRole.EXECUTIVE):
            data["stockpiles"] = odoo_api.get_stockpile_utilization()
        
        return DashboardResponse(
            success=True,
            data=data,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error fetching all dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cors-test")
async def cors_test():
    """Simple endpoint to test CORS configuration"""
    return {
        "message": "CORS test successful",
        "timestamp": datetime.now().isoformat(),
        "network_mode": os.getenv("NETWORK_MODE", "false")
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
