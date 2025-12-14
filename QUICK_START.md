# Quick Start Guide - PostgreSQL Backup with Claude Desktop

## Setup (One-time)

1. **Configure your default backup directory** in `.env`:
   ```env
   DEFAULT_BACKUP_DIR=C:\Agentic-RAG
   ```

2. **Ensure your DATABASE_URL is correct** with URL-encoded password:
   ```env
   DATABASE_URL=postgresql://username:password@host:5432/database?sslmode=require
   ```

   Note: If password contains special characters, encode them:
   - `@` becomes `%40`
   - `#` becomes `%23`
   - `&` becomes `%26`
   - etc.

3. **Restart Claude Desktop** to load the new configuration.

## Usage in Claude Desktop

### Simple Backup (uses default folder from .env)
Just say:
```
"Backup the youtube_db database"
```

Result: Creates `C:\Agentic-RAG\youtube_db_backup_YYYYMMDD_HHMMSS.dump`

---

### Backup to Specific Folder
Say:
```
"Backup the library database to C:\Agentic-RAG"
```

Result: Creates `C:\Agentic-RAG\library_backup_YYYYMMDD_HHMMSS.dump`

---

### Backup with Custom Filename
Say:
```
"Backup the youtube_db database to C:\Agentic-RAG\my_backup.dump"
```

Result: Creates `C:\Agentic-RAG\my_backup.dump`

---

### Backup as SQL File (Plain Text)
Say:
```
"Backup the library database to C:\Agentic-RAG as SQL format"
```

Result: Creates `C:\Agentic-RAG\library_backup_YYYYMMDD_HHMMSS.sql`

---

## What Changed?

### Before (not working):
- Password wasn't being decoded from URL encoding
- pg_dump would fail with "password authentication failed"

### After (working now):
- ✅ Password is properly URL-decoded (`Centurylink%40123` → `Centurylink@123`)
- ✅ Username format preserved for Azure (`username@servername`)
- ✅ SSL mode automatically detected and configured
- ✅ Auto-generates timestamped filenames when you specify a folder
- ✅ Creates backup directory if it doesn't exist

## File Naming Convention

When you specify just a folder path, files are named:
```
{database_name}_backup_{YYYYMMDD_HHMMSS}.{extension}
```

Examples:
- `youtube_db_backup_20231207_163422.dump` (custom/binary format)
- `library_backup_20231207_163422.sql` (plain SQL format)
- `myapp_backup_20231207_163422.tar` (TAR format)

## Tips

1. **Default location**: If you always backup to the same folder, set `DEFAULT_BACKUP_DIR` in `.env`
2. **Custom filenames**: Include the filename in your request if you want a specific name
3. **Multiple formats**: Request "SQL format" for plain text, or "custom format" for compressed binary
4. **Scheduled backups**: You can ask Claude to help you create a scheduled task

## Verification

To verify your setup is working:

1. **Check DATABASE_URL parsing**:
   ```bash
   cd C:\Users\kusha\postgresql-mcp
   python test_backup_fix.py
   ```

2. **Test path handling**:
   ```bash
   python test_backup_path.py
   ```

3. **Try a real backup in Claude Desktop**:
   ```
   "Backup the library database to C:\Agentic-RAG"
   ```

## Common Issues

### Issue: "password authentication failed"
**Cause**: Password in DATABASE_URL isn't URL-encoded
**Fix**: Encode special characters (@ → %40, # → %23, etc.)

### Issue: "folder not found"
**Cause**: Backup directory doesn't exist
**Fix**: The server will create it automatically, but ensure parent folders exist

### Issue: No default backup location
**Cause**: DEFAULT_BACKUP_DIR not set in .env
**Fix**: Add `DEFAULT_BACKUP_DIR=C:\Agentic-RAG` to your `.env` file

## Success!

You should now be able to backup databases easily through Claude Desktop with proper password authentication and flexible path handling!
