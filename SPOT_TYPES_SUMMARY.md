# Spot Types Implementation - Summary

## Overview

This implementation adds a comprehensive spot type system to the Claim GPS game, enabling different types of locations (churches, castles, sports facilities, etc.) to have unique XP and claim reward multipliers. Additionally, a Bavaria POI import script has been created to automatically populate the database with ~10,000-15,000 real-world locations from OpenStreetMap.

## What Was Changed

### Database Layer

1. **Extended `Spot` Model** (`app/models.py`)
   - Added `SpotType` enum with 17 different categories
   - Added `spot_type` column (enum, default: 'standard')
   - Added `xp_multiplier` column (float, default: 1.0)
   - Added `claim_multiplier` column (float, default: 1.0)
   - Added `icon_name` column (string, nullable)

2. **Migration Script** (`migrate_spot_types.py`)
   - Supports both PostgreSQL (with enum type) and SQLite
   - Idempotent - can be run multiple times safely
   - Creates index on `spot_type` for query performance

### Backend Layer

1. **Schemas** (`app/schemas.py`)
   - Added `SpotType` enum to schemas
   - Extended `SpotCreate` with spot type fields
   - Extended `SpotResponse` to include type information

2. **Configuration** (`app/spot_types_config.py`)
   - NEW FILE: Centralized configuration for all spot types
   - Defines XP and claim multipliers for each type
   - Helper functions: `get_xp_multiplier()`, `get_claim_multiplier()`, `get_icon_name()`

3. **Services**
   - **spot_service.py**: Updated `create_spot()` to apply type configuration
   - **log_service.py**: Updated `create_log()` to apply spot type multipliers when calculating rewards

4. **Routers** (`app/routers/spots.py`)
   - All spot endpoints now return type information
   - Spot responses include multipliers and icons

### Frontend Layer

1. **JavaScript** (`frontend/app.js`)
   - Added `SPOT_TYPE_ICONS` mapping (17 emoji icons)
   - Updated spot marker creation to support icons
   - Larger markers (24x24px) for spots with icons
   - Updated popup content to show spot type and bonuses

2. **CSS** (`frontend/styles.css`)
   - Added `.has-icon` class for icon-based markers
   - Icon positioning and styling
   - Maintained backward compatibility

### Import Tools

1. **Bavaria POI Import** (`import_bavaria_pois.py`)
   - NEW SCRIPT: Queries OpenStreetMap Overpass API
   - Maps OSM tags to spot types automatically
   - Command-line options for testing and limiting imports
   - Expected to import 10,000-15,000 POIs for Bavaria

2. **Example Usage** (`example_usage.py`)
   - NEW SCRIPT: Demonstrates how to use the system
   - Step-by-step guide for migration and import

### Documentation

1. **BAVARIA_POI_IMPORT.md**
   - NEW FILE: Complete guide for POI import
   - Lists all spot types and multipliers
   - Import instructions and troubleshooting
   - Legal/attribution requirements (OpenStreetMap)

2. **README.md**
   - Updated with spot type features
   - Reference to import documentation
   - Configuration examples

## Spot Types and Multipliers

| Spot Type | Icon | XP Bonus | Claim Bonus | Use Case |
|-----------|------|----------|-------------|----------|
| Standard | 📍 | Baseline | Baseline | Default spots |
| Church | ⛪ | +50% | +30% | Churches, cathedrals |
| Castle | 🏰 | +150% | +100% | Castles, palaces |
| Sight | 🏛️ | +100% | +50% | Tourist attractions |
| Sports Facility | 🏃 | +30% | +20% | Sports centers, stadiums |
| Playground | 🎮 | +20% | +10% | Playgrounds |
| Museum | 🏛️ | +120% | +60% | Museums, galleries |
| Monument | 🗿 | +80% | +40% | Monuments, memorials |
| Park | 🌳 | +20% | +10% | Parks, gardens |
| Viewpoint | 🔭 | +70% | +30% | Scenic viewpoints |
| Historic | 📜 | +90% | +50% | Historic sites |
| Cultural | 🎭 | +60% | +30% | Cultural centers |
| Religious | 🕌 | +40% | +20% | Other religious sites |
| Town Hall | 🏛️ | +50% | +30% | Town halls |
| Market | 🏪 | +30% | +20% | Markets |
| Fountain | ⛲ | +20% | +10% | Fountains |
| Statue | 🗽 | +40% | +20% | Statues, sculptures |

## How It Works

### When Creating a Spot

