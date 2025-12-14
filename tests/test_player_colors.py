"""Tests for player colors API endpoints"""
import pytest
from app.models import User, UserRole


def test_get_player_colors_authenticated(client, test_user, auth_headers):
    """Test that authenticated users can get player colors"""
    response = client.get("/api/admin/player-colors", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "players" in data
    assert len(data["players"]) >= 1


def test_get_player_colors_unauthenticated(client):
    """Test that unauthenticated users cannot get player colors"""
    response = client.get("/api/admin/player-colors")
    assert response.status_code == 401


def test_update_player_color_as_admin(client, test_db, test_user, test_admin, admin_headers):
    """Test that admin can update player colors"""
    response = client.put(
        f"/api/admin/player-colors/{test_user.id}",
        headers=admin_headers,
        json={"color": "#0000FF"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify the color was updated
    colors_response = client.get("/api/admin/player-colors", headers=admin_headers)
    players = colors_response.json()["players"]
    test_user_data = next(p for p in players if p["id"] == test_user.id)
    assert test_user_data["color"] == "#0000FF"


def test_update_player_color_as_regular_user(client, test_user, test_admin, auth_headers):
    """Test that regular users cannot update player colors"""
    response = client.put(
        f"/api/admin/player-colors/{test_admin.id}",
        headers=auth_headers,
        json={"color": "#0000FF"}
    )
    assert response.status_code == 403


def test_update_player_color_invalid_format(client, test_user, admin_headers):
    """Test that invalid color formats are rejected"""
    # Test with invalid hex color
    response = client.put(
        f"/api/admin/player-colors/{test_user.id}",
        headers=admin_headers,
        json={"color": "invalid"}
    )
    assert response.status_code == 400
    
    # Test with short hex color
    response = client.put(
        f"/api/admin/player-colors/{test_user.id}",
        headers=admin_headers,
        json={"color": "#FFF"}
    )
    assert response.status_code == 400


def test_update_nonexistent_user_color(client, admin_headers):
    """Test that updating color for nonexistent user returns 404"""
    response = client.put(
        "/api/admin/player-colors/99999",
        headers=admin_headers,
        json={"color": "#0000FF"}
    )
    assert response.status_code == 404
