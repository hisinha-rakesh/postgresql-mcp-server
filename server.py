#!/usr/bin/env python3
"""
Enterprise-Level MCP Server for PostgreSQL with Full DDL, DML, and TCL Support
Implements the Model Context Protocol (MCP) for database operations
"""

import os
import sys
import asyncio
import json
import logging
from typing import Any, Optional, Sequence
from contextlib import asynccontextmanager

import asyncpg
from dotenv import load_dotenv

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("mcp-postgres-server")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Backup configuration
DEFAULT_BACKUP_DIR = os.getenv("DEFAULT_BACKUP_DIR", os.path.join(os.getcwd(), "backups"))

# Global database pool
db_pool: Optional[asyncpg.Pool] = None


class DatabasePool:
    """Manages PostgreSQL connection pool"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize the connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        async with self.pool.acquire() as connection:
            yield connection


# Initialize database pool manager
db_manager = DatabasePool(DATABASE_URL)


# Helper function to get database connection
@asynccontextmanager
async def get_database_connection(database_name: Optional[str] = None):
    """Get a connection to the specified database or default database"""
    if database_name:
        import asyncpg
        import urllib.parse

        # Parse DATABASE_URL and replace the database name
        dsn_parts = DATABASE_URL.rsplit('/', 1)
        if len(dsn_parts) == 2:
            target_dsn = f"{dsn_parts[0]}/{database_name}"
        else:
            target_dsn = f"{DATABASE_URL}/{database_name}"

        # Create temporary connection to target database
        conn = await asyncpg.connect(target_dsn)
        try:
            yield conn
        finally:
            await conn.close()
    else:
        # Use default connection pool
        async with db_manager.acquire() as conn:
            yield conn


# Utility function to check if PostgreSQL client tools are available
def check_pg_tools_available():
    """Check if pg_dump, pg_restore, and psql are available in PATH"""
    import subprocess
    import shutil

    tools = {
        'pg_dump': shutil.which('pg_dump') is not None,
        'pg_restore': shutil.which('pg_restore') is not None,
        'psql': shutil.which('psql') is not None
    }

    return tools


# MCP Server instance
app = Server("postgres-enterprise-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available database operation tools"""
    return [
        # DML Operations (Data Manipulation Language)
        Tool(
            name="execute_select",
            description="Execute a SELECT query to retrieve data from the database. Supports complex queries with JOINs, WHERE clauses, aggregations, etc. Query will be executed on the database specified by database_name parameter or the default database from DATABASE_URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SELECT SQL query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional parameterized query values (use $1, $2, etc. in query)",
                        "items": {"type": ["string", "number", "boolean", "null"]}
                    },
                    "database_name": {
                        "type": "string",
                        "description": "Optional: Name of the database to query. If not specified, uses the database from DATABASE_URL."
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="execute_insert",
            description="Execute an INSERT statement to add new rows to a table. Supports single and bulk inserts with RETURNING clause.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The INSERT SQL query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional parameterized query values",
                        "items": {"type": ["string", "number", "boolean", "null"]}
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="execute_update",
            description="Execute an UPDATE statement to modify existing rows in a table. Use WHERE clause to target specific rows.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The UPDATE SQL query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional parameterized query values",
                        "items": {"type": ["string", "number", "boolean", "null"]}
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="execute_delete",
            description="Execute a DELETE statement to remove rows from a table. Use WHERE clause to target specific rows.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The DELETE SQL query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional parameterized query values",
                        "items": {"type": ["string", "number", "boolean", "null"]}
                    }
                },
                "required": ["query"]
            }
        ),

        # DDL Operations (Data Definition Language)
        Tool(
            name="execute_create_table",
            description="Execute a CREATE TABLE statement to create a new table with specified columns, constraints, and indexes. The table will be created in the database specified by database_name parameter or the default database from DATABASE_URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The CREATE TABLE SQL statement"
                    },
                    "database_name": {
                        "type": "string",
                        "description": "Optional: Name of the database where the table should be created. If not specified, uses the database from DATABASE_URL."
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="execute_alter_table",
            description="Execute an ALTER TABLE statement to modify table structure (add/drop columns, modify constraints, rename, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The ALTER TABLE SQL statement"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="execute_drop_table",
            description="Execute a DROP TABLE statement to permanently delete a table and all its data. Use with caution!",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The name of the table to drop"
                    },
                    "cascade": {
                        "type": "boolean",
                        "description": "If true, automatically drop objects that depend on the table",
                        "default": False
                    },
                    "if_exists": {
                        "type": "boolean",
                        "description": "If true, do not throw an error if the table doesn't exist",
                        "default": True
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="execute_create_index",
            description="Execute a CREATE INDEX statement to create an index on one or more columns for faster queries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The CREATE INDEX SQL statement"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="execute_drop_index",
            description="Execute a DROP INDEX statement to remove an index from the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "index_name": {
                        "type": "string",
                        "description": "The name of the index to drop"
                    },
                    "if_exists": {
                        "type": "boolean",
                        "description": "If true, do not throw an error if the index doesn't exist",
                        "default": True
                    }
                },
                "required": ["index_name"]
            }
        ),

        # TCL Operations (Transaction Control Language)
        Tool(
            name="execute_transaction",
            description="Execute multiple SQL statements within a transaction. All statements succeed or all fail (atomic operation).",
            inputSchema={
                "type": "object",
                "properties": {
                    "statements": {
                        "type": "array",
                        "description": "Array of SQL statements to execute in a transaction",
                        "items": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "params": {
                                    "type": "array",
                                    "items": {"type": ["string", "number", "boolean", "null"]}
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    "isolation_level": {
                        "type": "string",
                        "description": "Transaction isolation level",
                        "enum": ["read_uncommitted", "read_committed", "repeatable_read", "serializable"],
                        "default": "read_committed"
                    }
                },
                "required": ["statements"]
            }
        ),

        # Utility Operations
        Tool(
            name="get_schema_info",
            description="Get detailed schema information including all tables, columns, types, constraints, and indexes in the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema_name": {
                        "type": "string",
                        "description": "The schema name to inspect (default: public)",
                        "default": "public"
                    },
                    "include_system_schemas": {
                        "type": "boolean",
                        "description": "Include system schemas like pg_catalog",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="get_table_info",
            description="Get detailed information about a specific table including columns, constraints, indexes, and statistics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "The name of the table to inspect"
                    },
                    "schema_name": {
                        "type": "string",
                        "description": "The schema name (default: public)",
                        "default": "public"
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="execute_raw_sql",
            description="Execute any raw SQL statement. Use this for complex operations not covered by other tools. WARNING: Use with caution!",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional parameterized query values",
                        "items": {"type": ["string", "number", "boolean", "null"]}
                    }
                },
                "required": ["query"]
            }
        ),

        # Database Management Operations
        Tool(
            name="create_database",
            description="Create a new database on the PostgreSQL server. This operation requires explicit user consent. The database will be created with default settings unless specified otherwise.",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {
                        "type": "string",
                        "description": "The name of the database to create"
                    },
                    "owner": {
                        "type": "string",
                        "description": "Optional: The user who will own the database"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Optional: Character encoding (e.g., UTF8)",
                        "default": "UTF8"
                    },
                    "template": {
                        "type": "string",
                        "description": "Optional: Template database to copy from (e.g., template0, template1)",
                        "default": "template1"
                    }
                },
                "required": ["database_name"]
            }
        ),
        Tool(
            name="drop_database",
            description="Permanently delete a database from the PostgreSQL server. WARNING: This operation is irreversible and will delete all data in the database! Requires explicit user consent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {
                        "type": "string",
                        "description": "The name of the database to drop"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "If true, force drop by terminating all connections to the database first",
                        "default": False
                    },
                    "if_exists": {
                        "type": "boolean",
                        "description": "If true, do not throw an error if the database doesn't exist",
                        "default": True
                    }
                },
                "required": ["database_name"]
            }
        ),
        Tool(
            name="list_databases",
            description="List all databases on the PostgreSQL server with their details (owner, encoding, size, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_system_databases": {
                        "type": "boolean",
                        "description": "Include system databases like template0, template1, postgres",
                        "default": False
                    }
                }
            }
        ),

        # Backup and Restore Operations
        Tool(
            name="backup_database",
            description="Create a backup of a PostgreSQL database. When user specifies a folder location (e.g., 'backup to C:\\Agentic-RAG'), use that path with format: {folder}\\{database_name}_backup_{timestamp}.dump. Automatically uses pg_dump if available (recommended for large databases 50GB+), otherwise falls back to SQL-based method. Supports various backup formats and compression.",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {
                        "type": "string",
                        "description": "The name of the database to backup"
                    },
                    "backup_path": {
                        "type": "string",
                        "description": "Full path where the backup file will be saved. Can be a folder (e.g., C:\\Agentic-RAG) or full file path (e.g., C:\\Agentic-RAG\\mydb.dump). If folder only, filename will be auto-generated as {database_name}_backup_{timestamp}.dump"
                    },
                    "format": {
                        "type": "string",
                        "description": "Backup format: 'custom' (compressed, best for large DBs), 'plain' (SQL script), 'directory', 'tar'. Custom/directory/tar require pg_dump.",
                        "enum": ["custom", "plain", "directory", "tar"],
                        "default": "custom"
                    },
                    "compress_level": {
                        "type": "integer",
                        "description": "Compression level (0-9) for custom and directory formats. 0=no compression, 9=max compression",
                        "minimum": 0,
                        "maximum": 9,
                        "default": 6
                    },
                    "schema_only": {
                        "type": "boolean",
                        "description": "If true, only backup the schema (structure) without data",
                        "default": False
                    },
                    "data_only": {
                        "type": "boolean",
                        "description": "If true, only backup data without schema",
                        "default": False
                    },
                    "tables": {
                        "type": "array",
                        "description": "Optional: List of specific table names to backup. If not specified, all tables are backed up.",
                        "items": {"type": "string"}
                    },
                    "exclude_tables": {
                        "type": "array",
                        "description": "Optional: List of table names to exclude from backup",
                        "items": {"type": "string"}
                    },
                    "use_pg_dump": {
                        "type": "boolean",
                        "description": "If true, force use of pg_dump tool. If false, force SQL-based method. If not specified, auto-detect.",
                        "default": None
                    }
                },
                "required": ["database_name", "backup_path"]
            }
        ),
        Tool(
            name="restore_database",
            description="Restore a PostgreSQL database from a backup file. Automatically uses pg_restore/psql if available (recommended for large databases), otherwise falls back to SQL-based method. Use with caution as this can overwrite existing data!",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {
                        "type": "string",
                        "description": "The name of the target database to restore to"
                    },
                    "backup_path": {
                        "type": "string",
                        "description": "Full path to the backup file to restore from"
                    },
                    "create_database": {
                        "type": "boolean",
                        "description": "If true, create the database before restoring (only for plain SQL format)",
                        "default": False
                    },
                    "clean": {
                        "type": "boolean",
                        "description": "If true, drop existing database objects before restoring (use with caution!)",
                        "default": False
                    },
                    "data_only": {
                        "type": "boolean",
                        "description": "If true, only restore data without schema",
                        "default": False
                    },
                    "schema_only": {
                        "type": "boolean",
                        "description": "If true, only restore schema without data",
                        "default": False
                    },
                    "use_pg_restore": {
                        "type": "boolean",
                        "description": "If true, force use of pg_restore/psql tools. If false, force SQL-based method. If not specified, auto-detect.",
                        "default": None
                    }
                },
                "required": ["database_name", "backup_path"]
            }
        ),
        Tool(
            name="list_backups",
            description="List all backup files in a specified directory with their details (size, date, format).",
            inputSchema={
                "type": "object",
                "properties": {
                    "backup_directory": {
                        "type": "string",
                        "description": "Path to the directory containing backup files"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional file pattern to filter backups (e.g., '*.dump', '*.sql')",
                        "default": "*"
                    }
                },
                "required": ["backup_directory"]
            }
        ),
        Tool(
            name="check_backup_tools",
            description="Check if PostgreSQL backup/restore tools (pg_dump, pg_restore, psql) are installed and available. Useful for determining which backup methods are supported.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        # Route to appropriate handler
        if name == "execute_select":
            result = await handle_select(arguments)
        elif name == "execute_insert":
            result = await handle_insert(arguments)
        elif name == "execute_update":
            result = await handle_update(arguments)
        elif name == "execute_delete":
            result = await handle_delete(arguments)
        elif name == "execute_create_table":
            result = await handle_create_table(arguments)
        elif name == "execute_alter_table":
            result = await handle_alter_table(arguments)
        elif name == "execute_drop_table":
            result = await handle_drop_table(arguments)
        elif name == "execute_create_index":
            result = await handle_create_index(arguments)
        elif name == "execute_drop_index":
            result = await handle_drop_index(arguments)
        elif name == "execute_transaction":
            result = await handle_transaction(arguments)
        elif name == "get_schema_info":
            result = await handle_get_schema_info(arguments)
        elif name == "get_table_info":
            result = await handle_get_table_info(arguments)
        elif name == "execute_raw_sql":
            result = await handle_raw_sql(arguments)
        elif name == "create_database":
            result = await handle_create_database(arguments)
        elif name == "drop_database":
            result = await handle_drop_database(arguments)
        elif name == "list_databases":
            result = await handle_list_databases(arguments)
        elif name == "backup_database":
            result = await handle_backup_database(arguments)
        elif name == "restore_database":
            result = await handle_restore_database(arguments)
        elif name == "list_backups":
            result = await handle_list_backups(arguments)
        elif name == "check_backup_tools":
            result = await handle_check_backup_tools(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        error_result = {
            "success": False,
            "error": str(e),
            "tool": name
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


# Tool Handlers

async def handle_select(arguments: dict) -> dict:
    """Handle SELECT queries"""
    query = arguments.get("query")
    params = arguments.get("params", [])
    database_name = arguments.get("database_name")

    async with get_database_connection(database_name) as conn:
        rows = await conn.fetch(query, *params)

        result = {
            "success": True,
            "row_count": len(rows),
            "data": [dict(row) for row in rows]
        }
        if database_name:
            result["database"] = database_name
        return result


async def handle_insert(arguments: dict) -> dict:
    """Handle INSERT statements"""
    query = arguments.get("query")
    params = arguments.get("params", [])

    async with db_manager.acquire() as conn:
        # Check if RETURNING clause exists
        if "RETURNING" in query.upper():
            rows = await conn.fetch(query, *params)
            result = {
                "success": True,
                "rows_affected": len(rows),
                "returned_data": [dict(row) for row in rows]
            }
        else:
            status = await conn.execute(query, *params)
            # Extract row count from status string like "INSERT 0 5"
            rows_affected = int(status.split()[-1]) if status else 0
            result = {
                "success": True,
                "rows_affected": rows_affected
            }
        return result


async def handle_update(arguments: dict) -> dict:
    """Handle UPDATE statements"""
    query = arguments.get("query")
    params = arguments.get("params", [])

    async with db_manager.acquire() as conn:
        status = await conn.execute(query, *params)
        rows_affected = int(status.split()[-1]) if status else 0

        result = {
            "success": True,
            "rows_affected": rows_affected,
            "message": f"Updated {rows_affected} row(s)"
        }
        return result


async def handle_delete(arguments: dict) -> dict:
    """Handle DELETE statements"""
    query = arguments.get("query")
    params = arguments.get("params", [])

    async with db_manager.acquire() as conn:
        status = await conn.execute(query, *params)
        rows_affected = int(status.split()[-1]) if status else 0

        result = {
            "success": True,
            "rows_affected": rows_affected,
            "message": f"Deleted {rows_affected} row(s)"
        }
        return result


async def handle_create_table(arguments: dict) -> dict:
    """Handle CREATE TABLE statements"""
    query = arguments.get("query")
    database_name = arguments.get("database_name")

    async with get_database_connection(database_name) as conn:
        await conn.execute(query)

        result = {
            "success": True,
            "message": f"Table created successfully{' in database ' + database_name if database_name else ''}"
        }
        if database_name:
            result["database"] = database_name

        return result


async def handle_alter_table(arguments: dict) -> dict:
    """Handle ALTER TABLE statements"""
    query = arguments.get("query")

    async with db_manager.acquire() as conn:
        await conn.execute(query)

        result = {
            "success": True,
            "message": "Table altered successfully"
        }
        return result


async def handle_drop_table(arguments: dict) -> dict:
    """Handle DROP TABLE statements"""
    table_name = arguments.get("table_name")
    cascade = arguments.get("cascade", False)
    if_exists = arguments.get("if_exists", True)

    query = f"DROP TABLE {'IF EXISTS ' if if_exists else ''}{table_name}{' CASCADE' if cascade else ''}"

    async with db_manager.acquire() as conn:
        await conn.execute(query)

        result = {
            "success": True,
            "message": f"Table '{table_name}' dropped successfully"
        }
        return result


async def handle_create_index(arguments: dict) -> dict:
    """Handle CREATE INDEX statements"""
    query = arguments.get("query")

    async with db_manager.acquire() as conn:
        await conn.execute(query)

        result = {
            "success": True,
            "message": "Index created successfully"
        }
        return result


async def handle_drop_index(arguments: dict) -> dict:
    """Handle DROP INDEX statements"""
    index_name = arguments.get("index_name")
    if_exists = arguments.get("if_exists", True)

    query = f"DROP INDEX {'IF EXISTS ' if if_exists else ''}{index_name}"

    async with db_manager.acquire() as conn:
        await conn.execute(query)

        result = {
            "success": True,
            "message": f"Index '{index_name}' dropped successfully"
        }
        return result


async def handle_transaction(arguments: dict) -> dict:
    """Handle transaction execution"""
    statements = arguments.get("statements", [])
    isolation_level = arguments.get("isolation_level", "read_committed")

    results = []

    async with db_manager.acquire() as conn:
        async with conn.transaction(isolation=isolation_level):
            for stmt in statements:
                query = stmt.get("query")
                params = stmt.get("params", [])

                # Determine if it's a query that returns data
                query_upper = query.strip().upper()
                if query_upper.startswith("SELECT") or "RETURNING" in query_upper:
                    rows = await conn.fetch(query, *params)
                    results.append({
                        "query": query,
                        "data": [dict(row) for row in rows],
                        "row_count": len(rows)
                    })
                else:
                    status = await conn.execute(query, *params)
                    results.append({
                        "query": query,
                        "status": status
                    })

    return {
        "success": True,
        "message": "Transaction completed successfully",
        "results": results
    }


async def handle_get_schema_info(arguments: dict) -> dict:
    """Get database schema information"""
    schema_name = arguments.get("schema_name", "public")
    include_system = arguments.get("include_system_schemas", False)

    async with db_manager.acquire() as conn:
        # Get all tables
        schema_filter = "" if include_system else "AND schemaname NOT IN ('pg_catalog', 'information_schema')"

        tables_query = f"""
            SELECT schemaname, tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = $1 {schema_filter}
            ORDER BY tablename
        """
        tables = await conn.fetch(tables_query, schema_name)

        schema_info = []

        for table in tables:
            table_name = table['tablename']

            # Get columns
            columns_query = """
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
            """
            columns = await conn.fetch(columns_query, schema_name, table_name)

            # Get constraints
            constraints_query = """
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_schema = $1 AND table_name = $2
            """
            constraints = await conn.fetch(constraints_query, schema_name, table_name)

            schema_info.append({
                "table": table_name,
                "columns": [dict(col) for col in columns],
                "constraints": [dict(con) for con in constraints]
            })

        return {
            "success": True,
            "schema": schema_name,
            "tables": schema_info
        }


async def handle_get_table_info(arguments: dict) -> dict:
    """Get detailed table information"""
    table_name = arguments.get("table_name")
    schema_name = arguments.get("schema_name", "public")

    async with db_manager.acquire() as conn:
        # Get columns
        columns_query = """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        columns = await conn.fetch(columns_query, schema_name, table_name)

        # Get constraints
        constraints_query = """
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = $1 AND table_name = $2
        """
        constraints = await conn.fetch(constraints_query, schema_name, table_name)

        # Get indexes
        indexes_query = """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = $1 AND tablename = $2
        """
        indexes = await conn.fetch(indexes_query, schema_name, table_name)

        # Get row count
        count_query = f'SELECT COUNT(*) as count FROM "{schema_name}"."{table_name}"'
        count_result = await conn.fetchrow(count_query)

        return {
            "success": True,
            "table": table_name,
            "schema": schema_name,
            "columns": [dict(col) for col in columns],
            "constraints": [dict(con) for con in constraints],
            "indexes": [dict(idx) for idx in indexes],
            "row_count": count_result['count'] if count_result else 0
        }


async def handle_raw_sql(arguments: dict) -> dict:
    """Handle raw SQL execution"""
    query = arguments.get("query")
    params = arguments.get("params", [])

    async with db_manager.acquire() as conn:
        query_upper = query.strip().upper()

        # Determine if it's a query that returns data
        if query_upper.startswith("SELECT") or "RETURNING" in query_upper:
            rows = await conn.fetch(query, *params)
            result = {
                "success": True,
                "row_count": len(rows),
                "data": [dict(row) for row in rows]
            }
        else:
            status = await conn.execute(query, *params)
            result = {
                "success": True,
                "status": status,
                "message": "Query executed successfully"
            }

        return result


async def handle_create_database(arguments: dict) -> dict:
    """Handle CREATE DATABASE operation with consent"""
    database_name = arguments.get("database_name")
    owner = arguments.get("owner")
    encoding = arguments.get("encoding", "UTF8")
    template = arguments.get("template", "template1")

    # Validate database name to prevent SQL injection
    if not database_name or not database_name.replace("_", "").replace("-", "").isalnum():
        return {
            "success": False,
            "error": "Invalid database name. Use only alphanumeric characters, underscores, and hyphens."
        }

    # Build CREATE DATABASE query
    query_parts = [f'CREATE DATABASE "{database_name}"']

    if owner:
        query_parts.append(f'OWNER = "{owner}"')

    if encoding:
        query_parts.append(f"ENCODING = '{encoding}'")

    if template:
        query_parts.append(f'TEMPLATE = "{template}"')

    query = " ".join(query_parts)

    # DATABASE operations require a connection not in a transaction and not to the database being created
    # We need to connect to the maintenance database (postgres) to create a new database
    try:
        # Parse the current DATABASE_URL to connect to 'postgres' database
        import asyncpg

        # Get connection parameters from the pool
        # We'll create a temporary connection to the 'postgres' database
        dsn_parts = DATABASE_URL.rsplit('/', 1)
        if len(dsn_parts) == 2:
            maintenance_dsn = f"{dsn_parts[0]}/postgres"
        else:
            maintenance_dsn = DATABASE_URL

        # Create a direct connection to execute CREATE DATABASE
        # (cannot be done within a transaction or connection pool to another DB)
        conn = await asyncpg.connect(maintenance_dsn)

        try:
            # Check if database already exists
            check_query = "SELECT 1 FROM pg_database WHERE datname = $1"
            exists = await conn.fetchval(check_query, database_name)

            if exists:
                return {
                    "success": False,
                    "error": f"Database '{database_name}' already exists"
                }

            # Execute CREATE DATABASE
            await conn.execute(query)

            result = {
                "success": True,
                "message": f"Database '{database_name}' created successfully",
                "database_name": database_name,
                "encoding": encoding,
                "template": template
            }

            if owner:
                result["owner"] = owner

            logger.info(f"Database created: {database_name}")
            return result

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return {
            "success": False,
            "error": f"Failed to create database: {str(e)}"
        }


async def handle_drop_database(arguments: dict) -> dict:
    """Handle DROP DATABASE operation with consent"""
    database_name = arguments.get("database_name")
    force = arguments.get("force", False)
    if_exists = arguments.get("if_exists", True)

    # Validate database name to prevent SQL injection
    if not database_name or not database_name.replace("_", "").replace("-", "").isalnum():
        return {
            "success": False,
            "error": "Invalid database name. Use only alphanumeric characters, underscores, and hyphens."
        }

    # Prevent dropping system databases
    system_databases = ["postgres", "template0", "template1"]
    if database_name.lower() in system_databases:
        return {
            "success": False,
            "error": f"Cannot drop system database '{database_name}'"
        }

    try:
        import asyncpg

        # Parse the current DATABASE_URL to connect to 'postgres' database
        dsn_parts = DATABASE_URL.rsplit('/', 1)
        if len(dsn_parts) == 2:
            maintenance_dsn = f"{dsn_parts[0]}/postgres"
        else:
            maintenance_dsn = DATABASE_URL

        # Create a direct connection
        conn = await asyncpg.connect(maintenance_dsn)

        try:
            # Check if database exists
            check_query = "SELECT 1 FROM pg_database WHERE datname = $1"
            exists = await conn.fetchval(check_query, database_name)

            if not exists:
                if if_exists:
                    return {
                        "success": True,
                        "message": f"Database '{database_name}' does not exist (skipped)"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Database '{database_name}' does not exist"
                    }

            # If force is true, terminate all connections to the database
            if force:
                terminate_query = """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = $1 AND pid <> pg_backend_pid()
                """
                terminated = await conn.fetch(terminate_query, database_name)
                logger.info(f"Terminated {len(terminated)} connections to database '{database_name}'")

            # Execute DROP DATABASE
            drop_query = f'DROP DATABASE {"IF EXISTS " if if_exists else ""}"{database_name}"'
            await conn.execute(drop_query)

            logger.info(f"Database dropped: {database_name}")
            return {
                "success": True,
                "message": f"Database '{database_name}' dropped successfully",
                "database_name": database_name,
                "forced": force
            }

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Error dropping database: {e}")
        return {
            "success": False,
            "error": f"Failed to drop database: {str(e)}"
        }


async def handle_list_databases(arguments: dict) -> dict:
    """Handle LIST DATABASES operation"""
    include_system = arguments.get("include_system_databases", False)

    try:
        async with db_manager.acquire() as conn:
            # Query to get database information
            query = """
                SELECT
                    d.datname as name,
                    pg_catalog.pg_get_userbyid(d.datdba) as owner,
                    pg_catalog.pg_encoding_to_char(d.encoding) as encoding,
                    d.datcollate as collation,
                    d.datctype as ctype,
                    pg_catalog.pg_database_size(d.datname) as size_bytes,
                    pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname)) as size,
                    d.datallowconn as allow_connections,
                    d.datconnlimit as connection_limit,
                    (SELECT count(*) FROM pg_stat_activity WHERE datname = d.datname) as active_connections
                FROM pg_catalog.pg_database d
                WHERE 1=1
            """

            # Filter out system databases if requested
            if not include_system:
                query += " AND d.datname NOT IN ('template0', 'template1', 'postgres')"

            query += " ORDER BY d.datname"

            databases = await conn.fetch(query)

            return {
                "success": True,
                "database_count": len(databases),
                "databases": [dict(db) for db in databases]
            }

    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        return {
            "success": False,
            "error": f"Failed to list databases: {str(e)}"
        }


async def handle_backup_database(arguments: dict) -> dict:
    """Handle database backup using pg_dump or SQL-based approach"""
    from pathlib import Path
    import subprocess
    import urllib.parse
    import gzip
    from datetime import datetime

    database_name = arguments.get("database_name")
    backup_path = arguments.get("backup_path")
    backup_format = arguments.get("format", "custom")
    compress_level = arguments.get("compress_level", 6)
    schema_only = arguments.get("schema_only", False)
    data_only = arguments.get("data_only", False)
    tables = arguments.get("tables", [])
    exclude_tables = arguments.get("exclude_tables", [])
    use_pg_dump = arguments.get("use_pg_dump", None)

    try:
        # Validate database name
        if not database_name or not database_name.replace("_", "").replace("-", "").isalnum():
            return {
                "success": False,
                "error": "Invalid database name"
            }

        # Handle backup_path: if it's a directory, generate filename
        backup_path_obj = Path(backup_path)
        if backup_path_obj.is_dir() or (not backup_path_obj.suffix and not backup_path_obj.exists()):
            # It's a directory or path without extension - auto-generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Determine file extension based on format
            ext_map = {
                "custom": ".dump",
                "plain": ".sql",
                "tar": ".tar",
                "directory": ""  # directory format doesn't need extension
            }
            extension = ext_map.get(backup_format, ".dump")

            filename = f"{database_name}_backup_{timestamp}{extension}"
            backup_path = str(backup_path_obj / filename)
            logger.info(f"Auto-generated backup filename: {filename}")
            logger.info(f"Full backup path: {backup_path}")

        # Check if pg_dump is available
        pg_tools = check_pg_tools_available()
        pg_dump_available = pg_tools.get('pg_dump', False)

        # Decide which method to use
        if use_pg_dump is True and not pg_dump_available:
            return {
                "success": False,
                "error": "pg_dump tool not found in PATH. Please install PostgreSQL client tools or set use_pg_dump=False to use SQL-based method.",
                "tools_status": pg_tools
            }

        # Auto-detect: use pg_dump if available and format is not plain, or if explicitly requested
        should_use_pg_dump = (use_pg_dump is True) or (use_pg_dump is None and pg_dump_available and backup_format != "plain")

        if should_use_pg_dump and pg_dump_available:
            # Use pg_dump method
            return await _backup_with_pg_dump(
                database_name, backup_path, backup_format, compress_level,
                schema_only, data_only, tables, exclude_tables
            )
        else:
            # Use SQL-based method
            if backup_format in ["custom", "directory", "tar"]:
                logger.warning(f"Format '{backup_format}' requires pg_dump. Falling back to plain SQL format.")
                backup_format = "plain"

            return await _backup_with_sql(
                database_name, backup_path, compress_level,
                schema_only, data_only, tables, exclude_tables
            )

    except Exception as e:
        logger.error(f"Error during backup: {e}")
        return {
            "success": False,
            "error": f"Backup failed: {str(e)}"
        }


async def _backup_with_pg_dump(database_name, backup_path, backup_format, compress_level,
                                 schema_only, data_only, tables, exclude_tables) -> dict:
    """Backup using pg_dump command-line tool"""
    import subprocess
    import urllib.parse
    from pathlib import Path

    try:
        # Parse DATABASE_URL to get connection parameters
        parsed = urllib.parse.urlparse(DATABASE_URL)

        # Build pg_dump command
        pg_dump_cmd = ["pg_dump"]

        # Add connection parameters
        if parsed.hostname:
            pg_dump_cmd.extend(["-h", parsed.hostname])
        if parsed.port:
            pg_dump_cmd.extend(["-p", str(parsed.port)])
        if parsed.username:
            # Decode URL-encoded username (for Azure format: username@servername)
            username = urllib.parse.unquote(parsed.username)
            pg_dump_cmd.extend(["-U", username])
            logger.info(f"Using username: {username}")

        # Add database name
        pg_dump_cmd.extend(["-d", database_name])

        # Add format
        format_map = {
            "custom": "c",
            "plain": "p",
            "directory": "d",
            "tar": "t"
        }
        pg_dump_cmd.extend(["-F", format_map[backup_format]])

        # Add compression level (only for custom and directory formats)
        if backup_format in ["custom", "directory"]:
            pg_dump_cmd.extend(["-Z", str(compress_level)])

        # Add schema/data only options
        if schema_only:
            pg_dump_cmd.append("--schema-only")
        if data_only:
            pg_dump_cmd.append("--data-only")

        # Add specific tables
        for table in tables:
            pg_dump_cmd.extend(["-t", table])

        # Add exclude tables
        for table in exclude_tables:
            pg_dump_cmd.extend(["-T", table])

        # Add output file
        pg_dump_cmd.extend(["-f", backup_path])

        # Add verbose flag
        pg_dump_cmd.append("--verbose")

        # Set password environment variable if present
        env = os.environ.copy()
        if parsed.password:
            # Decode URL-encoded password
            password = urllib.parse.unquote(parsed.password)
            env["PGPASSWORD"] = password
            logger.info("Password extracted and set in environment")
        else:
            logger.warning("No password found in DATABASE_URL")

        # Add SSL/TLS support for Azure PostgreSQL
        # Parse query parameters from DATABASE_URL
        query_params = urllib.parse.parse_qs(parsed.query) if parsed.query else {}
        sslmode = query_params.get('sslmode', ['prefer'])[0]

        # Set SSL environment variables for Azure PostgreSQL
        if 'azure.com' in (parsed.hostname or '') or sslmode in ['require', 'verify-ca', 'verify-full']:
            env["PGSSLMODE"] = sslmode
            # Azure PostgreSQL requires SSL
            logger.info(f"Azure PostgreSQL detected - enabling SSL mode: {sslmode}")

        # Create backup directory if it doesn't exist
        backup_dir = Path(backup_path).parent
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Execute pg_dump
        logger.info(f"Executing pg_dump for database '{database_name}'")
        result = subprocess.run(
            pg_dump_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout for large databases
        )

        if result.returncode == 0:
            # Get backup file size
            backup_file = Path(backup_path)
            file_size = backup_file.stat().st_size if backup_file.exists() else 0
            file_size_mb = file_size / (1024 * 1024)

            logger.info(f"Backup completed successfully: {backup_path}")
            return {
                "success": True,
                "message": f"Database '{database_name}' backed up successfully using pg_dump",
                "database_name": database_name,
                "backup_path": backup_path,
                "backup_format": backup_format,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size_mb, 2),
                "schema_only": schema_only,
                "data_only": data_only,
                "method": "pg_dump",
                "note": "Backup created using pg_dump (recommended for large databases)"
            }
        else:
            logger.error(f"pg_dump failed: {result.stderr}")
            return {
                "success": False,
                "error": f"pg_dump failed: {result.stderr}",
                "stdout": result.stdout
            }

    except subprocess.TimeoutExpired:
        logger.error("Backup operation timed out")
        return {
            "success": False,
            "error": "Backup operation timed out after 2 hours"
        }
    except Exception as e:
        logger.error(f"Error during pg_dump backup: {e}")
        return {
            "success": False,
            "error": f"pg_dump backup failed: {str(e)}"
        }


async def _backup_with_sql(database_name, backup_path, compress_level,
                            schema_only, data_only, tables, exclude_tables) -> dict:
    """Backup using SQL-based approach"""
    from pathlib import Path
    import gzip
    from datetime import datetime

    try:
        # Validate database name
        if not database_name or not database_name.replace("_", "").replace("-", "").isalnum():
            return {
                "success": False,
                "error": "Invalid database name"
            }

        # Create backup directory if it doesn't exist
        backup_dir = Path(backup_path).parent
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Force plain format for SQL-based backup
        if backup_format != "plain":
            logger.warning(f"Format '{backup_format}' not supported for SQL-based backup, using 'plain' instead")
            backup_format = "plain"

        # Ensure .sql extension
        if not backup_path.endswith('.sql') and not backup_path.endswith('.sql.gz'):
            backup_path = backup_path + '.sql'

        # Connect to the target database
        import asyncpg
        dsn_parts = DATABASE_URL.rsplit('/', 1)
        if len(dsn_parts) == 2:
            db_dsn = f"{dsn_parts[0]}/{database_name}"
        else:
            db_dsn = DATABASE_URL

        conn = await asyncpg.connect(db_dsn)

        try:
            backup_content = []
            backup_content.append(f"-- PostgreSQL Database Backup")
            backup_content.append(f"-- Database: {database_name}")
            backup_content.append(f"-- Generated: {datetime.now().isoformat()}")
            backup_content.append(f"-- Format: SQL")
            backup_content.append("")

            # Get list of tables to backup
            if tables:
                table_list = tables
            else:
                # Get all tables from public schema
                table_query = """
                    SELECT tablename
                    FROM pg_catalog.pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """
                table_rows = await conn.fetch(table_query)
                table_list = [row['tablename'] for row in table_rows]

                # Apply exclusions
                if exclude_tables:
                    table_list = [t for t in table_list if t not in exclude_tables]

            logger.info(f"Backing up {len(table_list)} tables from database '{database_name}'")

            # Backup schema (CREATE TABLE statements)
            if not data_only:
                backup_content.append("-- Schema Definitions")
                backup_content.append("")

                for table_name in table_list:
                    # Get table definition
                    schema_query = f"""
                        SELECT
                            'CREATE TABLE ' || quote_ident(table_name) || ' (' ||
                            string_agg(
                                quote_ident(column_name) || ' ' ||
                                data_type ||
                                CASE
                                    WHEN character_maximum_length IS NOT NULL
                                    THEN '(' || character_maximum_length || ')'
                                    ELSE ''
                                END ||
                                CASE
                                    WHEN is_nullable = 'NO' THEN ' NOT NULL'
                                    ELSE ''
                                END,
                                ', '
                            ) || ');' as create_statement
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = '{table_name}'
                        GROUP BY table_name
                    """

                    try:
                        result = await conn.fetchrow(schema_query)
                        if result and result['create_statement']:
                            backup_content.append(f"-- Table: {table_name}")
                            backup_content.append(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                            backup_content.append(result['create_statement'])
                            backup_content.append("")
                    except Exception as e:
                        logger.warning(f"Could not get schema for table {table_name}: {e}")

            # Backup data (INSERT statements)
            if not schema_only:
                backup_content.append("-- Data")
                backup_content.append("")

                total_rows = 0
                for table_name in table_list:
                    # Get all rows from table
                    try:
                        rows = await conn.fetch(f'SELECT * FROM "{table_name}"')

                        if rows:
                            backup_content.append(f"-- Data for table: {table_name}")

                            # Get column names
                            columns = list(rows[0].keys())
                            column_list = ', '.join([f'"{col}"' for col in columns])

                            # Generate INSERT statements
                            for row in rows:
                                values = []
                                for col in columns:
                                    val = row[col]
                                    if val is None:
                                        values.append('NULL')
                                    elif isinstance(val, str):
                                        # Escape single quotes
                                        escaped = val.replace("'", "''")
                                        values.append(f"'{escaped}'")
                                    elif isinstance(val, (int, float, bool)):
                                        values.append(str(val))
                                    elif isinstance(val, datetime):
                                        values.append(f"'{val.isoformat()}'")
                                    else:
                                        # For other types, convert to string
                                        escaped = str(val).replace("'", "''")
                                        values.append(f"'{escaped}'")

                                value_list = ', '.join(values)
                                backup_content.append(f"INSERT INTO \"{table_name}\" ({column_list}) VALUES ({value_list});")

                            total_rows += len(rows)
                            backup_content.append("")
                            logger.info(f"Backed up {len(rows)} rows from table '{table_name}'")

                    except Exception as e:
                        logger.warning(f"Could not backup data from table {table_name}: {e}")
                        backup_content.append(f"-- Error backing up table {table_name}: {str(e)}")
                        backup_content.append("")

            # Write backup to file
            backup_sql = '\n'.join(backup_content)

            # Compress if requested (compression level > 0)
            if compress_level > 0:
                if not backup_path.endswith('.gz'):
                    backup_path += '.gz'

                with gzip.open(backup_path, 'wt', compresslevel=compress_level, encoding='utf-8') as f:
                    f.write(backup_sql)
            else:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(backup_sql)

            # Get backup file size
            backup_file = Path(backup_path)
            file_size = backup_file.stat().st_size if backup_file.exists() else 0
            file_size_mb = file_size / (1024 * 1024)

            logger.info(f"Backup completed successfully: {backup_path}")
            return {
                "success": True,
                "message": f"Database '{database_name}' backed up successfully using SQL-based method",
                "database_name": database_name,
                "backup_path": backup_path,
                "backup_format": "plain (SQL)",
                "tables_backed_up": len(table_list),
                "total_rows": total_rows if not schema_only else 0,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size_mb, 2),
                "compressed": compress_level > 0,
                "schema_only": schema_only,
                "data_only": data_only,
                "note": "Backup created using SQL-based method (no pg_dump required)"
            }

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Error during backup: {e}")
        return {
            "success": False,
            "error": f"Backup failed: {str(e)}",
            "note": "SQL-based backup method used. For advanced features, install PostgreSQL client tools (pg_dump)."
        }


async def handle_restore_database(arguments: dict) -> dict:
    """Handle database restore using pg_restore/psql or SQL-based approach"""
    from pathlib import Path
    import gzip
    import re

    database_name = arguments.get("database_name")
    backup_path = arguments.get("backup_path")
    create_database = arguments.get("create_database", False)
    clean = arguments.get("clean", False)
    data_only = arguments.get("data_only", False)
    schema_only = arguments.get("schema_only", False)
    use_pg_restore = arguments.get("use_pg_restore", None)

    try:
        # Validate database name
        if not database_name or not database_name.replace("_", "").replace("-", "").isalnum():
            return {
                "success": False,
                "error": "Invalid database name"
            }

        # Check if backup file exists
        backup_file = Path(backup_path)
        if not backup_file.exists():
            return {
                "success": False,
                "error": f"Backup file not found: {backup_path}"
            }

        # Check if pg_restore/psql are available
        pg_tools = check_pg_tools_available()
        pg_restore_available = pg_tools.get('pg_restore', False)
        psql_available = pg_tools.get('psql', False)

        # Decide which method to use
        if use_pg_restore is True and not (pg_restore_available or psql_available):
            return {
                "success": False,
                "error": "pg_restore/psql tools not found in PATH. Please install PostgreSQL client tools or set use_pg_restore=False to use SQL-based method.",
                "tools_status": pg_tools
            }

        # Determine backup file format
        is_plain_sql = backup_path.endswith('.sql') or backup_path.endswith('.sql.gz')
        is_custom_format = backup_path.endswith('.dump') or backup_path.endswith('.backup')

        # Auto-detect: use pg_restore/psql if available
        should_use_pg_tools = (use_pg_restore is True) or (
            use_pg_restore is None and (
                (is_custom_format and pg_restore_available) or
                (is_plain_sql and psql_available)
            )
        )

        if should_use_pg_tools and (pg_restore_available or psql_available):
            # Use pg_restore or psql method
            return await _restore_with_pg_tools(
                database_name, backup_path, create_database, clean,
                data_only, schema_only, is_plain_sql
            )
        else:
            # Use SQL-based method
            if not is_plain_sql:
                return {
                    "success": False,
                    "error": f"Cannot restore '{backup_path}' using SQL-based method. This format requires pg_restore. Please install PostgreSQL client tools or use a .sql backup file."
                }

            return await _restore_with_sql(
                database_name, backup_path, clean, data_only, schema_only
            )

    except Exception as e:
        logger.error(f"Error during restore: {e}")
        return {
            "success": False,
            "error": f"Restore failed: {str(e)}"
        }


async def _restore_with_pg_tools(database_name, backup_path, create_database, clean,
                                   data_only, schema_only, is_plain_sql) -> dict:
    """Restore using pg_restore or psql command-line tools"""
    import subprocess
    import urllib.parse

    try:
        # Parse DATABASE_URL to get connection parameters
        parsed = urllib.parse.urlparse(DATABASE_URL)

        # Build restore command based on backup format
        if is_plain_sql:
            # Use psql for plain SQL files
            restore_cmd = ["psql"]

            # Add connection parameters
            if parsed.hostname:
                restore_cmd.extend(["-h", parsed.hostname])
            if parsed.port:
                restore_cmd.extend(["-p", str(parsed.port)])
            if parsed.username:
                # Decode URL-encoded username (for Azure format: username@servername)
                username = urllib.parse.unquote(parsed.username)
                restore_cmd.extend(["-U", username])
                logger.info(f"Using username: {username}")

            # Add database name
            restore_cmd.extend(["-d", database_name])

            # Add file
            restore_cmd.extend(["-f", backup_path])

            # Add options
            if not create_database:
                restore_cmd.append("--single-transaction")
        else:
            # Use pg_restore for custom/tar/directory formats
            restore_cmd = ["pg_restore"]

            # Add connection parameters
            if parsed.hostname:
                restore_cmd.extend(["-h", parsed.hostname])
            if parsed.port:
                restore_cmd.extend(["-p", str(parsed.port)])
            if parsed.username:
                # Decode URL-encoded username (for Azure format: username@servername)
                username = urllib.parse.unquote(parsed.username)
                restore_cmd.extend(["-U", username])
                logger.info(f"Using username: {username}")

            # Add database name
            restore_cmd.extend(["-d", database_name])

            # Add options
            if clean:
                restore_cmd.append("--clean")
            if data_only:
                restore_cmd.append("--data-only")
            if schema_only:
                restore_cmd.append("--schema-only")

            # Verbose output
            restore_cmd.append("--verbose")

            # Add backup file
            restore_cmd.append(backup_path)

        # Set password environment variable if present
        env = os.environ.copy()
        if parsed.password:
            # Decode URL-encoded password
            password = urllib.parse.unquote(parsed.password)
            env["PGPASSWORD"] = password
            logger.info("Password extracted and set in environment")
        else:
            logger.warning("No password found in DATABASE_URL")

        # Add SSL/TLS support for Azure PostgreSQL
        query_params = urllib.parse.parse_qs(parsed.query) if parsed.query else {}
        sslmode = query_params.get('sslmode', ['prefer'])[0]

        # Set SSL environment variables for Azure PostgreSQL
        if 'azure.com' in (parsed.hostname or '') or sslmode in ['require', 'verify-ca', 'verify-full']:
            env["PGSSLMODE"] = sslmode
            logger.info(f"Azure PostgreSQL detected - enabling SSL mode: {sslmode}")

        # Execute restore command
        tool_name = "psql" if is_plain_sql else "pg_restore"
        logger.info(f"Executing {tool_name} for database '{database_name}'")
        result = subprocess.run(
            restore_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout for large databases
        )

        # pg_restore may return non-zero even on success (warnings), check stderr
        if result.returncode == 0 or (result.returncode == 1 and "error" not in result.stderr.lower()):
            logger.info(f"Restore completed for database '{database_name}'")
            return {
                "success": True,
                "message": f"Database '{database_name}' restored successfully using {tool_name}",
                "database_name": database_name,
                "backup_path": backup_path,
                "method": tool_name,
                "warnings": result.stderr if result.stderr else None,
                "note": f"Restore completed using {tool_name} (recommended for large databases)"
            }
        else:
            logger.error(f"{tool_name} failed: {result.stderr}")
            return {
                "success": False,
                "error": f"{tool_name} failed: {result.stderr}",
                "stdout": result.stdout
            }

    except subprocess.TimeoutExpired:
        logger.error("Restore operation timed out")
        return {
            "success": False,
            "error": "Restore operation timed out after 2 hours"
        }
    except Exception as e:
        logger.error(f"Error during restore: {e}")
        return {
            "success": False,
            "error": f"Restore failed: {str(e)}"
        }


async def _restore_with_sql(database_name, backup_path, clean, data_only, schema_only) -> dict:
    """Restore using SQL-based approach"""
    from pathlib import Path
    import gzip

    try:
        # Validate database name
        if not database_name or not database_name.replace("_", "").replace("-", "").isalnum():
            return {
                "success": False,
                "error": "Invalid database name"
            }

        # Check if backup file exists
        backup_file = Path(backup_path)
        if not backup_file.exists():
            return {
                "success": False,
                "error": f"Backup file not found: {backup_path}"
            }

        # Read backup file (handle gzip compression)
        logger.info(f"Reading backup file: {backup_path}")
        if backup_path.endswith('.gz'):
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                backup_sql = f.read()
        else:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_sql = f.read()

        # Connect to the target database
        import asyncpg
        dsn_parts = DATABASE_URL.rsplit('/', 1)
        if len(dsn_parts) == 2:
            db_dsn = f"{dsn_parts[0]}/{database_name}"
        else:
            db_dsn = DATABASE_URL

        conn = await asyncpg.connect(db_dsn)

        try:
            # Split SQL into individual statements
            # Simple split by semicolon (this may need enhancement for complex SQL)
            statements = [s.strip() for s in backup_sql.split(';') if s.strip() and not s.strip().startswith('--')]

            # Filter statements based on options
            filtered_statements = []
            for stmt in statements:
                stmt_upper = stmt.upper()

                # Skip schema statements if data_only
                if data_only and any(keyword in stmt_upper for keyword in ['CREATE TABLE', 'DROP TABLE', 'ALTER TABLE']):
                    continue

                # Skip data statements if schema_only
                if schema_only and 'INSERT INTO' in stmt_upper:
                    continue

                # Skip comments
                if stmt.startswith('--'):
                    continue

                filtered_statements.append(stmt)

            logger.info(f"Executing {len(filtered_statements)} SQL statements")

            # Execute statements in a transaction
            executed_count = 0
            error_count = 0
            warnings = []

            async with conn.transaction():
                for i, stmt in enumerate(filtered_statements):
                    try:
                        # Skip empty statements
                        if not stmt.strip():
                            continue

                        await conn.execute(stmt)
                        executed_count += 1

                        # Log progress every 100 statements
                        if (i + 1) % 100 == 0:
                            logger.info(f"Executed {i + 1}/{len(filtered_statements)} statements")

                    except Exception as e:
                        error_msg = f"Error executing statement {i + 1}: {str(e)[:100]}"
                        logger.warning(error_msg)
                        warnings.append(error_msg)
                        error_count += 1

                        # If clean mode, continue on errors; otherwise, might want to stop
                        if not clean and error_count > 10:
                            raise Exception(f"Too many errors during restore ({error_count}). Stopping.")

            logger.info(f"Restore completed for database '{database_name}'")
            return {
                "success": True,
                "message": f"Database '{database_name}' restored successfully using SQL-based method",
                "database_name": database_name,
                "backup_path": backup_path,
                "statements_executed": executed_count,
                "errors": error_count,
                "warnings": warnings if warnings else None,
                "note": "Restore completed using SQL-based method (no pg_restore required)"
            }

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Error during restore: {e}")
        return {
            "success": False,
            "error": f"Restore failed: {str(e)}",
            "note": "SQL-based restore method used. For advanced features, install PostgreSQL client tools (pg_restore)."
        }


async def handle_list_backups(arguments: dict) -> dict:
    """Handle listing backup files in a directory"""
    from pathlib import Path
    import fnmatch
    from datetime import datetime

    backup_directory = arguments.get("backup_directory")
    pattern = arguments.get("pattern", "*")

    try:
        backup_dir = Path(backup_directory)

        # Check if directory exists
        if not backup_dir.exists():
            return {
                "success": False,
                "error": f"Backup directory not found: {backup_directory}"
            }

        if not backup_dir.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {backup_directory}"
            }

        # Get all files matching pattern
        all_files = list(backup_dir.iterdir())
        matching_files = [
            f for f in all_files
            if f.is_file() and fnmatch.fnmatch(f.name, pattern)
        ]

        # Build backup info list
        backups = []
        for backup_file in sorted(matching_files, key=lambda x: x.stat().st_mtime, reverse=True):
            stat = backup_file.stat()

            # Determine format from extension
            extension = backup_file.suffix.lower()
            format_guess = {
                '.sql': 'plain SQL',
                '.dump': 'custom',
                '.tar': 'tar',
                '.backup': 'custom'
            }.get(extension, 'unknown')

            backups.append({
                "filename": backup_file.name,
                "full_path": str(backup_file),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "size_human": _format_file_size(stat.st_size),
                "format": format_guess,
                "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })

        return {
            "success": True,
            "backup_directory": backup_directory,
            "backup_count": len(backups),
            "backups": backups
        }

    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        return {
            "success": False,
            "error": f"Failed to list backups: {str(e)}"
        }


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


async def handle_check_backup_tools(arguments: dict) -> dict:
    """Check if PostgreSQL backup/restore tools are available"""
    import subprocess
    import shutil

    try:
        tools_status = check_pg_tools_available()

        # Try to get version information for each tool
        tool_versions = {}

        for tool_name, is_available in tools_status.items():
            if is_available:
                try:
                    result = subprocess.run(
                        [tool_name, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        version_line = result.stdout.strip().split('\n')[0]
                        tool_versions[tool_name] = version_line
                    else:
                        tool_versions[tool_name] = "Available (version unknown)"
                except Exception as e:
                    tool_versions[tool_name] = f"Available (error getting version: {str(e)})"
            else:
                tool_versions[tool_name] = "Not found in PATH"

        # Determine overall status
        all_available = all(tools_status.values())
        backup_available = tools_status.get('pg_dump', False)
        restore_available = tools_status.get('pg_restore', False) or tools_status.get('psql', False)

        recommendations = []
        if not all_available:
            recommendations.append("Install PostgreSQL client tools to enable pg_dump/pg_restore functionality")
            if sys.platform == "win32":
                recommendations.append("Windows: Download from https://www.postgresql.org/download/windows/")
            elif sys.platform == "darwin":
                recommendations.append("macOS: Run 'brew install postgresql'")
            else:
                recommendations.append("Linux: Run 'sudo apt-get install postgresql-client' (Debian/Ubuntu) or 'sudo yum install postgresql' (RHEL/CentOS)")

        return {
            "success": True,
            "tools_available": {
                "pg_dump": tools_status.get('pg_dump', False),
                "pg_restore": tools_status.get('pg_restore', False),
                "psql": tools_status.get('psql', False)
            },
            "tool_details": tool_versions,
            "can_backup_with_pg_dump": backup_available,
            "can_restore_with_pg_tools": restore_available,
            "all_tools_available": all_available,
            "recommendations": recommendations if recommendations else ["All PostgreSQL tools are available"],
            "fallback_methods": {
                "backup": "SQL-based backup available (works without pg_dump)",
                "restore": "SQL-based restore available for .sql files (works without pg_restore)"
            }
        }

    except Exception as e:
        logger.error(f"Error checking backup tools: {e}")
        return {
            "success": False,
            "error": f"Failed to check backup tools: {str(e)}"
        }


async def main():
    """Main entry point for the MCP server"""
    logger.info("Starting Enterprise PostgreSQL MCP Server...")

    # Initialize database pool
    await db_manager.initialize()

    try:
        # Run the stdio server
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP Server running on stdio")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    finally:
        # Cleanup
        await db_manager.close()
        logger.info("MCP Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
