"""
Tests for SpotType enum functionality and database compatibility
"""
import pytest
from app.models import Spot, SpotType, User, UserRole
from app.services.auth_service import get_password_hash


# Test data constants
TEST_LOCATION = "POINT(13.4050 52.5200)"  # Berlin coordinates in WKT format


def test_spot_type_enum_values():
    """Test that SpotType enum has correct values"""
    # Verify enum member names and values
    assert SpotType.STANDARD.name == "STANDARD"
    assert SpotType.STANDARD.value == "standard"
    
    assert SpotType.CHURCH.name == "CHURCH"
    assert SpotType.CHURCH.value == "church"
    
    assert SpotType.CASTLE.name == "CASTLE"
    assert SpotType.CASTLE.value == "castle"
    
    # Verify all enum members exist
    expected_types = [
        "STANDARD", "CHURCH", "SIGHT", "SPORTS_FACILITY", "PLAYGROUND",
        "MONUMENT", "MUSEUM", "CASTLE", "PARK", "VIEWPOINT",
        "HISTORIC", "CULTURAL", "RELIGIOUS", "TOWNHALL", "MARKET",
        "FOUNTAIN", "STATUE"
    ]
    
    actual_names = [e.name for e in SpotType]
    assert set(actual_names) == set(expected_types)


def test_create_spot_with_different_types(test_db):
    """Test creating spots with different SpotType values"""
    # Create a test user first
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password"),
        role=UserRole.TRAVELLER,
    )
    test_db.add(user)
    test_db.commit()
    
    # Test creating spots with various types
    test_cases = [
        (SpotType.STANDARD, "Standard Spot"),
        (SpotType.CHURCH, "Test Church"),
        (SpotType.CASTLE, "Test Castle"),
        (SpotType.MUSEUM, "Test Museum"),
    ]
    
    created_spots = []
    for spot_type, name in test_cases:
        spot = Spot(
            name=name,
            description=f"Test {name}",
            location=TEST_LOCATION,
            spot_type=spot_type,
            creator_id=user.id,
        )
        test_db.add(spot)
        test_db.commit()
        test_db.refresh(spot)
        created_spots.append(spot)
        
        # Verify the spot was created correctly
        assert spot.id is not None
        assert spot.spot_type == spot_type
        assert spot.name == name
    
    # Query back and verify
    for spot in created_spots:
        db_spot = test_db.query(Spot).filter(Spot.id == spot.id).first()
        assert db_spot is not None
        assert db_spot.spot_type == spot.spot_type


def test_query_spots_by_type(test_db):
    """Test querying spots by SpotType"""
    # Create a test user
    user = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password=get_password_hash("password"),
        role=UserRole.TRAVELLER,
    )
    test_db.add(user)
    test_db.commit()
    
    # Create multiple spots with different types
    spots_data = [
        ("Church 1", SpotType.CHURCH),
        ("Church 2", SpotType.CHURCH),
        ("Castle 1", SpotType.CASTLE),
        ("Standard 1", SpotType.STANDARD),
    ]
    
    for name, spot_type in spots_data:
        spot = Spot(
            name=name,
            location=TEST_LOCATION,
            spot_type=spot_type,
            creator_id=user.id,
        )
        test_db.add(spot)
    
    test_db.commit()
    
    # Query by specific types
    churches = test_db.query(Spot).filter(Spot.spot_type == SpotType.CHURCH).all()
    assert len(churches) == 2
    assert all(s.spot_type == SpotType.CHURCH for s in churches)
    
    castles = test_db.query(Spot).filter(Spot.spot_type == SpotType.CASTLE).all()
    assert len(castles) == 1
    assert castles[0].spot_type == SpotType.CASTLE
    
    standard = test_db.query(Spot).filter(Spot.spot_type == SpotType.STANDARD).all()
    assert len(standard) == 1
    assert standard[0].spot_type == SpotType.STANDARD


def test_spot_type_default_value(test_db):
    """Test that default spot_type is STANDARD"""
    user = User(
        username="testuser3",
        email="test3@example.com",
        hashed_password=get_password_hash("password"),
        role=UserRole.TRAVELLER,
    )
    test_db.add(user)
    test_db.commit()
    
    # Create spot without specifying spot_type
    spot = Spot(
        name="Default Spot",
        location=TEST_LOCATION,
        creator_id=user.id,
    )
    test_db.add(spot)
    test_db.commit()
    test_db.refresh(spot)
    
    # Verify default is STANDARD
    assert spot.spot_type == SpotType.STANDARD


def test_spot_type_serialization(test_db):
    """Test that SpotType serializes correctly"""
    user = User(
        username="testuser4",
        email="test4@example.com",
        hashed_password=get_password_hash("password"),
        role=UserRole.TRAVELLER,
    )
    test_db.add(user)
    test_db.commit()
    
    spot = Spot(
        name="Serialization Test",
        location=TEST_LOCATION,
        spot_type=SpotType.CHURCH,
        creator_id=user.id,
    )
    test_db.add(spot)
    test_db.commit()
    test_db.refresh(spot)
    
    # Verify the enum value
    assert isinstance(spot.spot_type, SpotType)
    assert spot.spot_type.value == "church"
    assert spot.spot_type.name == "CHURCH"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
