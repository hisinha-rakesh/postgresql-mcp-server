# PostgreSQL Backup - All Supported Path Examples

## ✅ You Can Backup To ANY Location!

The MCP server supports backing up to **any folder on your system**. Here are examples:

---

## Example 1: Backup to C: drive
```
"Backup youtube_db to C:\DatabaseBackups"
```
**Result**: `C:\DatabaseBackups\youtube_db_backup_20231207_164522.dump`

---

## Example 2: Backup to D: drive
```
"Backup library to D:\MyBackups"
```
**Result**: `D:\MyBackups\library_backup_20231207_164522.dump`

---

## Example 3: Backup to E: drive
```
"Backup myapp to E:\Production\Backups"
```
**Result**: `E:\Production\Backups\myapp_backup_20231207_164522.dump`

---

## Example 4: Backup to Documents folder
```
"Backup youtube_db to C:\Users\kusha\Documents\DatabaseBackups"
```
**Result**: `C:\Users\kusha\Documents\DatabaseBackups\youtube_db_backup_20231207_164522.dump`

---

## Example 5: Backup to Desktop
```
"Backup library to C:\Users\kusha\Desktop\Backups"
```
**Result**: `C:\Users\kusha\Desktop\Backups\library_backup_20231207_164522.dump`

---

## Example 6: Backup to Network Drive (if mapped)
```
"Backup youtube_db to Z:\SharedBackups"
```
**Result**: `Z:\SharedBackups\youtube_db_backup_20231207_164522.dump`

---

## Example 7: Backup with nested folders
```
"Backup myapp to C:\Data\PostgreSQL\Backups\Production"
```
**Result**: `C:\Data\PostgreSQL\Backups\Production\myapp_backup_20231207_164522.dump`

---

## Example 8: Backup with custom filename
```
"Backup youtube_db to D:\Backups\my_important_backup.dump"
```
**Result**: `D:\Backups\my_important_backup.dump` (exact name you specified)

---

## Example 9: Backup as SQL file to any location
```
"Backup library to E:\SQLBackups\library_export.sql"
```
**Result**: `E:\SQLBackups\library_export.sql` (plain SQL format)

---

## Example 10: Using default location (from .env)
```
"Backup youtube_db"
```
**Result**: `C:\Agentic-RAG\youtube_db_backup_20231207_164522.dump` (uses DEFAULT_BACKUP_DIR)

---

## Example 11: Relative path (from current directory)
```
"Backup myapp to backups\daily"
```
**Result**: `{current_directory}\backups\daily\myapp_backup_20231207_164522.dump`

---

## Example 12: Unix-style paths (also work on Windows)
```
"Backup library to C:/Backups/PostgreSQL"
```
**Result**: `C:\Backups\PostgreSQL\library_backup_20231207_164522.dump`

---

## Key Points

✅ **ANY path works** - C:, D:, E:, network drives, relative paths, etc.
✅ **Folders are created automatically** if they don't exist
✅ **Filename is auto-generated** unless you specify a full path with filename
✅ **DEFAULT_BACKUP_DIR in .env** is only used when you don't specify a path
✅ **Works with forward slashes** (/) or backslashes (\)

---

## Common Use Cases

### For daily backups
Set `DEFAULT_BACKUP_DIR` in `.env` to your preferred location, then just say:
```
"Backup youtube_db"
```

### For ad-hoc backups to different locations
Always specify the full path:
```
"Backup youtube_db to E:\SpecialBackups"
```

### For custom filenames
Include the filename in your request:
```
"Backup youtube_db to D:\Backups\before_migration.dump"
```

---

## The DEFAULT_BACKUP_DIR is Just a Convenience

Think of `DEFAULT_BACKUP_DIR` in `.env` as your "favorite" backup location. You can always override it by specifying any path you want in Claude Desktop!

**In Summary**:
- 🚀 Backup to **ANY folder** you want, anytime
- 🎯 `DEFAULT_BACKUP_DIR` is just a fallback for convenience
- 💪 Full flexibility - you're not locked into any specific location!
