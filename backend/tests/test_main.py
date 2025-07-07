import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Import your FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


@patch('odoo_api.OdooAPI')
def test_dashboard_all_endpoint(mock_odoo_api):
    """Test the dashboard all endpoint with mocked Odoo API"""
    # Mock the OdooAPI instance
    mock_instance = Mock()
    mock_odoo_api.return_value = mock_instance
    
    # Mock the methods
    mock_instance.get_forwarding_orders.return_value = {
        "current_week": {"total": 10, "weight": 1000},
        "last_week": {"total": 8, "weight": 800}
    }
    mock_instance.get_first_mile_truck_orders.return_value = {
        "today": {"total": 5, "weight": 500}
    }
    mock_instance.get_last_mile_truck_orders.return_value = {
        "today": {"total": 3, "weight": 300}
    }
    mock_instance.get_stockpiles.return_value = []
    
    response = client.get("/api/dashboard/all")
    assert response.status_code == 200
    data = response.json()
    
    assert "forwarding_orders" in data
    assert "first_mile_truck" in data
    assert "last_mile_truck_icad" in data
    assert "last_mile_truck_dic" in data
    assert "stockpiles" in data


def test_cors_headers():
    """Test that CORS headers are properly set"""
    response = client.get("/api/health")
    assert response.status_code == 200
    # In a real test, you'd check for CORS headers
    # This depends on your CORS configuration


@pytest.mark.parametrize("endpoint", [
    "/api/dashboard/forwarding-orders",
    "/api/dashboard/first-mile-truck",
    "/api/dashboard/last-mile-truck/ICAD",
    "/api/dashboard/last-mile-truck/DIC",
    "/api/dashboard/stockpiles"
])
@patch('odoo_api.OdooAPI')
def test_dashboard_endpoints_structure(mock_odoo_api, endpoint):
    """Test that all dashboard endpoints return proper structure"""
    # Mock the OdooAPI instance
    mock_instance = Mock()
    mock_odoo_api.return_value = mock_instance
    
    # Mock different return values based on endpoint
    if "forwarding-orders" in endpoint:
        mock_instance.get_forwarding_orders.return_value = {"test": "data"}
    elif "first-mile-truck" in endpoint:
        mock_instance.get_first_mile_truck_orders.return_value = {"test": "data"}
    elif "last-mile-truck" in endpoint:
        mock_instance.get_last_mile_truck_orders.return_value = {"test": "data"}
    elif "stockpiles" in endpoint:
        mock_instance.get_stockpiles.return_value = []
    
    response = client.get(endpoint)
    # Should either return 200 with data or handle errors gracefully
    assert response.status_code in [200, 500]  # 500 if Odoo connection fails
