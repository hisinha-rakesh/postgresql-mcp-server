"""
Database Management Tools
Handles CREATE DATABASE, DROP DATABASE, LIST DATABASES operations
"""

import logging
import asyncpg
from mcp.types import Tool

logger = logging.getLogger("mcp-postgres-server")


database_tools = [
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

]


# Handler functions - will be called from server.py with necessary parameters

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

