# MCP Server Setup Guide - Complete Instructions

## Current Status
✅ Python dependencies installed
✅ Database connection verified
✅ Configuration file created

## Next Steps to Use with Claude Desktop

### Step 1: Locate Your Claude Desktop Config File

The config file location depends on your operating system:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

To open this folder:
1. Press `Win + R`
2. Type: `%APPDATA%\Claude`
3. Press Enter

**Full path example:**
```
C:\Users\kusha\AppData\Roaming\Claude\claude_desktop_config.json
```

---

### Step 2: Edit Claude Desktop Config

1. **Open the config file** (create it if it doesn't exist)
2. **Copy the contents** from the file I created at:
   ```
   C:\Users\kusha\postgresql-mcp\claude_desktop_config.json
   ```

3. **Or manually add this configuration:**

```json
{
  "mcpServers": {
    "postgres-enterprise": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\kusha\\postgresql-mcp\\mcp_server_enterprise.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql://pgadmina:Centurylink%40123@pgs-youtube-app.postgres.database.azure.com:5432/postgres?sslmode=require"
      }
    }
  }
}
```

**Important Notes:**
- Use double backslashes (`\\`) in Windows paths
- The `%40` in the DATABASE_URL is the URL-encoded version of `@` in the password
- Make sure the JSON is valid (no trailing commas, proper brackets)

---

### Step 3: Restart Claude Desktop

1. **Completely close** Claude Desktop (check system tray)
2. **Restart** Claude Desktop
3. Wait a few seconds for it to initialize

---

### Step 4: Verify MCP Server is Connected

In Claude Desktop, you should see:
- A small icon or indicator showing MCP servers are connected
- When you type a message, Claude can now use database tools

---

## How to Use the MCP Server in Claude Desktop

Once connected, you can ask Claude to interact with your PostgreSQL database:

### Example Commands

#### Query Data (SELECT)
```
"Show me all tables in the database"
"List the first 10 rows from the users table"
"Find all records where status is 'active'"
```

#### Insert Data (INSERT)
```
"Add a new user: username='john_doe', email='john@example.com', age=30"
"Insert 3 products into the products table"
```

#### Update Data (UPDATE)
```
"Update the email to 'newemail@example.com' for user id 5"
"Change status to 'inactive' for all users older than 60"
```

#### Delete Data (DELETE)
```
"Delete the user with id 10"
"Remove all records where created_at is older than 2020"
```

#### Create Tables (DDL)
```
"Create a table called 'habits' with columns: id (serial primary key), name (varchar 100), frequency (varchar 20), created_at (timestamp)"
```

#### Alter Tables (DDL)
```
"Add a 'description' column to the habits table"
"Add an index on the email column in users table"
```

#### Drop Tables (DDL)
```
"Drop the temporary_test table"
```

#### Transactions
```
"Insert a new order and add 3 items to it, all in a single transaction"
```

#### Schema Information
```
"Show me the structure of the users table"
"List all columns in the orders table with their data types"
```

---

## Testing the Integration

### Test 1: List Tables
Ask Claude:
```
"What tables exist in my PostgreSQL database?"
```

### Test 2: Create a Test Table
Ask Claude:
```
"Create a test table called 'test_mcp' with columns: id (serial), name (varchar 50), created_at (timestamp default now)"
```

### Test 3: Insert Data
Ask Claude:
```
"Insert 2 test records into the test_mcp table"
```

### Test 4: Query Data
Ask Claude:
```
"Show me all data from the test_mcp table"
```

### Test 5: Cleanup
Ask Claude:
```
"Drop the test_mcp table"
```

---

## Troubleshooting

### Issue: "MCP server not showing up in Claude Desktop"

**Solutions:**
1. Check the config file path is correct for your OS
2. Verify JSON syntax is valid (use https://jsonlint.com)
3. Make sure you completely restarted Claude Desktop
4. Check Claude Desktop logs for errors

### Issue: "Database connection errors"

**Solutions:**
1. Verify DATABASE_URL in the config is correct
2. Test connection using: `python test_mcp_setup.py`
3. Check if your IP is allowed in Azure PostgreSQL firewall
4. Verify credentials are correct

### Issue: "Python not found"

**Solutions:**
1. Use the full path to Python in the virtual environment
2. Current config uses: `C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe`
3. Verify this file exists

### Issue: "Module not found errors"

**Solutions:**
1. Make sure you installed dependencies: `.venv/Scripts/pip install -r requirements.txt`
2. Verify mcp and asyncpg are installed
3. Activate the virtual environment and check: `pip list`

---

## Security Best Practices

### 1. Restrict Database User Permissions

Create a dedicated database user for MCP:

```sql
-- Connect to your database
-- Create dedicated user
CREATE USER mcp_user WITH PASSWORD 'secure_password_here';

-- Grant specific permissions (adjust as needed)
GRANT CONNECT ON DATABASE postgres TO mcp_user;
GRANT USAGE ON SCHEMA public TO mcp_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mcp_user;
GRANT CREATE ON SCHEMA public TO mcp_user;  -- Only if you need DDL operations

-- For existing tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mcp_user;
```

### 2. Use Environment Variables

Instead of hardcoding DATABASE_URL in the config, you can:
1. Keep it in the `.env` file
2. Reference it in the MCP server code
3. The server will load it automatically

### 3. Enable Audit Logging

Monitor what queries are being executed:
- Enable PostgreSQL query logging
- Review logs regularly
- Set up alerts for DROP/TRUNCATE operations

---

## Advanced Configuration

### Multiple Databases

You can connect to multiple databases:

```json
{
  "mcpServers": {
    "postgres-production": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\kusha\\postgresql-mcp\\mcp_server_enterprise.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@host:5432/production?sslmode=require"
      }
    },
    "postgres-development": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\kusha\\postgresql-mcp\\mcp_server_enterprise.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@host:5432/development?sslmode=require"
      }
    }
  }
}
```

---

## Available MCP Tools

Your MCP server provides these tools to Claude:

1. **execute_select** - Query data (SELECT)
2. **execute_insert** - Add new records (INSERT)
3. **execute_update** - Modify records (UPDATE)
4. **execute_delete** - Remove records (DELETE)
5. **execute_create_table** - Create new tables
6. **execute_alter_table** - Modify table structure
7. **execute_drop_table** - Delete tables
8. **execute_create_index** - Create indexes
9. **execute_drop_index** - Remove indexes
10. **execute_transaction** - Run multiple statements atomically
11. **get_schema_info** - View database schema
12. **get_table_info** - Get table details
13. **execute_raw_sql** - Run any SQL command

---

## Support & Documentation

- **Full Documentation**: See `MCP_README.md`
- **Test Client**: Run `python mcp_client_enterprise.py` for examples
- **Connection Test**: Run `python test_mcp_setup.py`

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│  CLAUDE DESKTOP MCP SERVER - QUICK REFERENCE           │
├─────────────────────────────────────────────────────────┤
│  Config File: %APPDATA%\Claude\claude_desktop_config.json│
│  Server Path: C:\Users\kusha\postgresql-mcp\mcp_server_enterprise.py│
│  Test Script: python test_mcp_setup.py                 │
│  Test Client: python mcp_client_enterprise.py          │
├─────────────────────────────────────────────────────────┤
│  Usage: Just ask Claude to interact with your database │
│  Example: "Show me all tables"                         │
│  Example: "Create a users table"                       │
│  Example: "Insert a new record"                        │
└─────────────────────────────────────────────────────────┘
```

---

## Ready to Use!

Your MCP server is now ready. Follow Step 2 above to configure Claude Desktop, then restart it and start using natural language to interact with your PostgreSQL database!
