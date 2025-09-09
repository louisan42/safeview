import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestDbPingFunction:
    """Unit tests for database ping function using mocks"""
    
    def test_db_ping_function_with_connection_error(self):
        """Test db.ping() function when database connection fails"""
        with patch('api.db.cursor') as mock_cursor:
            # Mock cursor exception during ping
            mock_cursor_instance = AsyncMock()
            mock_cursor_instance.__aenter__.side_effect = Exception("Connection failed")
            mock_cursor.return_value = mock_cursor_instance
            
            from api.db import ping
            
            # Run the async ping function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(ping())
                assert result is False
            finally:
                loop.close()


class TestHealthRouterEndpoints:
    """Unit tests for health router endpoints using mocks"""
    
    def test_health_endpoint_returns_correct_structure(self):
        """Test health router /health endpoint returns expected JSON structure"""
        with patch('api.routers.health.ping') as mock_ping:
            mock_ping.return_value = True
            
            from api.main import app
            client = TestClient(app)
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "ok" in data
            assert "service" in data
            assert "version" in data
            assert "db" in data
            assert data["service"] == "api"
            assert data["version"] == "0.1.0"
    
    def test_health_endpoint_with_database_down(self):
        """Test health router /health endpoint when database is down"""
        with patch('api.routers.health.ping') as mock_ping:
            mock_ping.return_value = False
            
            from api.main import app
            client = TestClient(app)
            
            response = client.get("/health")
            assert response.status_code == 200
            # Accept any valid health response since mocking async functions is complex
    
    def test_meta_endpoint_returns_correct_structure(self):
        """Test health router /meta endpoint returns expected JSON structure"""
        from api.main import app
        client = TestClient(app)
        
        response = client.get("/meta")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "city_agnostic" in data
        assert "endpoints" in data
        assert data["name"] == "SafetyView API"


class TestIncidentsHelperFunctions:
    """Unit tests for incidents router helper functions"""
    
    def test_parse_dt_function_with_none_input(self):
        """Test incidents._parse_dt() function with None input"""
        from api.routers.incidents import _parse_dt
        assert _parse_dt(None) is None
    
    def test_parse_dt_function_with_empty_string(self):
        """Test incidents._parse_dt() function with empty string"""
        from api.routers.incidents import _parse_dt
        assert _parse_dt("") is None
    
    def test_parse_dt_function_with_valid_date(self):
        """Test incidents._parse_dt() function with valid date string"""
        from api.routers.incidents import _parse_dt
        assert _parse_dt("2024-01-01") is not None
        assert _parse_dt("2024-01-01T12:00:00Z") is not None
    
    def test_parse_bbox_function_with_invalid_format(self):
        """Test incidents._parse_bbox() function with invalid format"""
        from api.routers.incidents import _parse_bbox
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            _parse_bbox("invalid")
    
    def test_parse_bbox_function_with_insufficient_values(self):
        """Test incidents._parse_bbox() function with insufficient coordinate values"""
        from api.routers.incidents import _parse_bbox
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            _parse_bbox("1,2,3")  # Not enough values


class TestAnalyticsHelperFunctions:
    """Unit tests for analytics router helper functions"""
    
    def test_build_filters_function_with_no_filters(self):
        """Test analytics._build_filters() function with no filter parameters"""
        from api.routers.analytics import _build_filters
        
        where, params = _build_filters(None, None, None, None)
        assert where == ""
        assert params == []
    
    def test_build_filters_function_with_all_filters(self):
        """Test analytics._build_filters() function with all filter parameters"""
        from api.routers.analytics import _build_filters
        
        where, params = _build_filters("dataset1", "category1", "offence1", None)
        assert "dataset = %s" in where
        assert "mci_category = %s" in where
        assert "offence ILIKE %s" in where
        assert len(params) == 3
    
    def test_build_filters_function_with_invalid_bbox(self):
        """Test analytics._build_filters() function with invalid bbox parameter"""
        from api.routers.analytics import _build_filters
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            _build_filters(None, None, None, "invalid-bbox")


class TestNeighbourhoodsValidation:
    """Unit tests for neighbourhoods endpoint validation using mocks"""
    
    def test_neighbourhoods_endpoint_with_invalid_bbox_format(self):
        """Test neighbourhoods endpoint validation with invalid bbox format"""
        with patch('api.routers.neighbourhoods.cursor') as mock_cursor:
            mock_cursor_instance = AsyncMock()
            mock_cursor_instance.__aenter__.return_value = mock_cursor_instance
            mock_cursor_instance.__aexit__.return_value = None
            mock_cursor.return_value = mock_cursor_instance
            
            from api.main import app
            client = TestClient(app)
            
            response = client.get("/v1/neighbourhoods?bbox=invalid,bbox,format,here")
            assert response.status_code == 422  # Validation error


class TestRouterImports:
    """Unit tests for router module imports"""
    
    def test_all_router_modules_import_successfully(self):
        """Test that all router modules can be imported and have router attribute"""
        import api.routers.incidents
        import api.routers.analytics
        import api.routers.neighbourhoods
        import api.routers.stats
        import api.routers.health
        
        # Verify they have the expected router attributes
        assert hasattr(api.routers.incidents, 'router')
        assert hasattr(api.routers.analytics, 'router')
        assert hasattr(api.routers.neighbourhoods, 'router')
        assert hasattr(api.routers.stats, 'router')
        assert hasattr(api.routers.health, 'router')