1. User specifies spot type (or it's auto-detected from OSM import)
2. System looks up configuration for that type
3. XP and claim multipliers are set on the spot record
4. Icon is assigned based on type

### When Logging a Spot

1. Base XP and claim points are calculated (with existing bonuses)
2. Spot type multipliers are applied:
   ```python
   xp_gained = base_xp * spot.xp_multiplier
   claim_points = base_claim * spot.claim_multiplier
   ```
3. User receives enhanced rewards for special locations

### Frontend Display

1. Spot marker shows emoji icon for non-standard types
2. Popup displays spot type name and bonuses
3. Example: "🏰 castle +150% XP, +100% Claims"

## Usage Instructions

### Step 1: Run Migration

```bash
python migrate_spot_types.py
```

This adds the required columns to your database.

### Step 2: Test Import (Optional)

```bash
python import_bavaria_pois.py --test --limit 10
```

Preview what would be imported without making changes.

### Step 3: Import Bavaria POIs

```bash
# Full import (10k-15k spots, takes 5-10 minutes)
python import_bavaria_pois.py

# Or limited import for testing
python import_bavaria_pois.py --limit 100
```

### Step 4: Verify

1. Check the database: `SELECT COUNT(*), spot_type FROM spots GROUP BY spot_type;`
2. Open the game and view the map
3. Visit different spot types and verify multipliers work

## API Examples

### Creating a Spot with Type

```bash
curl -X POST http://localhost:8000/api/spots \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Schloss Neuschwanstein",
    "description": "Famous castle in Bavaria",
    "latitude": 47.5576,
    "longitude": 10.7498,
    "spot_type": "castle",
    "xp_multiplier": 2.5,
    "claim_multiplier": 2.0,
    "icon_name": "castle"
  }'
```

### Querying Nearby Spots

```bash
curl http://localhost:8000/api/spots/nearby?latitude=48.1351&longitude=11.5820&radius=5000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response includes spot type information:

```json
{
  "id": 123,
  "name": "Schloss Neuschwanstein",
  "spot_type": "castle",
  "xp_multiplier": 2.5,
  "claim_multiplier": 2.0,
  "icon_name": "castle",
  ...
}
```

## Benefits

1. **Enhanced Gameplay**: Different locations provide different rewards
2. **Real-World Integration**: Thousands of real POIs imported automatically
3. **Exploration Incentive**: Players seek out high-value locations (castles, museums)
4. **Cultural Value**: Highlights Bavaria's cultural and historical sites
5. **Scalable**: Easy to add more regions or adjust multipliers

## Limitations & Future Work

### Current Limitations

1. **Bavaria Only**: Import script is configured for Bavaria bounding box
2. **Basic Deduplication**: May create some duplicate spots
3. **Static Multipliers**: Multipliers are set at import time
4. **No Category Filtering**: Frontend shows all spots regardless of type

### Future Enhancements

1. **Region Expansion**: Add import support for other German states/countries
2. **Dynamic Multipliers**: Adjust based on time, events, or player activity
3. **Spot Type Filters**: UI to show/hide specific types
4. **Advanced Deduplication**: Better duplicate detection
5. **Spot Clustering**: Performance optimization for dense areas
6. **User-Generated Types**: Allow players to suggest spot types
7. **Seasonal Events**: Temporary multiplier boosts for certain types

## Technical Notes

### Database Performance

- Index on `spot_type` for fast filtering
- Consider partitioning if spot count exceeds 100k
- Spatial queries still use PostGIS indexes

### Frontend Performance

- Spots hidden at zoom < 13 to reduce marker count
- Icon rendering uses CSS (no image loading)
- Consider marker clustering for future versions

### API Performance

- Spot type queries are efficient (indexed)
- No additional joins required
- Multipliers applied in-memory during logging

## Testing Checklist

- [x] Python syntax validation
- [x] JavaScript syntax validation
- [ ] Database migration (PostgreSQL)
- [ ] Database migration (SQLite)
- [ ] API endpoints (create, query, delete)
- [ ] Import script (test mode)
- [ ] Import script (limited)
- [ ] Import script (full)
- [ ] Frontend display (desktop)
- [ ] Frontend display (mobile)
- [ ] Multiplier application (logging)
- [ ] Performance with 10k+ spots

## Support & Troubleshooting

See [BAVARIA_POI_IMPORT.md](BAVARIA_POI_IMPORT.md) for:
- Detailed troubleshooting guide
- Overpass API usage
- OpenStreetMap attribution requirements
- Common issues and solutions

## Credits

- **OpenStreetMap Contributors**: POI data source
- **Overpass API**: Query infrastructure
- **Emoji Icons**: Standard Unicode emoji set

## License Note

The imported POI data is from OpenStreetMap and is licensed under the Open Database License (ODbL). You must provide attribution: "© OpenStreetMap contributors"
