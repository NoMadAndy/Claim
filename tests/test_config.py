"""
Test configuration settings
"""
import os
import pytest


def test_settings_allow_extra_fields():
    """Test that Settings class allows and ignores extra environment variables"""
    # Set extra environment variables that aren't in the Settings model
    os.environ["DB_USER"] = "test_user"
    os.environ["DB_PASSWORD"] = "test_password"
    os.environ["DB_NAME"] = "test_db"
    os.environ["DB_PORT"] = "5432"
    os.environ["API_PORT"] = "8000"
    os.environ["CORS_ORIGINS"] = "*"
    
    # This should not raise a validation error in Pydantic v2
    from app.config import Settings
    
    try:
        settings = Settings()
        # Verify that defined fields still work
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'SECRET_KEY')
        # Verify that extra fields are not added to the model
        assert not hasattr(settings, 'DB_USER')
        assert not hasattr(settings, 'DB_PASSWORD')
    finally:
        # Clean up environment variables
        for key in ["DB_USER", "DB_PASSWORD", "DB_NAME", "DB_PORT", "API_PORT", "CORS_ORIGINS"]:
            os.environ.pop(key, None)


def test_settings_defined_fields_work():
    """Test that explicitly defined fields in Settings still work correctly"""
    # Set a defined field
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["TESTING"] = "true"
    
    from app.config import Settings
    
    try:
        settings = Settings()
        assert settings.DATABASE_URL == "sqlite:///test.db"
        assert settings.SECRET_KEY == "test-secret-key"
        assert settings.TESTING is True
    finally:
        # Clean up
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("SECRET_KEY", None)
        os.environ.pop("TESTING", None)


def test_settings_methods():
    """Test Settings helper methods"""
    from app.config import Settings
    
    # Test with SQLite URL
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    try:
        settings = Settings()
        assert settings.is_sqlite() is True
        assert settings.is_postgresql() is False
    finally:
        os.environ.pop("DATABASE_URL", None)
    
    # Test with PostgreSQL URL
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
    try:
        settings = Settings()
        assert settings.is_sqlite() is False
        assert settings.is_postgresql() is True
    finally:
        os.environ.pop("DATABASE_URL", None)
