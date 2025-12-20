# Bavaria POI Import - Spot Types System

This document describes the new spot type system and how to import Points of Interest (POIs) from OpenStreetMap for Bavaria, Germany.

## Features

### Spot Type System

The application now supports different types of spots with unique characteristics:

- **Churches** (⛪): +50% XP, +30% Claims
- **Tourist Sights** (🏛️): +100% XP, +50% Claims  
- **Sports Facilities** (🏃): +30% XP, +20% Claims
- **Playgrounds** (🎮): +20% XP, +10% Claims
- **Castles** (🏰): +150% XP, +100% Claims
- **Museums** (🏛️): +120% XP, +60% Claims
- **Monuments** (🗿): +80% XP, +40% Claims
- **Parks** (🌳): +20% XP, +10% Claims
- **Viewpoints** (🔭): +70% XP, +30% Claims
- **Historic Sites** (📜): +90% XP, +50% Claims
- **Cultural Centers** (🎭): +60% XP, +30% Claims
- **Religious Sites** (🕌): +40% XP, +20% Claims
- **Town Halls** (🏛️): +50% XP, +30% Claims
- **Markets** (🏪): +30% XP, +20% Claims
- **Fountains** (⛲): +20% XP, +10% Claims
- **Statues** (🗽): +40% XP, +20% Claims

## Database Migration

Before importing POIs, run the database migration to add the required columns:

```bash
python migrate_spot_types.py
```

This will add the following columns to the `spots` table:
- `spot_type` - Enum type for spot category
- `xp_multiplier` - XP reward multiplier (e.g., 1.5 = +50%)
- `claim_multiplier` - Claim points multiplier
- `icon_name` - Icon identifier for the spot

The migration supports both PostgreSQL and SQLite databases.

## Importing Bavaria POIs

### Prerequisites

Install required dependencies:

```bash
pip install httpx
```

### Basic Import

Import all POI types for Bavaria:

```bash
python import_bavaria_pois.py
```

### Test Mode (Dry Run)

Preview what would be imported without making database changes:

```bash
python import_bavaria_pois.py --test
```

### Limited Import (for Testing)

Import only a limited number of POIs per category:

```bash
python import_bavaria_pois.py --limit 100
```

### Import Specific Category

Import only specific categories:

```bash
python import_bavaria_pois.py --category church  # Churches only
python import_bavaria_pois.py --category sight   # Tourist sights only
python import_bavaria_pois.py --category sports  # Sports facilities only
python import_bavaria_pois.py --category playground  # Playgrounds only
```

## How It Works

### 1. OpenStreetMap Overpass API

