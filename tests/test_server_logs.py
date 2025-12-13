"""
Tests for the server logs endpoint
"""
import pytest
from fastapi import status
import os
from pathlib import Path


def test_server_logs_endpoint_exists(client):
    """Test that the server logs endpoint exists and returns valid response"""
    response = client.get("/api/server-logs")
    
    # Should return 200, not 500
    assert response.status_code == status.HTTP_200_OK


def test_server_logs_returns_expected_structure(client):
    """Test that server logs endpoint returns expected structure"""
    response = client.get("/api/server-logs")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should have expected keys
    assert "logs" in data
    assert "line_count" in data
    assert "file_exists" in data
    
    # Types should be correct
    assert isinstance(data["logs"], str)
    assert isinstance(data["line_count"], int)
    assert isinstance(data["file_exists"], bool)


def test_server_logs_no_file(client):
    """Test server logs when file doesn't exist yet"""
    response = client.get("/api/server-logs")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # If file doesn't exist, should return empty logs
    if not data["file_exists"]:
        assert data["logs"] == ""
        assert data["line_count"] == 0


def test_server_logs_with_existing_file(client, tmp_path, monkeypatch):
    """Test server logs with an existing log file"""
    # Create a temporary log file
    temp_log = tmp_path / "client-debug.log"
    log_content = """[2025-12-13T10:00:00] [INFO] Test log entry 1
[2025-12-13T10:01:00] [INFO] Test log entry 2
[2025-12-13T10:02:00] [ERROR] Test error entry
[2025-12-13T10:03:00] [INFO] Test log entry 3
"""
    temp_log.write_text(log_content)
    
    # Set environment variable to point to our test log
    monkeypatch.setenv("SERVER_LOG_PATH", str(temp_log))
    
    # Make request
    response = client.get("/api/server-logs")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should have logs
    assert data["file_exists"] is True
    assert data["line_count"] == 4
    assert "Test log entry 1" in data["logs"]
    assert "Test error entry" in data["logs"]


def test_server_logs_tail_limit(client, tmp_path, monkeypatch):
    """Test that server logs respects max lines limit"""
    # Create a log file with many lines
    temp_log = tmp_path / "client-debug.log"
    
    # Create 250 lines (more than the 200 limit)
    lines = [f"[2025-12-13T10:00:00] [INFO] Log entry {i}" for i in range(250)]
    temp_log.write_text("\n".join(lines))
    
    # Set environment variable
    monkeypatch.setenv("SERVER_LOG_PATH", str(temp_log))
    
    # Make request
    response = client.get("/api/server-logs")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should only return last 200 lines
    assert data["line_count"] == 200
    
    # Should have the last line (249) but not the first lines
    assert "Log entry 249" in data["logs"]
    assert "Log entry 0" not in data["logs"]


def test_server_logs_path_resolution():
    """Test that server logs path resolution logic works"""
    from app.routers.server_logs import get_log_file_path
    
    # Should either find the file or raise FileNotFoundError
    try:
        path = get_log_file_path()
        assert isinstance(path, Path)
        assert path.exists()
        assert path.name == "client-debug.log"
    except FileNotFoundError:
        # This is acceptable if log file doesn't exist yet
        pass


def test_server_logs_empty_file(client, tmp_path, monkeypatch):
    """Test server logs with an empty log file"""
    # Create empty log file
    temp_log = tmp_path / "client-debug.log"
    temp_log.write_text("")
    
    # Set environment variable
    monkeypatch.setenv("SERVER_LOG_PATH", str(temp_log))
    
    # Make request
    response = client.get("/api/server-logs")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should handle empty file gracefully
    assert data["file_exists"] is True
    assert data["logs"] == ""
    assert data["line_count"] == 0


def test_server_logs_unicode_content(client, tmp_path, monkeypatch):
    """Test server logs with unicode characters"""
    # Create log file with unicode content
    temp_log = tmp_path / "client-debug.log"
    unicode_content = "[2025-12-13T10:00:00] [INFO] Unicode test: 你好世界 🌍 Ñoño\n"
    temp_log.write_text(unicode_content, encoding='utf-8')
    
    # Set environment variable
    monkeypatch.setenv("SERVER_LOG_PATH", str(temp_log))
    
    # Make request
    response = client.get("/api/server-logs")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should handle unicode correctly
    assert "你好世界" in data["logs"]
    assert "🌍" in data["logs"]
    assert "Ñoño" in data["logs"]
