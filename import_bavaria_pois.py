#!/usr/bin/env python3
"""
Import Points of Interest (POIs) from OpenStreetMap for Bavaria, Germany.
This script queries the Overpass API and creates spots in the database.

Usage:
    python import_bavaria_pois.py [--limit N] [--test]
    
Options:
    --limit N   Limit the number of POIs imported per category (for testing)
    --test      Dry run - don't actually insert into database
"""

import asyncio
import sys
import argparse
from typing import List, Dict, Any, Optional
import httpx
from app.database import SessionLocal
from app.models import Spot, SpotType
from app.spot_types_config import get_spot_config
from geoalchemy2.elements import WKTElement
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bavaria bounding box (approximate): [south, west, north, east]
# Bavaria: latitude 47.27 to 50.56, longitude 8.98 to 13.84
BAVARIA_BBOX = "47.27,8.98,50.56,13.84"

# Overpass API endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Mapping of OSM tags to our SpotType
OSM_TO_SPOT_TYPE = {
    # Churches and religious buildings
    "amenity=place_of_worship": SpotType.CHURCH,
    "building=church": SpotType.CHURCH,
    "building=cathedral": SpotType.CHURCH,
    "building=chapel": SpotType.RELIGIOUS,
    "building=monastery": SpotType.RELIGIOUS,
    "amenity=monastery": SpotType.RELIGIOUS,
    
    # Tourist attractions and sights
    "tourism=attraction": SpotType.SIGHT,
    "tourism=viewpoint": SpotType.VIEWPOINT,
    "historic=monument": SpotType.MONUMENT,
    "historic=memorial": SpotType.MONUMENT,
    "historic=castle": SpotType.CASTLE,
    "historic=manor": SpotType.HISTORIC,
    "historic=ruins": SpotType.HISTORIC,
    "historic=archaeological_site": SpotType.HISTORIC,
    
    # Museums
    "tourism=museum": SpotType.MUSEUM,
    "tourism=gallery": SpotType.CULTURAL,
    
    # Parks and gardens
    "leisure=park": SpotType.PARK,
    "leisure=garden": SpotType.PARK,
    "tourism=theme_park": SpotType.PARK,
    
    # Sports facilities
    "leisure=sports_centre": SpotType.SPORTS_FACILITY,
    "leisure=stadium": SpotType.SPORTS_FACILITY,
    "leisure=pitch": SpotType.SPORTS_FACILITY,
    "sport=*": SpotType.SPORTS_FACILITY,
    
    # Playgrounds
    "leisure=playground": SpotType.PLAYGROUND,
    
    # Town halls
    "amenity=townhall": SpotType.TOWNHALL,
    
    # Markets
    "amenity=marketplace": SpotType.MARKET,
    
    # Fountains
    "amenity=fountain": SpotType.FOUNTAIN,
    
    # Statues and artwork
    "tourism=artwork": SpotType.STATUE,
    "historic=wayside_cross": SpotType.STATUE,
}


def build_overpass_query(spot_type_mapping: Dict[str, SpotType], bbox: str, limit: Optional[int] = None) -> str:
    """Build an Overpass API query for multiple POI types"""
    # Create query parts for each OSM tag
    query_parts = []
    
    for osm_tag in spot_type_mapping.keys():
        if "=" in osm_tag:
            key, value = osm_tag.split("=", 1)
            if value == "*":
                # Any value for this key
                query_parts.append(f'node["{key}"]({bbox});')
                query_parts.append(f'way["{key}"]({bbox});')
            else:
                query_parts.append(f'node["{key}"="{value}"]({bbox});')
                query_parts.append(f'way["{key}"="{value}"]({bbox});')
    
    # Combine into full query
    query = f"""
    [out:json][timeout:180];
    (
        {chr(10).join(query_parts)}
    );
    out center body;
    """
    
    return query


