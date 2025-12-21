# SpotType Enum Case Mismatch Fix

## Problem

The application was crashing with the following error when querying spots from the database:

```
LookupError: 'standard' is not among the defined enum values. Enum name: spottype. 
Possible values: STANDARD, CHURCH, SIGHT, ..., STATUE
```

This occurred on endpoints like:
- `/api/loot/cleanup`
- `/api/claims/heatmap/all`

## Root Cause

When using SQLAlchemy with PostgreSQL native enum types, there is a mismatch between how Python enums work and what values are stored in the database:

1. **Python Enum Definition** (in `app/models.py`):
   ```python
   class SpotType(str, enum.Enum):
       STANDARD = "standard"  # .name = "STANDARD", .value = "standard"
       CHURCH = "church"      # .name = "CHURCH", .value = "church"
       # ...
   ```

2. **PostgreSQL Enum** (originally created by migration):
   ```sql
   CREATE TYPE spottype AS ENUM ('standard', 'church', ...);  -- lowercase!
   ```

3. **SQLAlchemy Behavior**:
   - By default, SQLAlchemy uses the enum **member name** (`.name`) when working with native PostgreSQL enums
   - So it expects database values to be `'STANDARD'`, `'CHURCH'`, etc. (uppercase)
   - But the database had `'standard'`, `'church'`, etc. (lowercase)
   - This caused the LookupError when reading from the database

## Solution

The fix involves three parts:

### 1. Database Migration

Run the `fix_spot_type_enum.py` script to update the PostgreSQL enum:

```bash
python3 fix_spot_type_enum.py
```

This script:
- Converts the `spot_type` column temporarily to TEXT
- Updates all existing values to uppercase
- Drops and recreates the `spottype` enum with uppercase values
- Converts the column back to use the new enum type

### 2. Updated Migration Script

The `migrate_spot_types.py` script has been updated to create the enum with uppercase values for future installations:

```python
CREATE TYPE spottype AS ENUM (
    'STANDARD', 'CHURCH', 'SIGHT', ...  -- Now uppercase!
);
```

### 3. Python Model (No Changes Needed)

The Python enum in `app/models.py` keeps lowercase **values** for compatibility:

```python
class SpotType(str, enum.Enum):
    STANDARD = "standard"  # SQLAlchemy uses .name ("STANDARD") for PostgreSQL
    CHURCH = "church"      # But .value ("church") for JSON/API responses
```

## API Compatibility

The Pydantic schema in `app/schemas.py` continues to use lowercase values, ensuring API responses remain unchanged:

```python
class SpotType(str, Enum):
    STANDARD = "standard"  # API returns lowercase
    CHURCH = "church"
```

When serializing SQLAlchemy models to Pydantic schemas, the conversion happens automatically:
- Database stores: `'STANDARD'` (uppercase)
- Python enum has `.name = "STANDARD"` and `.value = "standard"`
- API returns: `"standard"` (lowercase)

## How to Apply the Fix

1. **For existing production databases**:
   ```bash
   python3 fix_spot_type_enum.py
   ```

2. **For new installations**:
   - The updated `migrate_spot_types.py` will create the enum correctly
   - No additional steps needed

## Verification

After applying the fix, test the previously failing endpoints:

```bash
# Should return 200 OK
curl http://localhost:8000/api/loot/cleanup -X POST
curl http://localhost:8000/api/claims/heatmap/all
```

## Technical Details

### Why SQLAlchemy Uses .name Instead of .value

For native PostgreSQL enum types, SQLAlchemy maps Python enum members directly to database enum values using the member name. This is the default behavior for `native_enum=True` (the default).

### Alternative Approach (Not Used)

We could have set `native_enum=False` in the column definition:

```python
spot_type = Column(SQLEnum(SpotType, native_enum=False), ...)
```

This would:
- Store enum values as VARCHAR in PostgreSQL
- Use the enum `.value` instead of `.name`
- Not use the native PostgreSQL enum type

However, this approach has downsides:
- Loses database-level type safety
- Requires dropping the existing enum type
- Less efficient than native enums

Therefore, we chose to update the database enum to match SQLAlchemy's expectations.
