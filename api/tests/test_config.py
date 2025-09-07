import os
import tempfile
import pytest
from unittest.mock import patch
from api.config import Settings


class TestConfig:
    """Test configuration loading and fallback mechanisms"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('api.config.Settings._fallback_pg_dsn_from_yaml', return_value=None):
                settings = Settings()
                assert settings.CORS_ORIGINS == ["*"]
                assert settings.PG_DSN is None
    
    def test_config_from_env(self):
        """Test configuration from environment variables"""
        with patch.dict(os.environ, {
            'PG_DSN': 'postgresql://test:test@localhost/test',
            'CORS_ORIGINS': '["http://localhost:3000"]'
        }):
            settings = Settings()
            assert settings.PG_DSN == 'postgresql://test:test@localhost/test'
    
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
            # Mock the config path to point to our temp file
            with patch('api.config.os.path.join', return_value=yaml_path):
                with patch('api.config.os.path.exists', return_value=True):
                    settings = Settings()
                    assert settings.PG_DSN == 'postgresql://yaml:yaml@localhost/yaml_db'
        finally:
            os.unlink(yaml_path)
    
    def test_yaml_fallback_no_file(self):
        """Test YAML fallback when file doesn't exist"""
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
            with patch('api.config.os.path.join', return_value=yaml_path):
                with patch('api.config.os.path.exists', return_value=True):
                    settings = Settings()
                    assert settings.PG_DSN is None
        finally:
            os.unlink(yaml_path)
    
    def test_yaml_fallback_exception_handling(self):
        """Test YAML fallback handles exceptions gracefully"""
        with patch('api.config.os.path.join', side_effect=Exception("File error")):
            settings = Settings()
            assert settings.PG_DSN is None
