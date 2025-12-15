# Enterprise PostgreSQL MCP Server

A production-grade Model Context Protocol (MCP) server for PostgreSQL with complete DDL, DML, and TCL support. This server enables Claude Desktop and other MCP-compatible clients to perform full database operations through natural language.

## Features

### Data Manipulation Language (DML)
- **SELECT** - Query and retrieve data with complex JOINs, aggregations, and filters
- **INSERT** - Add new records with RETURNING clause support
- **UPDATE** - Modify existing records with parameterized queries
- **DELETE** - Remove records with WHERE clause filtering

### Data Definition Language (DDL)
- **CREATE TABLE** - Create new tables with constraints and indexes
- **ALTER TABLE** - Modify table structure (add/drop columns, constraints)
- **DROP TABLE** - Remove tables with CASCADE and IF EXISTS options
- **CREATE INDEX** - Create indexes for performance optimization
- **DROP INDEX** - Remove indexes from the database

### Transaction Control Language (TCL)
- **TRANSACTIONS** - Execute multiple statements atomically
- **ISOLATION LEVELS** - Support for all PostgreSQL isolation levels
- **ROLLBACK** - Automatic rollback on error

### Utility Operations
- **Schema Inspection** - View all tables, columns, and constraints
- **Table Information** - Detailed table metadata and statistics
- **Raw SQL Execution** - Execute any SQL for advanced use cases

## Installation

