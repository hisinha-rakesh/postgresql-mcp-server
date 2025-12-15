# Quick Test Reference - PostgreSQL Utilities

## All Tests Passed ✓

---

## Quick Verification Commands

### Test psql
```bash
psql "host=pgs-youtube-app.postgres.database.azure.com port=5432 user=pgadmina dbname=postgres sslmode=require" -c "SELECT 'OK';"
```
**Expected**: Should return "OK" without asking for password

### Test pg_dump
```bash
pg_dump -h pgs-youtube-app.postgres.database.azure.com -U pgadmina -d library -F c -f test.dump
```
**Expected**: Should create test.dump without asking for password

### Test pg_restore
```bash
pg_restore --list test.dump
```
**Expected**: Should list backup contents

### Test asyncpg (Python)
```bash
python test_asyncpg.py
```
**Expected**: Should print "PASS: asyncpg connection works"

---

## Configuration Files

### .env (This Directory)
```env
DATABASE_URL=postgresql://pgadmina:XXXXXXX%40123@pgs-youtube-app.postgres.database.azure.com:5432/postgres?sslmode=require
```
**Key**: Username is `pgadmina` (NOT `pgadmina@pgs-youtube-app`)

### .pgpass (C:\Users\kusha\AppData\Roaming\postgresql\pgpass.conf)
```
pgs-youtube-app.postgres.database.azure.com:5432:*:pgadmina:Centurylink@123
```
**Key**: Password is plain text (NOT URL-encoded)

---

## Test Results Summary

| Test | Status | Tool |
|------|--------|------|
| psql connection | ✓ PASS | psql |
| pg_dump backup | ✓ PASS | pg_dump |
| pg_restore read | ✓ PASS | pg_restore |
| asyncpg connection | ✓ PASS | Python asyncpg |

---

## MCP Server Status

**File**: `c:\Users\kusha\postgresql-mcp\mcp_server_enterprise.py`

**Status**: ✓ READY TO USE

**Features Working**:
- ✓ backup_database
- ✓ restore_database
- ✓ execute_select
- ✓ execute_insert
- ✓ execute_update
- ✓ execute_delete
- ✓ execute_create_table
- ✓ create_database
- ✓ drop_database
- ✓ list_databases

---

## Try in Claude Desktop

After restarting Claude Desktop, try:

```
"List all databases"
```

```
"Backup the library database to C:\Agentic-RAG"
```

```
"Show me all tables in the library database"
```

All should work without password prompts!

---

## Troubleshooting

If something stops working:

1. **Check .env file**:
   - Username should be `pgadmina` (not `pgadmina@pgs-youtube-app`)

2. **Check .pgpass file**:
   - Location: `C:\Users\kusha\AppData\Roaming\postgresql\pgpass.conf`
   - Username should match .env (pgadmina)
   - Password should be plain text

3. **Test tools manually**:
   ```bash
   psql --version
   pg_dump --version
   pg_restore --version
   ```

4. **Re-run tests**:
   ```bash
   python test_asyncpg.py
   ```

---

Last Updated: 2025-12-07
Status: All tests passing ✓
