"""
Configuration for spot types including XP/claim multipliers and icons.
"""
from app.models import SpotType

# XP and claim multipliers for each spot type
SPOT_TYPE_CONFIG = {
    SpotType.STANDARD: {
        "xp_multiplier": 1.0,
        "claim_multiplier": 1.0,
        "icon": "standard",
        "description": "Standard spot"
    },
    SpotType.CHURCH: {
        "xp_multiplier": 1.5,
        "claim_multiplier": 1.3,
        "icon": "church",
        "description": "Church (Kirche)"
    },
    SpotType.SIGHT: {
        "xp_multiplier": 2.0,
        "claim_multiplier": 1.5,
        "icon": "sight",
        "description": "Tourist sight (Sehenswürdigkeit)"
    },
    SpotType.SPORTS_FACILITY: {
        "xp_multiplier": 1.3,
        "claim_multiplier": 1.2,
        "icon": "sports",
        "description": "Sports facility (Sportstätte)"
    },
    SpotType.PLAYGROUND: {
        "xp_multiplier": 1.2,
        "claim_multiplier": 1.1,
        "icon": "playground",
        "description": "Playground (Spielplatz)"
    },
    SpotType.MONUMENT: {
        "xp_multiplier": 1.8,
        "claim_multiplier": 1.4,
        "icon": "monument",
        "description": "Monument"
    },
    SpotType.MUSEUM: {
        "xp_multiplier": 2.2,
        "claim_multiplier": 1.6,
        "icon": "museum",
        "description": "Museum"
    },
    SpotType.CASTLE: {
        "xp_multiplier": 2.5,
        "claim_multiplier": 2.0,
        "icon": "castle",
        "description": "Castle or palace (Schloss)"
    },
    SpotType.PARK: {
        "xp_multiplier": 1.2,
        "claim_multiplier": 1.1,
        "icon": "park",
        "description": "Park or garden"
    },
    SpotType.VIEWPOINT: {
        "xp_multiplier": 1.7,
        "claim_multiplier": 1.3,
        "icon": "viewpoint",
        "description": "Scenic viewpoint"
    },
    SpotType.HISTORIC: {
        "xp_multiplier": 1.9,
        "claim_multiplier": 1.5,
        "icon": "historic",
        "description": "Historic site"
    },
    SpotType.CULTURAL: {
        "xp_multiplier": 1.6,
        "claim_multiplier": 1.3,
        "icon": "cultural",
        "description": "Cultural center"
    },
    SpotType.RELIGIOUS: {
        "xp_multiplier": 1.4,
        "claim_multiplier": 1.2,
        "icon": "religious",
        "description": "Religious site"
    },
    SpotType.TOWNHALL: {
        "xp_multiplier": 1.5,
        "claim_multiplier": 1.3,
        "icon": "townhall",
        "description": "Town hall (Rathaus)"
    },
    SpotType.MARKET: {
        "xp_multiplier": 1.3,
        "claim_multiplier": 1.2,
        "icon": "market",
        "description": "Market (Markt)"
    },
    SpotType.FOUNTAIN: {
        "xp_multiplier": 1.2,
        "claim_multiplier": 1.1,
        "icon": "fountain",
        "description": "Fountain (Brunnen)"
    },
    SpotType.STATUE: {
        "xp_multiplier": 1.4,
        "claim_multiplier": 1.2,
        "icon": "statue",
        "description": "Statue or sculpture"
    },
}


def get_spot_config(spot_type: SpotType) -> dict:
    """Get configuration for a spot type"""
    return SPOT_TYPE_CONFIG.get(spot_type, SPOT_TYPE_CONFIG[SpotType.STANDARD])


def get_xp_multiplier(spot_type: SpotType) -> float:
    """Get XP multiplier for a spot type"""
    return get_spot_config(spot_type)["xp_multiplier"]


def get_claim_multiplier(spot_type: SpotType) -> float:
    """Get claim multiplier for a spot type"""
    return get_spot_config(spot_type)["claim_multiplier"]


def get_icon_name(spot_type: SpotType) -> str:
    """Get icon name for a spot type"""
    return get_spot_config(spot_type)["icon"]
