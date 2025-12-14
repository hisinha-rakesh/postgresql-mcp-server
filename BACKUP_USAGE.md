# PostgreSQL MCP Server - Backup Usage Guide

## Overview
This MCP server provides enterprise-level PostgreSQL backup and restore capabilities with automatic path handling.

## Backup Directory Configuration

### Method 1: Using .env file (Recommended)
Set the default backup directory in your `.env` file:

```env
DEFAULT_BACKUP_DIR=C:\Agentic-RAG
```

### Method 2: Specify full path in backup command
You can always override the default by providing a full path.

## Usage Examples in Claude Desktop

### Example 1: Backup to default directory (from .env)
When you say in Claude Desktop:
```
"Take a backup of youtube_db database"
```

The backup will be saved to: `C:\Agentic-RAG\youtube_db_backup_20231207_143022.dump`

### Example 2: Backup to specific folder
When you say:
```
"Take a backup of youtube_db database to C:\Agentic-RAG"
```

The backup will be saved to: `C:\Agentic-RAG\youtube_db_backup_20231207_143022.dump`

### Example 3: Backup with specific filename
When you say:
```
"Take a backup of youtube_db database to C:\Agentic-RAG\my_custom_backup.dump"
```

The backup will be saved to: `C:\Agentic-RAG\my_custom_backup.dump`

## Backup Formats

- **custom** (default): Compressed binary format, best for large databases
- **plain**: Plain SQL script, human-readable
- **tar**: TAR archive format
- **directory**: Directory with one file per table

## Auto-generated Filename Format

When you specify only a folder path, the filename is automatically generated as:
```
{database_name}_backup_{YYYYMMDD_HHMMSS}.{extension}
```

Examples:
- `youtube_db_backup_20231207_143022.dump` (custom format)
- `youtube_db_backup_20231207_143022.sql` (plain format)
- `youtube_db_backup_20231207_143022.tar` (tar format)

## Password Authentication Fix

The server now properly handles:
- ✅ URL-encoded passwords (e.g., `Centurylink%40123` → `Centurylink@123`)
- ✅ Azure PostgreSQL username format (e.g., `username@servername`)
- ✅ SSL/TLS connections required by Azure PostgreSQL
- ✅ PGPASSWORD environment variable for non-interactive backups

## How It Works

1. **Password Handling**: The password from `DATABASE_URL` is URL-decoded and passed via the `PGPASSWORD` environment variable
2. **Username Handling**: Azure's `username@servername` format is properly preserved
3. **SSL Mode**: Automatically detected from `DATABASE_URL` and set via `PGSSLMODE` environment variable
4. **Path Handling**:
   - If you provide a directory, a timestamped filename is auto-generated
   - If you provide a full path with filename, it's used as-is
   - Directory is created automatically if it doesn't exist

## Technical Details

### pg_dump Command Generated
```bash
pg_dump -h pgs-youtube-app.postgres.database.azure.com \
        -p 5432 \
        -U pgadmina@pgs-youtube-app \
        -d youtube_db \
        -F c \
        -f "C:\Agentic-RAG\youtube_db_backup_20231207_143022.dump" \
        --verbose
```

### Environment Variables Set
```bash
PGPASSWORD=Centurylink@123
PGSSLMODE=require
```

## Troubleshooting

### Issue: "password authentication failed"
**Solution**: Ensure your `DATABASE_URL` in `.env` has the password URL-encoded if it contains special characters.

Example:
- Wrong: `postgresql://user:Pass@123@host`
- Correct: `postgresql://user:Pass%40123@host` (@ is encoded as %40)

### Issue: "pg_dump not found"
**Solution**: Install PostgreSQL client tools or the server will automatically fall back to SQL-based backup method.

### Issue: "permission denied" on backup directory
**Solution**: Ensure the directory exists and has write permissions, or the server will create it automatically.

## Features

✅ Automatic password URL-decoding
✅ Azure PostgreSQL support with SSL
✅ Auto-generated timestamped filenames
✅ Automatic directory creation
✅ Support for custom backup paths
✅ Multiple backup formats
✅ Compression support
✅ Schema-only or data-only backups
✅ Table filtering (include/exclude)
✅ Fallback to SQL-based backup if pg_dump unavailable

## Example Conversation

**You**: "Take a backup of my library database to C:\Agentic-RAG"

**Claude**: "I'll backup the library database to C:\Agentic-RAG folder."

*Result*: `C:\Agentic-RAG\library_backup_20231207_143532.dump` created successfully
