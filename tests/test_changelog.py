"""
Tests for the changelog endpoint
"""
import pytest
from fastapi import status
import os
from pathlib import Path


def test_changelog_endpoint_exists(client):
    """Test that the changelog endpoint exists and returns valid response"""
    response = client.get("/api/changelog")
    
    # Should return 200 or 404, not 500
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


def test_changelog_returns_list(client):
    """Test that changelog endpoint returns a list"""
    response = client.get("/api/changelog")
    
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        assert isinstance(data, list)
        
        # If there are entries, validate structure
        if len(data) > 0:
            entry = data[0]
            assert "date" in entry
            assert "title" in entry
            assert "description" in entry
            assert "highlights" in entry
            assert "files" in entry


def test_changelog_filters_pyc_files(client):
    """Test that changelog filters out .pyc files"""
    response = client.get("/api/changelog")
    
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        
        # Check that no entries contain only .pyc files
        for entry in data:
            files = entry.get("files", [])
            if files:
                # Should not have only .pyc files
                pyc_only = all(".pyc" in f or "__pycache__" in f for f in files)
                assert not pyc_only, f"Entry contains only .pyc files: {entry}"


def test_changelog_path_resolution():
    """Test that changelog path resolution logic works"""
    from app.routers.changelog import get_changelog_path
    
    # Should either find the file or raise FileNotFoundError
    try:
        path = get_changelog_path()
        assert isinstance(path, Path)
        assert path.exists()
        assert path.name == "CHANGELOG.md"
    except FileNotFoundError:
        # This is acceptable if CHANGELOG.md doesn't exist in test environment
        pass


def test_changelog_with_env_variable(client, monkeypatch, tmp_path):
    """Test changelog path resolution with environment variable"""
    # Create a temporary changelog file
    temp_changelog = tmp_path / "CHANGELOG.md"
    temp_changelog.write_text("""# Changelog

## 2025-12-13 Test Entry
**Highlights:**
- Test feature 1
- Test feature 2

**Modified:**
- `test_file.py`
""")
    
    # Set environment variable
    monkeypatch.setenv("CHANGELOG_PATH", str(temp_changelog))
    
    # Make a request
    response = client.get("/api/changelog")
    
    # Should work with custom path
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert data[0]["title"] == "Test Entry"


def test_changelog_parsing():
    """Test changelog parsing function"""
    from app.routers.changelog import parse_changelog
    
    test_content = """# Changelog

## 2025-12-13 Feature Release
**Highlights:**
- New feature added
- Bug fix implemented

**Modified:**
- `app/main.py`
- `app/models.py`

## 2025-12-12 22:00:00
**Modified:**
- `app/__pycache__/test.cpython-312.pyc`

## 2025-12-11 Update
**Modified:**
- `app/config.py`
"""
    
    entries = parse_changelog(test_content)
    
    # Should have 2 entries (pyc-only entry should be filtered)
    assert len(entries) == 2
    
    # First entry
    assert entries[0]["date"] == "2025-12-13"
    assert entries[0]["title"] == "Feature Release"
    assert len(entries[0]["highlights"]) == 2
    assert "app/main.py" in entries[0]["files"]
    assert ".pyc" not in str(entries[0]["files"])
    
    # Second entry (pyc-only entry should be skipped)
    assert entries[1]["date"] == "2025-12-11"
    assert entries[1]["title"] == "Update"
