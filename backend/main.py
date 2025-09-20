from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager

from odoo_api import OdooAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Odoo API globally
odoo_api = OdooAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
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

# Authentication models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: str = None

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
async def login(request: LoginRequest):
    """Authenticate user with admin credentials"""
    try:
        # Get admin credentials from environment
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not admin_username or not admin_password:
            logger.error("Admin credentials not configured in environment")
            raise HTTPException(status_code=500, detail="Authentication not configured")
        
        # Check credentials
        if request.username == admin_username and request.password == admin_password:
            # Generate a simple token (in production, use JWT or similar)
            token = f"auth_token_{datetime.now().timestamp()}"
            
            logger.info(f"Successful login for user: {request.username}")
            return LoginResponse(
                success=True,
                message="Login successful",
                token=token
            )
        else:
            logger.warning(f"Failed login attempt for user: {request.username}")
            return LoginResponse(
                success=False,
                message="Invalid credentials"
            )
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/dashboard/forwarding-orders", response_model=DashboardResponse)
async def get_forwarding_orders_data():
    """1st Item: Get forwarding orders train departure data"""
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
async def get_first_mile_truck_data():
    """2nd Item: Get first mile truck orders data for NDP terminal"""
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
async def get_last_mile_truck_data(terminal: str):
    """3rd & 4th Item: Get last mile truck orders data for ICAD/DIC terminal"""
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
async def get_stockpile_data():
    """5th Item: Get stockpile utilization data"""
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
async def get_all_dashboard_data():
    """Get all dashboard data in one request"""
    try:
        data = {
            "forwarding_orders": odoo_api.get_forwarding_orders_train_data(),
            "first_mile_truck": odoo_api.get_first_mile_truck_data(),
            "last_mile_icad": odoo_api.get_last_mile_truck_data("ICAD"),
            "last_mile_dic": odoo_api.get_last_mile_truck_data("DIC"),
            "stockpiles": odoo_api.get_stockpile_utilization()
        }
        
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
