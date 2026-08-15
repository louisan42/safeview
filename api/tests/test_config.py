import os
import tempfile
import pytest
from unittest.mock import patch
from api.config import Settings


class TestConfig:
    """Test configuration loading and fallback mechanisms"""
    
    def test_config_defaults(self):
        """Test that configuration defaults are set correctly."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('api.config.Settings._fallback_pg_dsn_from_yaml', return_value=None):
                settings = Settings()
                assert settings.PG_DSN is None
                assert settings.cors_origin_list == ["http://localhost:3000", "http://localhost:5173"]

    def test_config_from_env(self):
        with patch.dict(os.environ, {
            'PG_DSN': 'postgresql://test:test@localhost/test',
            'CORS_ORIGINS': '["http://localhost:3000"]'
        }):
            settings = Settings()
            assert settings.PG_DSN == 'postgresql://test:test@localhost/test'
            assert settings.cors_origin_list == ["http://localhost:3000"]

    def test_database_url_alias(self):
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://from:env@localhost/dburl',
        }, clear=True):
            with patch('api.config.Settings._fallback_pg_dsn_from_yaml', return_value=None):
                settings = Settings()
                assert settings.PG_DSN == 'postgresql://from:env@localhost/dburl'

    def test_cors_origins_comma_separated(self):
        with patch.dict(os.environ, {
            'CORS_ORIGINS': 'http://localhost:5173,https://example.up.railway.app',
        }, clear=True):
            with patch('api.config.Settings._fallback_pg_dsn_from_yaml', return_value=None):
                settings = Settings()
                assert settings.cors_origin_list == [
                    'http://localhost:5173',
                    'https://example.up.railway.app',
                ]
    
    def test_yaml_fallback_mechanism(self):
        """Test YAML config fallback when PG_DSN not in env"""
        # Create a temporary YAML config file
        yaml_content = """
# Test config
pg_dsn: postgresql://yaml:yaml@localhost/yaml_db
other_setting: value
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            with patch.dict(os.environ, {}, clear=True):
                with patch('api.config.os.path.join', return_value=yaml_path):
                    with patch('api.config.os.path.exists', return_value=True):
                        settings = Settings()
                        assert settings.PG_DSN == 'postgresql://yaml:yaml@localhost/yaml_db'
        finally:
            os.unlink(yaml_path)
    
    def test_yaml_fallback_no_file(self):
        """Test YAML fallback when file doesn't exist"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('api.config.os.path.exists', return_value=False):
                settings = Settings()
                assert settings.PG_DSN is None
    
    def test_yaml_fallback_commented_line(self):
        """Test YAML fallback ignores commented lines"""
        yaml_content = """
# This is a comment
# pg_dsn: postgresql://commented:out@localhost/db
other_setting: value
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            with patch.dict(os.environ, {}, clear=True):
                with patch('api.config.os.path.join', return_value=yaml_path):
                    with patch('api.config.os.path.exists', return_value=True):
                        settings = Settings()
                        assert settings.PG_DSN is None
        finally:
            os.unlink(yaml_path)
    
    def test_yaml_fallback_exception_handling(self):
        """Test YAML fallback handles exceptions gracefully"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('api.config.os.path.join', side_effect=Exception("File error")):
                settings = Settings()
                assert settings.PG_DSN is None
