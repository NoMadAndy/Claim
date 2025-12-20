#!/usr/bin/env python3
"""
Example usage of the spot type system and Bavaria POI import.
This script demonstrates:
1. Running the database migration
2. Testing the import (dry run)
3. Importing a limited set of POIs
4. Querying spots by type
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def main():
    print("=" * 60)
    print("Claim - Bavaria POI Import Example")
    print("=" * 60)
    print()
    
    # Step 1: Database Migration
    print("Step 1: Database Migration")
    print("-" * 60)
    print("To add spot type support to your database, run:")
    print("  python migrate_spot_types.py")
    print()
    print("This adds the following columns to the spots table:")
    print("  - spot_type (enum)")
    print("  - xp_multiplier (float)")
    print("  - claim_multiplier (float)")
    print("  - icon_name (string)")
    print()
    
    # Step 2: Test Import
    print("Step 2: Test Import (Dry Run)")
    print("-" * 60)
    print("To preview what would be imported without making changes:")
    print("  python import_bavaria_pois.py --test")
    print()
    print("This will:")
    print("  - Query OpenStreetMap Overpass API")
    print("  - Show statistics of POIs found")
    print("  - Display counts by type")
    print("  - NOT insert anything into the database")
    print()
    
    # Step 3: Limited Import
    print("Step 3: Limited Import (Testing)")
    print("-" * 60)
    print("To import a limited number of POIs for testing:")
    print("  python import_bavaria_pois.py --limit 100")
    print()
    print("This will import up to 100 POIs per category.")
    print()
    
    # Step 4: Full Import
    print("Step 4: Full Import")
    print("-" * 60)
    print("To import all POIs for Bavaria (may take 5-10 minutes):")
    print("  python import_bavaria_pois.py")
    print()
    print("Expected results:")
    print("  - Churches: 3,000-5,000 spots")
    print("  - Tourist Attractions: 500-1,000 spots")
    print("  - Sports Facilities: 1,000-2,000 spots")
    print("  - Playgrounds: 500-1,000 spots")
    print("  - Castles: 100-200 spots")
    print("  - Museums: 300-500 spots")
    print("  - Other types: 2,000-4,000 spots")
    print("  - Total: ~10,000-15,000 spots")
    print()
    
    # Step 5: Using the API
    print("Step 5: Using the New Spot Type Features")
    print("-" * 60)
    print("Creating a spot with a specific type via API:")
    print()
    print("POST /api/spots")
    print("""{
  "name": "Schloss Neuschwanstein",
  "description": "Famous castle in Bavaria",
  "latitude": 47.5576,
  "longitude": 10.7498,
  "spot_type": "castle",
  "xp_multiplier": 2.5,
  "claim_multiplier": 2.0,
  "icon_name": "castle"
}""")
    print()
    print("Querying nearby spots (includes spot type information):")
    print("GET /api/spots/nearby?latitude=48.1351&longitude=11.5820&radius=5000")
    print()
    
    # Step 6: Frontend
    print("Step 6: Frontend Display")
    print("-" * 60)
    print("The frontend automatically:")
    print("  - Shows emoji icons for each spot type")
    print("  - Displays larger markers (24x24px) for special types")
    print("  - Shows spot type and bonuses in popups")
    print("  - Example: '🏰 castle +150% XP, +100% Claims'")
    print()
    
    # Configuration
    print("Step 7: Configuration")
    print("-" * 60)
    print("To adjust multipliers, edit app/spot_types_config.py:")
    print()
    print("SPOT_TYPE_CONFIG = {")
    print("    SpotType.CASTLE: {")
    print("        'xp_multiplier': 2.5,  # +150% XP")
    print("        'claim_multiplier': 2.0,  # +100% Claims")
    print("        'icon': 'castle'")
    print("    },")
    print("    # ... other types")
    print("}")
    print()
    
    # Done
    print("=" * 60)
    print("For complete documentation, see: BAVARIA_POI_IMPORT.md")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