### 1. Install Python Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require
```

Example for Azure PostgreSQL:
```env
DATABASE_URL=postgresql://pgadmina:XXXXXXXXX@123@pgs-youtube-app.postgres.database.azure.com:5432/habittracker?sslmode=require
```

### 3. Test the Server Standalone

```bash
# Run the MCP client to test all functionality
python mcp_client_enterprise.py
```

## Claude Desktop Configuration

To use this MCP server with Claude Desktop, add it to your Claude configuration file:

### Windows
Edit: `%APPDATA%\Claude\claude_desktop_config.json`

### macOS
Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Linux
Edit: `~/.config/Claude/claude_desktop_config.json`

### Configuration Format

```json
{
  "mcpServers": {
    "postgres-habittracker": {
      "command": "python",
      "args": [
        "C:\\Users\\kusha\\postgresql-mcp\\mcp_server_enterprise.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql://pgadmina:XXXXXXXXXXX@123@pgs-youtube-app.postgres.database.azure.com:5432/habittracker?sslmode=require"
      }
    }
  }
}
```

**Important Notes:**
- Use absolute paths for the Python script
- On Windows, use double backslashes (`\\`) in paths
- Include the `DATABASE_URL` in the `env` section
- Restart Claude Desktop after making changes

## Available Tools in Claude Desktop

Once configured, you can ask Claude to perform database operations:

### Query Examples

**SELECT Queries:**
```
"Show me all tables in the database"
"Get all users where age > 25"
"Find the top 10 orders by total amount"
```

**INSERT Operations:**
```
"Add a new user with username 'john_doe', email 'john@example.com', and age 30"
"Insert multiple products into the products table"
```

**UPDATE Operations:**
```
"Update the user's email to 'newemail@example.com' where username is 'john_doe'"
"Set all inactive users' status to 'archived'"
```

**DELETE Operations:**
```
"Delete the user with id 5"
"Remove all orders older than 2020"
```

**CREATE TABLE:**
```
"Create a new table called 'products' with columns: id (serial primary key), name (varchar), price (decimal)"
```

**ALTER TABLE:**
```
"Add a 'description' column to the products table"
"Add a unique constraint on the email column in users table"
```

**DROP TABLE:**
```
"Drop the temporary_data table"
```

**TRANSACTIONS:**
```
"Create a new order and add 3 items to it, all in a single transaction"
```

**SCHEMA INSPECTION:**
```
"Show me the structure of the users table"
"List all tables and their columns"
```

## Tool Reference

### DML Tools

#### execute_select
Execute SELECT queries to retrieve data.

**Parameters:**
- `query` (string, required): The SELECT SQL query
- `params` (array, optional): Parameterized values for $1, $2, etc.

**Example:**
```json
{
  "query": "SELECT * FROM users WHERE age > $1",
  "params": [25]
}
```

#### execute_insert
Insert new records into a table.

**Parameters:**
- `query` (string, required): The INSERT SQL query
- `params` (array, optional): Parameterized values

**Example:**
```json
{
  "query": "INSERT INTO users (username, email) VALUES ($1, $2) RETURNING id",
  "params": ["john_doe", "john@example.com"]
}
```

#### execute_update
Update existing records.

**Parameters:**
- `query` (string, required): The UPDATE SQL query
- `params` (array, optional): Parameterized values

**Example:**
```json
{
  "query": "UPDATE users SET email = $1 WHERE id = $2",
  "params": ["newemail@example.com", 5]
}
```

#### execute_delete
Delete records from a table.

**Parameters:**
- `query` (string, required): The DELETE SQL query
- `params` (array, optional): Parameterized values

**Example:**
```json
{
  "query": "DELETE FROM users WHERE id = $1",
  "params": [5]
}
```

### DDL Tools

#### execute_create_table
Create a new table.

**Parameters:**
- `query` (string, required): The CREATE TABLE SQL statement

**Example:**
```json
{
  "query": "CREATE TABLE products (id SERIAL PRIMARY KEY, name VARCHAR(100), price DECIMAL(10,2))"
}
```

#### execute_alter_table
Modify an existing table structure.

**Parameters:**
- `query` (string, required): The ALTER TABLE SQL statement

**Example:**
```json
{
  "query": "ALTER TABLE products ADD COLUMN description TEXT"
}
```

#### execute_drop_table
Drop a table from the database.

**Parameters:**
- `table_name` (string, required): Name of the table to drop
- `cascade` (boolean, optional): Drop dependent objects too
- `if_exists` (boolean, optional): Don't error if table doesn't exist

**Example:**
```json
{
  "table_name": "temporary_data",
  "cascade": true,
  "if_exists": true
}
```

#### execute_create_index
Create an index on a table.

**Parameters:**
- `query` (string, required): The CREATE INDEX SQL statement

**Example:**
```json
{
  "query": "CREATE INDEX idx_users_email ON users(email)"
}
```

#### execute_drop_index
Remove an index.

**Parameters:**
- `index_name` (string, required): Name of the index to drop
- `if_exists` (boolean, optional): Don't error if index doesn't exist

**Example:**
```json
{
  "index_name": "idx_users_email",
  "if_exists": true
}
```

### TCL Tools

#### execute_transaction
Execute multiple statements in a transaction (all succeed or all fail).

**Parameters:**
- `statements` (array, required): Array of SQL statement objects
- `isolation_level` (string, optional): Transaction isolation level

**Example:**
```json
{
  "statements": [
    {
      "query": "INSERT INTO orders (user_id) VALUES ($1) RETURNING order_id",
      "params": [123]
    },
    {
      "query": "INSERT INTO order_items (order_id, product_id) VALUES (1, $1)",
      "params": [456]
    }
  ],
  "isolation_level": "read_committed"
}
```

### Utility Tools

#### get_schema_info
Get information about all tables in a schema.

**Parameters:**
- `schema_name` (string, optional): Schema name (default: "public")
- `include_system_schemas` (boolean, optional): Include pg_catalog, etc.

**Example:**
```json
{
  "schema_name": "public"
}
```

#### get_table_info
Get detailed information about a specific table.

**Parameters:**
- `table_name` (string, required): Name of the table
- `schema_name` (string, optional): Schema name (default: "public")

**Example:**
```json
{
  "table_name": "users",
  "schema_name": "public"
}
```

#### execute_raw_sql
Execute any raw SQL statement.

**Parameters:**
- `query` (string, required): The SQL query to execute
- `params` (array, optional): Parameterized values

**Example:**
```json
{
  "query": "VACUUM ANALYZE users"
}
```

## Security Considerations

This MCP server has **full database access** including destructive operations. Follow these best practices:

### 1. Database User Permissions
Create a dedicated database user with minimal required permissions:

```sql
-- Create a dedicated user
CREATE USER mcp_user WITH PASSWORD 'secure_password';