async def fetch_pois_from_overpass(query: str) -> List[Dict[str, Any]]:
    """Fetch POIs from Overpass API"""
    logger.info("Querying Overpass API for Bavaria POIs...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            data = response.json()
            
            elements = data.get("elements", [])
            logger.info(f"Received {len(elements)} POIs from Overpass API")
            return elements
            
        except httpx.HTTPError as e:
            logger.error(f"Error fetching from Overpass API: {e}")
            return []


def determine_spot_type(tags: Dict[str, str]) -> Optional[SpotType]:
    """Determine SpotType from OSM tags"""
    # Check specific tag combinations first
    for osm_pattern, spot_type in OSM_TO_SPOT_TYPE.items():
        if "=" in osm_pattern:
            key, value = osm_pattern.split("=", 1)
            if value == "*":
                # Any value for this key
                if key in tags:
                    return spot_type
            else:
                if tags.get(key) == value:
                    return spot_type
    
    return None


def extract_poi_data(element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract relevant data from OSM element"""
    tags = element.get("tags", {})
    
    # Determine spot type
    spot_type = determine_spot_type(tags)
    if not spot_type:
        return None
    
    # Get coordinates
    if element["type"] == "node":
        lat = element.get("lat")
        lon = element.get("lon")
    elif element["type"] == "way":
        # Use center for ways
        center = element.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")
    else:
        return None
    
    if not lat or not lon:
        return None
    
    # Get name (try different name tags)
    name = tags.get("name") or tags.get("name:de") or tags.get("official_name") or "Unnamed POI"
    
    # Get description from various tags
    description_parts = []
    if tags.get("description"):
        description_parts.append(tags["description"])
    if tags.get("historic"):
        description_parts.append(f"Historic: {tags['historic']}")
    if tags.get("tourism"):
        description_parts.append(f"Tourism: {tags['tourism']}")
    if tags.get("building"):
        description_parts.append(f"Building: {tags['building']}")
    
    description = " | ".join(description_parts) if description_parts else None
    
    # Get config for this spot type
    config = get_spot_config(spot_type)
    
    return {
        "name": name,
        "description": description,
        "latitude": lat,
        "longitude": lon,
        "spot_type": spot_type,
        "xp_multiplier": config["xp_multiplier"],
        "claim_multiplier": config["claim_multiplier"],
        "icon_name": config["icon"],
        "osm_id": element.get("id"),
        "osm_tags": tags
    }


def import_pois_to_database(pois: List[Dict[str, Any]], db, test_mode: bool = False) -> int:
    """Import POIs into the database"""
    imported_count = 0
    skipped_count = 0
    
    logger.info(f"Importing {len(pois)} POIs to database (test_mode={test_mode})...")
    
    for poi_data in pois:
        try:
            # Check if spot already exists at this location (within 10 meters)
            # This is a simple check - in production you might want more sophisticated deduplication
            point = f'POINT({poi_data["longitude"]} {poi_data["latitude"]})'
            
            # Create spot
            if not test_mode:
                spot = Spot(
                    name=poi_data["name"],
                    description=poi_data.get("description"),
                    location=WKTElement(point, srid=4326),
                    is_permanent=True,
                    is_loot=False,
                    spot_type=poi_data["spot_type"],
                    xp_multiplier=poi_data["xp_multiplier"],
                    claim_multiplier=poi_data["claim_multiplier"],
                    icon_name=poi_data["icon_name"],
                    creator_id=None  # System-created spot
                )
                db.add(spot)
            
            imported_count += 1
            
            if imported_count % 100 == 0:
                logger.info(f"Imported {imported_count} POIs...")
                if not test_mode:
                    db.commit()
            
        except Exception as e:
            logger.error(f"Error importing POI {poi_data.get('name')}: {e}")
            skipped_count += 1
    
    if not test_mode:
        db.commit()
    
    logger.info(f"Import complete: {imported_count} imported, {skipped_count} skipped")
    return imported_count


async def main():
    parser = argparse.ArgumentParser(description="Import Bavaria POIs from OpenStreetMap")
    parser.add_argument("--limit", type=int, help="Limit number of POIs per category (for testing)")
    parser.add_argument("--test", action="store_true", help="Dry run - don't actually insert into database")
    parser.add_argument("--category", choices=["church", "sight", "sports", "playground", "all"], 
                       default="all", help="Import only specific category")
    
    args = parser.parse_args()
    
    # Build query
    query = build_overpass_query(OSM_TO_SPOT_TYPE, BAVARIA_BBOX, args.limit)
    
    # Fetch POIs
    elements = await fetch_pois_from_overpass(query)
    
    if not elements:
        logger.warning("No POIs fetched from Overpass API")
        return
    
    # Extract and filter POI data
    pois = []
    for element in elements:
        poi_data = extract_poi_data(element)
        if poi_data:
            pois.append(poi_data)
    
    logger.info(f"Extracted {len(pois)} valid POIs from {len(elements)} elements")
    
    # Group by type for statistics
    type_counts = {}
    for poi in pois:
        spot_type = poi["spot_type"]
        type_counts[spot_type] = type_counts.get(spot_type, 0) + 1
    
    logger.info("POI counts by type:")
    for spot_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {spot_type.value}: {count}")
    
    # Import to database
    if not args.test:
        db = SessionLocal()
        try:
            imported = import_pois_to_database(pois, db, test_mode=False)
            logger.info(f"Successfully imported {imported} POIs to database")
        finally:
            db.close()
    else:
        logger.info("Test mode - no database changes made")
        logger.info(f"Would import {len(pois)} POIs")


if __name__ == "__main__":
    asyncio.run(main())