The import script queries the [Overpass API](https://overpass-api.de/) to fetch POI data from OpenStreetMap for the Bavaria region (bounding box: 47.27°N to 50.56°N, 8.98°E to 13.84°E).

### 2. POI Mapping

The script maps OpenStreetMap tags to our spot types:

| OSM Tag | Spot Type |
|---------|-----------|
| `amenity=place_of_worship` | Church |
| `building=church` | Church |
| `building=cathedral` | Church |
| `tourism=attraction` | Sight |
| `tourism=museum` | Museum |
| `historic=castle` | Castle |
| `leisure=sports_centre` | Sports Facility |
| `leisure=stadium` | Sports Facility |
| `leisure=playground` | Playground |
| `amenity=townhall` | Town Hall |
| `amenity=fountain` | Fountain |
| ... and many more |

### 3. Automatic Configuration

For each imported POI, the script automatically:
- Assigns the appropriate spot type
- Sets XP and claim multipliers based on spot type
- Assigns the corresponding icon
- Extracts name and description from OSM data
- Stores GPS coordinates

### 4. Deduplication

The script includes basic deduplication to avoid creating duplicate spots at the same location.

## Expected Results

Running the full import for Bavaria will create approximately:
- **Churches**: 3,000-5,000 spots
- **Tourist Attractions**: 500-1,000 spots  
- **Sports Facilities**: 1,000-2,000 spots
- **Playgrounds**: 500-1,000 spots
- **Castles**: 100-200 spots
- **Museums**: 300-500 spots
- **Other types**: 2,000-4,000 spots

**Total**: ~10,000-15,000 POI spots for Bavaria

## Frontend Display

The frontend automatically displays:
- Emoji icons for each spot type (e.g., ⛪ for churches, 🏰 for castles)
- Larger markers (24x24px) for special spot types
- Spot type information in popups
- Bonus percentages (e.g., "+50% XP, +30% Claims")
- Color-coded markers based on cooldown and dominance

## Configuration

### Adjusting Multipliers

Edit `app/spot_types_config.py` to change XP and claim multipliers:

```python
SPOT_TYPE_CONFIG = {
    SpotType.CASTLE: {
        "xp_multiplier": 2.5,  # +150% XP
        "claim_multiplier": 2.0,  # +100% Claims
        "icon": "castle",
        "description": "Castle or palace (Schloss)"
    },
    # ... other types
}
```

### Adding New Spot Types

1. Add the type to `SpotType` enum in `app/models.py`
2. Add configuration in `app/spot_types_config.py`
3. Add icon mapping in `frontend/app.js` (`SPOT_TYPE_ICONS`)
4. Add OSM mapping in `import_bavaria_pois.py` (`OSM_TO_SPOT_TYPE`)
5. Run migration again to update the enum type

## API Changes

### Creating Spots

When creating spots via API, you can now specify:

```json
POST /api/spots
{
  "name": "Schloss Neuschwanstein",
  "description": "Famous castle in Bavaria",
  "latitude": 47.5576,
  "longitude": 10.7498,
  "spot_type": "castle",
  "xp_multiplier": 2.5,
  "claim_multiplier": 2.0,
  "icon_name": "castle"
}
```

### Spot Response

Spot responses now include:

```json
{
  "id": 1,
  "name": "Schloss Neuschwanstein",
  "spot_type": "castle",
  "xp_multiplier": 2.5,
  "claim_multiplier": 2.0,
  "icon_name": "castle",
  ...
}
```

## Troubleshooting

### Import Fails with "Timeout"

The Overpass API may rate-limit or timeout for large queries. Solutions:
1. Use `--limit` to import smaller batches
2. Wait a few minutes and retry
3. Use a different Overpass API instance

### Database Error During Migration

If migration fails:
1. Check database connection
2. Ensure you have write permissions
3. For PostgreSQL, ensure PostGIS is installed
4. Check if columns already exist (migration is idempotent)

### POIs Not Showing on Map

1. Ensure migration was run successfully
2. Check that spots were imported (query database)
3. Clear browser cache
4. Check browser console for JavaScript errors
5. Verify zoom level (spots are hidden below zoom 13)

## Performance Considerations

### Database Indexes

The migration creates an index on `spot_type` for fast filtering:

```sql
CREATE INDEX idx_spots_spot_type ON spots(spot_type);
```

### Query Optimization

When querying many spots, the API uses:
- Spatial indexes (PostGIS)
- Radius-based filtering
- Pagination support

### Frontend Optimization

- Spots are hidden at zoom levels < 13
- Marker clustering may be added in the future
- Icon rendering uses CSS for performance

## Legal & Attribution

### OpenStreetMap Data

The imported POI data comes from OpenStreetMap and is licensed under the [Open Data Commons Open Database License (ODbL)](https://www.openstreetmap.org/copyright).

**Required Attribution**: "© OpenStreetMap contributors"

You must:
- Include this attribution when using the data
- Share adaptations under the same license
- Make data sources clear to users

### Overpass API

The [Overpass API](https://overpass-api.de/) is provided by the OpenStreetMap Foundation. Please use responsibly and follow their [usage policy](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html).

## Next Steps

1. Run the migration: `python migrate_spot_types.py`
2. Test the import: `python import_bavaria_pois.py --test --limit 10`
3. Run the full import: `python import_bavaria_pois.py`
4. Check the map to see the new POIs
5. Test logging at different spot types
6. Monitor XP and claim multipliers

## Support

For issues or questions:
- Check the logs for detailed error messages
- Ensure all dependencies are installed
- Verify database connectivity
- Check API availability (Overpass API status)
