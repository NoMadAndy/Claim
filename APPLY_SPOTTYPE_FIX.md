# How to Apply the SpotType Enum Fix

## Quick Start

If you're experiencing the error:
```
LookupError: 'standard' is not among the defined enum values
```

Follow these steps to fix it:

## Option 1: Using the Python Script (Recommended)

1. **Backup your database first!**
   ```bash
   docker exec claim-db pg_dump -U claim_user claim_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Run the migration script:**
   ```bash
   python3 fix_spot_type_enum.py
   ```

3. **Restart the application:**
   ```bash
   docker-compose -f docker-compose.prod.yml restart api
   ```

## Option 2: Using SQL Directly

1. **Backup your database first!**
   ```bash
   docker exec claim-db pg_dump -U claim_user claim_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Apply the SQL migration:**
   ```bash
   docker exec -i claim-db psql -U claim_user -d claim_db < fix_spot_type_enum.sql
   ```

3. **Restart the application:**
   ```bash
   docker-compose -f docker-compose.prod.yml restart api
   ```

## Verification

After applying the fix, verify it worked:

1. **Check the enum values in the database:**
   ```bash
   docker exec claim-db psql -U claim_user -d claim_db -c "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'spottype'::regtype ORDER BY enumlabel;"
   ```

   Expected output should show uppercase values:
   ```
    enumlabel       
   -----------------
    CASTLE
    CHURCH
    CULTURAL
    FOUNTAIN
    HISTORIC
    MARKET
    MONUMENT
    MUSEUM
    PARK
    PLAYGROUND
    RELIGIOUS
    SIGHT
    SPORTS_FACILITY
    STANDARD
    STATUE
    TOWNHALL
    VIEWPOINT
   ```

2. **Test the previously failing endpoints:**
   ```bash
   # Test loot cleanup (requires authentication)
   curl -X POST http://localhost:8000/api/loot/cleanup \
     -H "Authorization: Bearer YOUR_TOKEN"
   
   # Test heatmap endpoint
   curl http://localhost:8000/api/claims/heatmap/all
   ```

   Both should return successful responses without the LookupError.

3. **Check the application logs:**
   ```bash
   docker logs claim-api --tail 50
   ```

   You should not see any more enum-related errors.

## Rollback (If Needed)

If something goes wrong and you need to rollback:

1. **Restore from backup:**
   ```bash
   docker exec -i claim-db psql -U claim_user -d claim_db < backup_YYYYMMDD_HHMMSS.sql
   ```

   OR

2. **Use the rollback script** (not recommended, better to restore from backup):
   ```bash
   docker exec -i claim-db psql -U claim_user -d claim_db < rollback_spot_type_enum.sql
   ```

## For New Installations

If you're setting up a new installation, the migration is not needed. The updated `migrate_spot_types.py` script will create the enum correctly with uppercase values from the start.

## Technical Details

For more information about why this fix is needed and how it works, see:
- [SPOTTYPE_ENUM_FIX.md](SPOTTYPE_ENUM_FIX.md) - Detailed technical explanation

## Support

If you encounter any issues:
1. Check that you backed up your database before applying the fix
2. Review the application logs: `docker logs claim-api`
3. Verify your PostgreSQL version is compatible (15+)
4. Ensure all prerequisites are installed
