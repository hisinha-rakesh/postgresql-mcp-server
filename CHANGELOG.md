# Changelog - PostgreSQL MCP Server Backup Fix

## Version 1.1.0 - 2024-12-07

### Fixed: Password Authentication Issue
**Problem**: pg_dump was failing with "password authentication failed for user" error even though manual pg_dump with password prompt worked fine.

**Root Cause**:
- Password in DATABASE_URL was URL-encoded (e.g., `Centurylink%40123`)
- The password wasn't being decoded before passing to pg_dump via PGPASSWORD environment variable
- Azure PostgreSQL username format (`username@servername`) wasn't being preserved

**Solution**:
1. Added `urllib.parse.unquote()` to decode password before setting PGPASSWORD
2. Added `urllib.parse.unquote()` to decode username to preserve Azure format
3. Added logging to help diagnose authentication issues
4. Added null checks for hostname to prevent errors

### Added: Flexible Backup Path Handling

**New Feature**: Auto-generate timestamped filenames when only folder path is provided

**How it works**:
- If you specify `C:\Agentic-RAG` (folder only), filename is auto-generated as `database_backup_20231207_163422.dump`
- If you specify `C:\Agentic-RAG\mybackup.dump` (full path), that exact filename is used
- Backup directory is created automatically if it doesn't exist

**Configuration**:
- Added `DEFAULT_BACKUP_DIR` environment variable support
- Can be set in `.env` file: `DEFAULT_BACKUP_DIR=C:\Agentic-RAG`

### Code Changes

#### File: `mcp_server_enterprise.py`

**Lines 46-47**: Added DEFAULT_BACKUP_DIR configuration
```python
# Backup configuration
DEFAULT_BACKUP_DIR = os.getenv("DEFAULT_BACKUP_DIR", os.path.join(os.getcwd(), "backups"))
```

**Lines 440-441**: Updated backup_database tool description
```python
description="Create a backup of a PostgreSQL database. When user specifies a folder location (e.g., 'backup to C:\\Agentic-RAG'), use that path with format: {folder}\\{database_name}_backup_{timestamp}.dump. ..."
```

**Lines 1195-1213**: Added auto-filename generation logic in `handle_backup_database`
```python
# Handle backup_path: if it's a directory, generate filename
backup_path_obj = Path(backup_path)
if backup_path_obj.is_dir() or (not backup_path_obj.suffix and not backup_path_obj.exists()):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext_map = {"custom": ".dump", "plain": ".sql", "tar": ".tar", "directory": ""}
    extension = ext_map.get(backup_format, ".dump")
    filename = f"{database_name}_backup_{timestamp}{extension}"
    backup_path = str(backup_path_obj / filename)
```

**Lines 1255-1258**: Added username decoding in `_backup_with_pg_dump`
```python
if parsed.username:
    username = urllib.parse.unquote(parsed.username)
    pg_dump_cmd.extend(["-U", username])
    logger.info(f"Using username: {username}")
```

**Lines 1296-1301**: Added password decoding in `_backup_with_pg_dump`
```python
if parsed.password:
    password = urllib.parse.unquote(parsed.password)
    env["PGPASSWORD"] = password
    logger.info("Password extracted and set in environment")
else:
    logger.warning("No password found in DATABASE_URL")
```

**Lines 1309**: Added null check for hostname
```python
if 'azure.com' in (parsed.hostname or '') or sslmode in ['require', 'verify-ca', 'verify-full']:
```

**Lines 1678-1681, 1702-1705**: Added username decoding in `_restore_with_pg_tools`
```python
if parsed.username:
    username = urllib.parse.unquote(parsed.username)
    restore_cmd.extend(["-U", username])
    logger.info(f"Using username: {username}")
```

**Lines 1718-1723**: Added password decoding in `_restore_with_pg_tools`
```python
if parsed.password:
    password = urllib.parse.unquote(parsed.password)
    env["PGPASSWORD"] = password
    logger.info("Password extracted and set in environment")
else:
    logger.warning("No password found in DATABASE_URL")
```

#### File: `.env`

**Lines 5-7**: Added backup configuration
```env
# Backup Configuration (optional)
# If not set, defaults to ./backups folder
DEFAULT_BACKUP_DIR=C:\Agentic-RAG
```

### Documentation Added

1. **BACKUP_USAGE.md**: Comprehensive guide on backup functionality
2. **QUICK_START.md**: Quick start guide for Claude Desktop users
3. **CHANGELOG.md**: This file, documenting all changes

### Testing Files Added

1. **test_backup_fix.py**: Test DATABASE_URL parsing and password decoding
2. **test_backup_path.py**: Test backup path handling logic

### Usage Examples

#### Before:
```
Request: backup youtube_db to /tmp/mybackup.dump
Response: Error - password authentication failed
```

#### After:
```
Request: backup youtube_db to C:\Agentic-RAG
Response: Success - Created C:\Agentic-RAG\youtube_db_backup_20231207_163422.dump
```

### Breaking Changes
None - All changes are backward compatible

### Migration Guide
No migration needed. Update `.env` file to add `DEFAULT_BACKUP_DIR` if desired (optional).

### Performance Impact
Negligible - Only adds URL decoding operations which are fast

### Security Improvements
- Password is no longer logged (only masked output for debugging)
- Environment variables properly scoped to subprocess only
- No password storage in temporary files

### Known Limitations
- Windows console encoding issues with unicode characters in test output (cosmetic only)
- Directory format backups require pg_dump tool (falls back to SQL if unavailable)

### Future Enhancements
- Add support for incremental backups
- Add backup scheduling functionality
- Add backup rotation/retention policies
- Add backup verification checksums

### Contributors
- Fixed authentication issue for Azure PostgreSQL
- Added flexible path handling for user convenience
- Improved logging for troubleshooting

---

## How to Verify the Fix

1. **Check password decoding**:
   ```bash
   python test_backup_fix.py
   ```
   Expected output: Password should show as decoded (e.g., `Centurylink@123` not `Centurylink%40123`)

2. **Check path handling**:
   ```bash
   python test_backup_path.py
   ```
   Expected output: Shows how different path inputs are handled

3. **Test actual backup** in Claude Desktop:
   ```
   "Backup the library database to C:\Agentic-RAG"
   ```
   Expected result: Creates timestamped .dump file successfully

## Support
For issues or questions, check the README.md or create an issue in the repository.
