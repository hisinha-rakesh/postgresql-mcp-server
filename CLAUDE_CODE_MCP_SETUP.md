# Claude Code MCP Server Configuration

## ✅ Global MCP Servers Configured

All MCP servers are now configured **globally** in your home directory (`C:\Users\kusha`), making them available across **all projects** when you run Claude Code.

---

## Configured MCP Servers

### 1. Terraform Registry
**Purpose**: Terraform module documentation and registry access

**Configuration**:
```json
{
  "command": "npx",
  "args": ["-y", "terraform-mcp-server"]
}
```

**Usage**: Ask Claude about Terraform modules and configurations

---

### 2. Filesystem
**Purpose**: Read/write file operations, directory browsing

**Configuration**:
```json
{
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-filesystem",
    "C:\\Users\\kusha"
  ]
}
```

**Capabilities**:
- Read files
- Write/create files
- List directories
- Search files
- Move/delete files

**Access**: Full access to `C:\Users\kusha` directory

---

### 3. PostgreSQL Enterprise ⭐
**Purpose**: Advanced PostgreSQL database management

**Configuration**:
```json
{
  "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
  "args": ["C:\\Users\\kusha\\postgresql-mcp\\mcp_server_enterprise.py"],
  "env": {
    "DATABASE_URL": "postgresql://pgadmina:Centurylink%40123@pgs-youtube-app.postgres.database.azure.com:5432/postgres?sslmode=require"
  }
}
```

**Features**:
- ✅ Database backups (pg_dump)
- ✅ Database restores (pg_restore/psql)
- ✅ Query execution (SELECT, INSERT, UPDATE, DELETE)
- ✅ Schema management (CREATE TABLE, ALTER TABLE, DROP TABLE)
- ✅ Database administration (CREATE DATABASE, DROP DATABASE, LIST DATABASES)
- ✅ Automatic password authentication (no prompts)
- ✅ SSL/TLS support for Azure PostgreSQL
- ✅ Support for specifying target database for operations

**Connection Details**:
- **Server**: Azure PostgreSQL (pgs-youtube-app.postgres.database.azure.com)
- **Port**: 5432
- **Username**: pgadmina
- **SSL**: Required
- **Default Database**: postgres

**Authentication**:
- Password stored in `.pgpass` file: `C:\Users\kusha\AppData\Roaming\postgresql\pgpass.conf`
- No password prompts needed

---

## Configuration Location

**File**: `C:\Users\kusha\.claude.json`

**Section**: Under `projects["C:\\Users\\kusha"]["mcpServers"]`

This makes all servers available when you run Claude Code from **any directory** under your home folder.

---

## How to Use

### Start Claude Code

From any directory:
```bash
claude
```

Or from a specific project:
```bash
cd C:\Users\kusha\postgresql-mcp
claude
```

### Check Available MCP Servers

```
/mcp
```

You should see:
- ✅ terraform-registry
- ✅ filesystem
- ✅ postgres-enterprise

### Example Commands

#### PostgreSQL Operations

**List databases**:
```
"List all databases on the server"
```

**Backup database**:
```
"Backup the library database to C:\Agentic-RAG"
```

**Query database**:
```
"Show all tables in the library database"
"Select all books from the books table in library database"
```

**Create table**:
```
"Create a users table in the youtube_db database with columns: id, name, email"
```

**Restore database**:
```
"Restore the library database from C:\Agentic-RAG\backup.dump"
```

#### Filesystem Operations

**List files**:
```
"List all Python files in my postgresql-mcp directory"
```

**Read file**:
```
"Read the contents of mcp_server_enterprise.py"
```

**Write file**:
```
"Create a new file called notes.txt with this content: ..."
```

#### Terraform Operations

```
"Tell me about the AWS VPC Terraform module"
"Show me documentation for terraform-aws-modules/vpc/aws"
```

---

## Testing

### Quick Test Script

Run this to verify everything is working:

```bash
cd C:\Users\kusha
claude
```

Then in Claude Code:
```
/mcp
```

Expected output:
```
Available MCP Servers:
  • terraform-registry
  • filesystem
  • postgres-enterprise
```

### Test PostgreSQL Connection

```
"List all databases"
```

Expected: Should list your databases without asking for password

### Test Filesystem Access

```
"List files in the postgresql-mcp directory"
```

Expected: Should list all files in that directory

---

## Troubleshooting

### MCP Server Not Showing Up

1. **Restart Claude Code** after configuration changes
2. **Check server status**:
   ```
   /mcp
   ```
3. **Check configuration file**: Verify `C:\Users\kusha\.claude.json` has correct structure

### PostgreSQL Authentication Issues

1. **Check .pgpass file exists**: `C:\Users\kusha\AppData\Roaming\postgresql\pgpass.conf`
2. **Verify password**: Should be `Centurylink@123` (not URL-encoded)
3. **Verify username**: Should be `pgadmina` (not `pgadmina@pgs-youtube-app`)
4. **Run test**:
   ```bash
   psql "host=pgs-youtube-app.postgres.database.azure.com port=5432 user=pgadmina dbname=postgres sslmode=require" -c "SELECT 1;"
   ```

### Python Virtual Environment Issues

If postgres-enterprise fails to start:
1. **Check Python path**: `C:\Users\kusha\postgresql-mcp\.venv\Scripts\python.exe` exists
2. **Check dependencies**:
   ```bash
   cd C:\Users\kusha\postgresql-mcp
   .venv\Scripts\activate
   pip list
   ```
   Should show: `mcp`, `asyncpg`, `python-dotenv`

---

## Benefits of Global Configuration

✅ **Available everywhere**: No need to reconfigure for each project
✅ **Consistent tools**: Same tools across all projects
✅ **Single source of truth**: One configuration file to maintain
✅ **Easy updates**: Update once, applies everywhere

---

## Important Files

| File | Purpose |
|------|---------|
| `C:\Users\kusha\.claude.json` | Claude Code configuration (MCP servers) |
| `C:\Users\kusha\AppData\Roaming\postgresql\pgpass.conf` | PostgreSQL password file |
| `C:\Users\kusha\postgresql-mcp\.env` | PostgreSQL MCP server environment variables |
| `C:\Users\kusha\postgresql-mcp\mcp_server_enterprise.py` | PostgreSQL MCP server script |

---

## Next Steps

1. ✅ Configuration complete
2. ✅ All MCP servers configured globally
3. 🎯 Start using Claude Code with MCP servers:
   ```bash
   claude
   ```
4. 🎯 Try some database operations:
   ```
   "List all databases"
   "Backup library to C:\Agentic-RAG"
   ```

---

## Summary

You now have **3 powerful MCP servers** configured globally:
1. **Terraform Registry** - For infrastructure documentation
2. **Filesystem** - For file operations
3. **PostgreSQL Enterprise** - For database management

All configured in: `C:\Users\kusha\.claude.json`

All available globally across all projects! 🎉
