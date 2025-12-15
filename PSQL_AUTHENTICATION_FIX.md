# psql / pg_dump / pg_restore Authentication Issue

## Problem
Even though the password is correctly URL-decoded (`XXXXXXXX@123`) and set in the `PGPASSWORD` environment variable, `psql`, `pg_dump`, and `pg_restore` are failing with "password authentication failed".

## Current Status
- ✅ Password is correctly decoded: `Centurylink%40123` → `Centurylink@123`
- ✅ Username is correctly decoded: `pgadmina@pgs-youtube-app`
- ✅ SSL mode is set: `require`
- ✅ `PGPASSWORD` environment variable is set
- ❌ Connection still fails

## Why Manual Entry Works
When you run `pg_dump` manually, it prompts for a password interactively, and that works. This suggests:
1. The credentials are correct
2. Something about the `PGPASSWORD` environment variable approach isn't working
3. Possible Azure PostgreSQL specific requirement

## Possible Solutions

### Solution 1: Use .pgpass File (Recommended)
Create a `.pgpass` file (or `pgpass.conf` on Windows) with your credentials.

**Location:**
- Windows: `%APPDATA%\postgresql\pgpass.conf`
- Linux/Mac: `~/.pgpass`

**Format:**
```
hostname:port:database:username:password
```

**For your setup:**
```
pgs-youtube-app.postgres.database.azure.com:5432:*:pgadmina@pgs-youtube-app:XXXXXXXX@123
```

The `*` means it applies to all databases on that server.

**Permissions (Linux/Mac):**
```bash
chmod 600 ~/.pgpass
```

### Solution 2: Check if PGPASSWORD is Being Overridden
Sometimes system environment variables or other configs can override `PGPASSWORD`.

### Solution 3: Use Connection Service File
Create a `pg_service.conf` file.

### Solution 4: Test with Different Authentication Method
Azure PostgreSQL might have specific requirements.

## Testing

### Test 1: Check if PGPASSWORD works at all
```cmd
set PGPASSWORD=Centurylink@123
set PGSSLMODE=require
psql -h pgs-youtube-app.postgres.database.azure.com -U "pgadmina@pgs-youtube-app" -d postgres -c "SELECT 1;"
```

### Test 2: Create .pgpass file
1. Create directory: `mkdir "%APPDATA%\postgresql"`
2. Create file: `"%APPDATA%\postgresql\pgpass.conf"`
3. Add line:
   ```
   pgs-youtube-app.postgres.database.azure.com:5432:*:pgadmina@pgs-youtube-app:Centurylink@123
   ```
4. Test:
   ```cmd
   psql -h pgs-youtube-app.postgres.database.azure.com -U "pgadmina@pgs-youtube-app" -d postgres -c "SELECT 1;"
   ```

## Update MCP Server to Use .pgpass

If `.pgpass` works, we can update the MCP server to create/update the `.pgpass` file automatically before running `pg_dump`/`pg_restore`/`psql`.

## Azure PostgreSQL Specific Notes

Azure PostgreSQL requires:
1. Username in format: `username@servername` ✅ (We have this)
2. SSL connection: `sslmode=require` ✅ (We have this)
3. Password might have special handling requirements

## Next Steps

1. Try creating `.pgpass` file manually
2. Test if `psql` works with `.pgpass`
3. If it works, update MCP server to use `.pgpass` approach
4. If it doesn't work, investigate Azure PostgreSQL specific requirements

## Alternative: Interactive Password Entry
As a last resort, the MCP server could use `pexpect` library (Python) to handle interactive password prompts, but this is less secure and more complex.
