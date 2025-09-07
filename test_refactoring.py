#!/usr/bin/env python3
"""
Simple test script to verify the incidents router refactoring works correctly.
Tests the helper functions and basic functionality without requiring pytest.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from routers.incidents import (
    _parse_dt, 
    _build_where_clause_and_params, 
    _parse_bbox, 
    _get_order_clause,
    _format_geojson_response
)
from datetime import datetime

def test_parse_dt():
    """Test date parsing function."""
    print("Testing _parse_dt...")
    
    # Test None and empty
    assert _parse_dt(None) is None
    assert _parse_dt("") is None
    assert _parse_dt("   ") is None
    
    # Test date formats
    dt = _parse_dt("2025-01-01")
    assert dt.year == 2025 and dt.month == 1 and dt.day == 1
    
    # Test datetime with Z
    dt = _parse_dt("2025-01-01T12:30:00Z")
    assert dt.year == 2025 and dt.hour == 12
    
    print("✅ _parse_dt tests passed")

def test_parse_bbox():
    """Test bbox parsing function."""
    print("Testing _parse_bbox...")
    
    # Valid bbox
    sql, params = _parse_bbox("-79.6,43.6,-79.3,43.8")
    assert "ST_Intersects" in sql
    assert len(params) == 4
    assert params == [-79.6, 43.6, -79.3, 43.8]
    
    # Test error cases
    try:
        _parse_bbox("invalid")
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert "bbox must be" in str(e)
    
    print("✅ _parse_bbox tests passed")

def test_get_order_clause():
    """Test order clause generation."""
    print("Testing _get_order_clause...")
    
    # Default case
    order = _get_order_clause(None, None)
    assert "report_date DESC" in order
    
    # Custom sort
    order = _get_order_clause("id", "asc")
    assert "id ASC" in order
    
    # Invalid field should default to report_date
    order = _get_order_clause("invalid_field", "desc")
    assert "report_date DESC" in order
    
    print("✅ _get_order_clause tests passed")

def test_build_where_clause():
    """Test WHERE clause building."""
    print("Testing _build_where_clause_and_params...")
    
    # No filters
    where, params = _build_where_clause_and_params(
        None, None, None, None, None, None, None, None
    )
    assert where == "1=1"
    assert params == []
    
    # With dataset filter
    where, params = _build_where_clause_and_params(
        "robbery", None, None, None, None, None, None, None
    )
    assert "dataset = %s" in where
    assert "robbery" in params
    
    # With date range
    where, params = _build_where_clause_and_params(
        None, "2025-01-01", "2025-01-31", None, None, None, None, None
    )
    assert "report_date >=" in where
    assert "report_date <=" in where
    assert len(params) == 2
    
    print("✅ _build_where_clause_and_params tests passed")

def test_format_geojson_response():
    """Test GeoJSON response formatting."""
    print("Testing _format_geojson_response...")
    
    # Empty response
    result = _format_geojson_response([], 0)
    assert result["type"] == "FeatureCollection"
    assert result["features"] == []
    assert result["total"] == 0
    
    # With data
    rows = [
        {
            "id": 1,
            "dataset": "test",
            "geometry": {"type": "Point", "coordinates": [-79.4, 43.7]},
            "lon": -79.4,
            "lat": 43.7
        }
    ]
    result = _format_geojson_response(rows, 1)
    assert len(result["features"]) == 1
    assert result["features"][0]["type"] == "Feature"
    assert result["features"][0]["properties"]["id"] == 1
    
    print("✅ _format_geojson_response tests passed")

def main():
    """Run all tests."""
    print("🧪 Testing SafetyView incidents router refactoring...")
    print()
    
    try:
        test_parse_dt()
        test_parse_bbox()
        test_get_order_clause()
        test_build_where_clause()
        test_format_geojson_response()
        
        print()
        print("🎉 All tests passed! The refactoring is working correctly.")
        print("✅ Cognitive complexity has been reduced by extracting helper functions.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
