# SpotType Enum Fix - Quick Reference

## 🚨 Problem
```
LookupError: 'standard' is not among the defined enum values. 
Enum name: spottype. Possible values: STANDARD, CHURCH, SIGHT, ..., STATUE
```

## ⚡ Quick Fix (Production)
```bash
# 1. Backup (IMPORTANT!)
docker exec claim-db pg_dump -U claim_user claim_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Apply fix
python3 fix_spot_type_enum.py

# 3. Restart
docker-compose -f docker-compose.prod.yml restart api
```

## 📚 Documentation
- **User Guide**: [APPLY_SPOTTYPE_FIX.md](APPLY_SPOTTYPE_FIX.md)
- **Technical Details**: [SPOTTYPE_ENUM_FIX.md](SPOTTYPE_ENUM_FIX.md)
- **Summary**: [SPOTTYPE_FIX_SUMMARY.md](SPOTTYPE_FIX_SUMMARY.md)

## 🧪 Verification
```bash
python3 verify_spot_type_fix.py
```

## 🔄 Rollback (if needed)
```bash
docker exec -i claim-db psql -U claim_user -d claim_db < backup_YYYYMMDD_HHMMSS.sql
```

## ✅ What This Fixes
- ❌ Before: `/api/loot/cleanup` → 500 Error
- ✅ After: `/api/loot/cleanup` → 200 OK
- ❌ Before: `/api/claims/heatmap/all` → 500 Error
- ✅ After: `/api/claims/heatmap/all` → 200 OK

## 📋 Files in This Fix
| File | Purpose |
|------|---------|
| `fix_spot_type_enum.py` | Python migration script |
| `fix_spot_type_enum.sql` | SQL migration script |
| `rollback_spot_type_enum.sql` | Rollback script |
| `verify_spot_type_fix.py` | Verification script |
| `migrate_spot_types.py` | Updated for new installs |
| `APPLY_SPOTTYPE_FIX.md` | User guide |
| `SPOTTYPE_ENUM_FIX.md` | Technical docs |
| `SPOTTYPE_FIX_SUMMARY.md` | Summary |
| `tests/test_spot_types.py` | Test suite |

## 🎯 Key Points
1. **Database enum** now uses UPPERCASE: `'STANDARD'`, `'CHURCH'`
2. **API responses** still lowercase: `"standard"`, `"church"`
3. **No frontend changes** needed
4. **Backward compatible**

## 🆕 New Installations
No action needed - `migrate_spot_types.py` creates enum correctly.

## 💡 Why This Happened
SQLAlchemy 2.0 with PostgreSQL native enums uses Python enum **member names** (STANDARD) not **values** (standard). Original migration created lowercase enum values, causing the mismatch.

## 📞 Support
- Check logs: `docker logs claim-api`
- Run verification: `python3 verify_spot_type_fix.py`
- See documentation files listed above