-- Grant only necessary permissions
GRANT CONNECT ON DATABASE your_database TO mcp_user;
GRANT USAGE ON SCHEMA public TO mcp_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mcp_user;

-- For DDL operations (only if needed)
GRANT CREATE ON SCHEMA public TO mcp_user;
```

### 2. Network Security
- Use SSL/TLS connections (`sslmode=require`)
- Restrict database access by IP address
- Use Azure Private Link or VPN for cloud databases

### 3. Environment Variables
- Never commit `.env` files to version control
- Use secret management tools (Azure Key Vault, AWS Secrets Manager)
- Rotate credentials regularly

### 4. Monitoring
- Enable PostgreSQL logging
- Monitor for unusual query patterns
- Set up alerts for DDL operations

### 5. Backup Strategy
- Maintain regular database backups
- Test backup restoration regularly
- Use point-in-time recovery when available

## Troubleshooting

### Connection Issues

**Problem:** "Failed to connect to database"
- Verify `DATABASE_URL` is correct
- Check if database accepts connections from your IP
- Ensure SSL mode is configured correctly
- Test connection with `psql` or pgAdmin first

### Claude Desktop Integration

**Problem:** "MCP server not appearing in Claude Desktop"
- Restart Claude Desktop after config changes
- Check config file path is correct for your OS
- Verify JSON syntax is valid
- Check Claude Desktop logs for errors

**Problem:** "Tool execution fails"
- Check Python is in system PATH
- Verify all dependencies are installed
- Check `.env` file is in the same directory as the script
- Look at server logs (stderr) for error messages

### Permission Issues

**Problem:** "Permission denied" errors
- Verify database user has required permissions
- Check schema access permissions
- Ensure table-level permissions are granted

## Development

### Running Tests

```bash
# Run the test client
python mcp_client_enterprise.py
```

### Adding Custom Tools

Edit `mcp_server_enterprise.py` and add new tools to the `list_tools()` function:

```python
Tool(
    name="your_custom_tool",
    description="Description of what your tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Parameter description"}
        },
        "required": ["param1"]
    }
)
```

Then add a handler function:

```python
async def handle_your_custom_tool(arguments: dict) -> dict:
    # Your implementation
    pass
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           Claude Desktop / MCP Client        │
│                                             │
│  - Natural language interface               │
│  - Tool discovery & invocation              │
└────────────────┬────────────────────────────┘
                 │ MCP Protocol (stdio)
                 │
┌────────────────▼────────────────────────────┐
│      MCP Server (mcp_server_enterprise.py)  │
│                                             │
│  - Tool registration                        │
│  - Request routing                          │
│  - Connection pooling                       │
│  - Error handling                           │
└────────────────┬────────────────────────────┘
                 │ asyncpg
                 │
┌────────────────▼────────────────────────────┐
│         PostgreSQL Database                 │
│                                             │
│  - Data storage                             │
│  - Query execution                          │
│  - Transaction management                   │
└─────────────────────────────────────────────┘
```

## License

MIT License - feel free to use and modify for your needs.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review Claude Desktop documentation
- Open an issue on GitHub

## Comparison with Standard MCP PostgreSQL Server

| Feature | Standard @modelcontextprotocol/server-postgres | This Enterprise Server |
|---------|-----------------------------------------------|----------------------|
| SELECT queries | ✅ Yes | ✅ Yes |
| INSERT operations | ❌ No | ✅ Yes |
| UPDATE operations | ❌ No | ✅ Yes |
| DELETE operations | ❌ No | ✅ Yes |
| CREATE TABLE | ❌ No | ✅ Yes |
| ALTER TABLE | ❌ No | ✅ Yes |
| DROP TABLE | ❌ No | ✅ Yes |
| Transactions | ❌ No | ✅ Yes |
| Parameterized queries | ✅ Yes | ✅ Yes |
| Schema inspection | ✅ Yes | ✅ Yes |
| Connection pooling | ❌ No | ✅ Yes |
| Custom isolation levels | ❌ No | ✅ Yes |

This server provides **full database control** compared to the read-only standard MCP PostgreSQL server.
