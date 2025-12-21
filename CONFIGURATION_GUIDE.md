# PostgreSQL MCP Server - Configuration Guide

This guide explains how to integrate the PostgreSQL MCP Server with Claude Desktop, Claude Code CLI, and Visual Studio Code.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Claude Desktop Configuration](#claude-desktop-configuration)
- [Claude Code CLI Configuration](#claude-code-cli-configuration)
- [Visual Studio Code Configuration](#visual-studio-code-configuration)
- [Testing the Connection](#testing-the-connection)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

1. **Python 3.8+** installed
2. **PostgreSQL** database access
3. **Python virtual environment** set up:
   ```bash
   cd C:\Users\kusha\postgresql-mcp
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

4. **Environment variables** configured (see [Environment Setup](#environment-setup))

---

## Environment Setup

### 1. Create `.env` file

Copy `.env.example` to `.env` and configure your database connection:

```bash
cd C:\Users\kusha\postgresql-mcp
copy .env.example .env
```

### 2. Edit `.env` file

```ini
# PostgreSQL Database Connection
DATABASE_URL=postgresql://username:password@hostname:port/database?sslmode=require

# Example for local PostgreSQL
# DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/mydb

# Example for Azure PostgreSQL
# DATABASE_URL=postgresql://myuser%40myserver:mypassword@myserver.postgres.database.azure.com:5432/mydb?sslmode=require

# Optional: Default backup directory
DEFAULT_BACKUP_DIR=C:\Users\kusha\postgresql-mcp\backups
```

### 3. Verify Installation

Test that the server can start:

```bash
cd C:\Users\kusha\postgresql-mcp
.venv\Scripts\activate
python server.py
```

Press `Ctrl+C` to stop. If no errors appear, you're ready to configure clients.

---

## Authentication Methods

This MCP server supports two authentication methods:

### Method 1: Traditional PostgreSQL Authentication
- Uses username and password
- Standard PostgreSQL connection string
- Credentials stored in `DATABASE_URL`

### Method 2: EntraID (Azure AD) Authentication
- Uses Azure Active Directory tokens
- More secure - no passwords stored
- Automatic token refresh
- Supports multiple credential types:
  - Managed Identity (recommended for Azure resources)
  - Service Principal
  - Azure CLI
  - Visual Studio Code

### Choosing an Authentication Method

Set the `AUTH_TYPE` environment variable in your `.env` file:
- `AUTH_TYPE=postgresql` for traditional authentication
- `AUTH_TYPE=entraid` for EntraID/Azure AD authentication

---

## Setting Up EntraID Authentication

If you're using Azure PostgreSQL, EntraID authentication is recommended for better security.

### Prerequisites for EntraID

1. **Azure PostgreSQL Flexible Server** (required for EntraID auth)
2. **Azure Active Directory Admin** configured on your PostgreSQL server
3. **One of the following:**
   - Azure Managed Identity (for Azure VMs, App Services, Container Apps)
   - Azure AD Service Principal (for applications)
   - Azure CLI authentication (for local development)

### Step 1: Enable Azure AD on PostgreSQL

1. Go to your Azure PostgreSQL Flexible Server in Azure Portal
2. Navigate to **Settings > Authentication**
3. Enable **Azure Active Directory authentication**
4. Set an Azure AD admin (can be a user or group)
5. Save changes

### Step 2: Grant Database Permissions

Connect to your PostgreSQL database and grant permissions:

```sql
-- For a Service Principal or Managed Identity:
SELECT * FROM pgaadauth_create_principal('<app-name or object-id>', false, false);

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE mydatabase TO "<app-name>";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "<app-name>";
```

### Step 3: Configure Environment Variables

#### Option A: Using Managed Identity (Recommended for Azure)

```ini
# .env file
AUTH_TYPE=entraid

# PostgreSQL connection details
PG_HOST=myserver.postgres.database.azure.com
PG_PORT=5432
PG_DATABASE=mydatabase
PG_USER=myapp
PG_SSLMODE=require

# No Azure credentials needed - Managed Identity will be used automatically
```

#### Option B: Using Service Principal

1. Create an App Registration in Azure AD
2. Create a client secret
3. Grant the service principal access to PostgreSQL

```ini
# .env file
AUTH_TYPE=entraid

# PostgreSQL connection details
PG_HOST=myserver.postgres.database.azure.com
PG_PORT=5432
PG_DATABASE=mydatabase
PG_USER=myapp
PG_SSLMODE=require

# Azure AD credentials
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

#### Option C: Using Azure CLI (Local Development)

1. Run `az login` first
2. Configure the environment:

```ini
# .env file
AUTH_TYPE=entraid

# PostgreSQL connection details
PG_HOST=myserver.postgres.database.azure.com
PG_PORT=5432
PG_DATABASE=mydatabase
PG_USER=your-email@domain.com
PG_SSLMODE=require

# No Azure credentials needed - Azure CLI credentials will be used
```

### Step 4: Test Authentication

After configuration, you can test the authentication:

```bash
cd C:\Users\kusha\postgresql-mcp
.venv\Scripts\activate
python server.py
```

The server will log which authentication method is being used. You can also use the new `get_authentication_info` tool to verify your setup.

---

## Claude Desktop Configuration

### Location of Config File

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```
Full path: `C:\Users\kusha\AppData\Roaming\Claude\claude_desktop_config.json`

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Configuration

1. **Open or create** `claude_desktop_config.json`

2. **Add the PostgreSQL MCP server:**

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\kusha\\postgresql-mcp\\server.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql://username:password@hostname:port/database?sslmode=require"
      }
    }
  }
}
```

### Alternative: Using .env file (Recommended)

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\kusha\\postgresql-mcp\\server.py"
      ],
      "cwd": "C:\\Users\\kusha\\postgresql-mcp"
    }
  }
}
```
*This method reads from your `.env` file automatically.*

### Using EntraID Authentication with Claude Desktop

For EntraID authentication, you can configure it in your `.env` file and reference it:

```json
{
  "mcpServers": {
    "postgresql-entraid": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\kusha\\postgresql-mcp\\server.py"
      ],
      "cwd": "C:\\Users\\kusha\\postgresql-mcp",
      "env": {
        "AUTH_TYPE": "entraid",
        "PG_HOST": "myserver.postgres.database.azure.com",
        "PG_PORT": "5432",
        "PG_DATABASE": "mydatabase",
        "PG_USER": "myapp",
        "PG_SSLMODE": "require"
      }
    }
  }
}
```

For Service Principal authentication, add Azure credentials:

```json
{
  "mcpServers": {
    "postgresql-entraid": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\kusha\\postgresql-mcp\\server.py"
      ],
      "cwd": "C:\\Users\\kusha\\postgresql-mcp",
      "env": {
        "AUTH_TYPE": "entraid",
        "PG_HOST": "myserver.postgres.database.azure.com",
        "PG_PORT": "5432",
        "PG_DATABASE": "mydatabase",
        "PG_USER": "myapp",
        "PG_SSLMODE": "require",
        "AZURE_TENANT_ID": "your-tenant-id",
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

### 4. Verify in Claude Desktop

In a new conversation, you should see the MCP tools icon. Try:
```
Can you list all the database tools available?
```

---

## Claude Code CLI Configuration

Claude Code automatically detects MCP servers configured in `claude_desktop_config.json`.

### Method 1: Use Claude Desktop Config (Easiest)

If you've already configured Claude Desktop, Claude Code will automatically use the same configuration.

### Method 2: Project-Specific Configuration

Create `.claude/mcp.json` in your project:

```bash
cd C:\Users\kusha\postgresql-mcp
mkdir .claude
```

Create `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\kusha\\postgresql-mcp\\server.py"
      ],
      "cwd": "C:\\Users\\kusha\\postgresql-mcp"
    }
  }
}
```

### Using Claude Code

1. **Start Claude Code** in your project:
   ```bash
   cd your-project-folder
   claude
   ```

2. **Test the MCP connection:**
   ```
   You: Can you connect to the PostgreSQL database and list all databases?
   ```

3. **Run queries:**
   ```
   You: Execute this query: SELECT * FROM users LIMIT 5;
   ```

---

## Visual Studio Code Configuration

### Option 1: Using Claude Code Extension

If you have the Claude Code extension for VS Code:

1. **Install the extension** (if not already installed)
2. **Configure MCP** using one of the methods above
3. **Open Command Palette** (`Ctrl+Shift+P` / `Cmd+Shift+P`)
4. **Type:** "Claude: Start Session"

### Option 2: Using Integrated Terminal

1. **Open VS Code**
2. **Open integrated terminal** (`` Ctrl+` ``)
3. **Navigate to your project:**
   ```bash
   cd C:\Users\kusha\postgresql-mcp
   ```
4. **Activate virtual environment:**
   ```bash
   .venv\Scripts\activate
   ```
5. **Start Claude Code:**
   ```bash
   claude
   ```

### Option 3: VS Code Tasks

Create `.vscode/tasks.json` in your project:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start PostgreSQL MCP Server",
      "type": "shell",
      "command": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
      "args": [
        "${workspaceFolder}\\server.py"
      ],
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

**Run the task:**
- Press `Ctrl+Shift+P`
- Type "Tasks: Run Task"
- Select "Start PostgreSQL MCP Server"

---

## Testing the Connection

### Test 0: Check Authentication Info

**In Claude Desktop or Claude Code:**
```
Can you show me the authentication information for the PostgreSQL connection?
```

**Expected response:**
- Authentication type (postgresql or entraid)
- Connection details
- For EntraID: token-based authentication status

### Test 1: List Available Tools

**In Claude Desktop or Claude Code:**
```
Can you list all the PostgreSQL database tools available to you?
```

**Expected response:** List of 20 tools including:
- execute_select
- execute_insert
- execute_update
- execute_delete
- execute_create_table
- create_database
- backup_database
- get_authentication_info
- etc.

### Test 2: List Databases

```
Can you list all databases on the PostgreSQL server?
```

### Test 3: Execute a Simple Query

```
Execute this SQL query: SELECT version();
```

### Test 4: Get Schema Information

```
Can you show me the schema information for the 'public' schema?
```

### Test 5: Create and Query a Test Table

```
1. Create a test table called 'test_users' with columns: id (serial), name (varchar), email (varchar)
2. Insert 3 sample records
3. Query all records from the table
4. Drop the test table
```

---

## Troubleshooting

### Issue 1: "Cannot connect to database"

**Check:**
- Is PostgreSQL running?
- Is `DATABASE_URL` correct in `.env`?
- Can you connect with `psql` or another client?

**Test connection:**
```bash
cd C:\Users\kusha\postgresql-mcp
.venv\Scripts\activate
python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('your_database_url_here'))"
```

### Issue 2: "MCP Server not found"

**Check:**
- Path to Python executable is correct
- Path to `server.py` is correct
- Use absolute paths (not relative)

**Verify paths:**
```bash
# Find Python path
where python

# Should output something like:
# C:\Users\kusha\postgresql-mcp\.venv\Scripts\python.exe
```

### Issue 3: "Module not found" errors

**Install dependencies:**
```bash
cd C:\Users\kusha\postgresql-mcp
.venv\Scripts\activate
pip install -r requirements.txt
```

### Issue 4: Claude Desktop doesn't show tools

**Steps:**
1. Close Claude Desktop completely
2. Check config file syntax (use JSONLint.com)
3. Verify all paths use double backslashes `\\` on Windows
4. Restart Claude Desktop
5. Wait 10-15 seconds for MCP to initialize
6. Look for MCP tools icon in the chat interface

### Issue 5: Permission Denied

**Windows:**
```bash
# Ensure .venv\Scripts\python.exe is executable
icacls ".venv\Scripts\python.exe" /grant Everyone:RX
```

**Linux/Mac:**
```bash
chmod +x .venv/bin/python
chmod +x server.py
```

### Issue 6: SSL/TLS Certificate Errors (Azure PostgreSQL)

Add SSL mode to your DATABASE_URL:
```
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

For stricter SSL:
```
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=verify-full&sslrootcert=/path/to/ca-cert.pem
```

---

## Advanced Configuration

### Using Multiple Databases

Configure multiple MCP servers for different databases:

```json
{
  "mcpServers": {
    "postgresql-production": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\kusha\\postgresql-mcp\\server.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@prod-server:5432/proddb"
      }
    },
    "postgresql-development": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\kusha\\postgresql-mcp\\server.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@dev-server:5432/devdb"
      }
    }
  }
}
```

### Custom Backup Directory

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\kusha\\postgresql-mcp\\server.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@host:5432/db",
        "DEFAULT_BACKUP_DIR": "C:\\Users\\kusha\\backups\\postgresql"
      }
    }
  }
}
```

### Enable Debug Logging

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "C:\\Users\\kusha\\postgresql-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\kusha\\postgresql-mcp\\server.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@host:5432/db",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

---

## Example Usage in Claude

Once configured, you can interact naturally:

### Example 1: Data Analysis
```
Can you analyze the users table and show me:
1. Total number of users
2. Users created in the last 30 days
3. Top 5 most active users by login count
```

### Example 2: Database Maintenance
```
I need to:
1. Create a backup of the 'sales' database
2. Create a new table for quarterly reports
3. Migrate data from the old reports table
4. Verify the migration was successful
```

### Example 3: Complex Queries
```
Show me the total revenue by product category for the last quarter,
including the average order value and number of orders.
Use a LEFT JOIN with the products and categories tables.
```

---

## Security Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use read-only database users** when possible
3. **Enable SSL/TLS** for remote connections
4. **Use parameterized queries** (the server does this automatically)
5. **Limit database permissions** - Don't use superuser accounts
6. **Rotate credentials** regularly
7. **Monitor query logs** for suspicious activity

---

## Getting Help

- **GitHub Issues:** Report bugs or request features
- **Documentation:** Check README.md for server-specific details
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **MCP Documentation:** https://modelcontextprotocol.io/

---

## Quick Reference

### Config File Locations

| Platform | Claude Desktop Config |
|----------|----------------------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

### Common Commands

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source .venv/bin/activate

# Run server directly
python server.py

# Test database connection
python -c "import asyncpg, asyncio; asyncio.run(asyncpg.connect('DATABASE_URL'))"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `DEFAULT_BACKUP_DIR` | Default backup folder | `C:\Users\kusha\backups` |
| `LOG_LEVEL` | Logging verbosity | `INFO`, `DEBUG`, `ERROR` |

---

**You're all set! 🚀** Start using your PostgreSQL MCP Server with Claude Desktop, Claude Code, and VS Code.
