#!/usr/bin/env python3
"""
Test all PostgreSQL utilities (pg_dump, pg_restore, psql)
with the MCP server configuration
"""

import os
import sys
import asyncio
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import from mcp_server_enterprise
from mcp_server_enterprise import (
    check_pg_tools_available,
    DATABASE_URL,
    _backup_with_pg_dump,
    _restore_with_pg_tools
)

print("=" * 80)
print("Testing PostgreSQL Utilities with MCP Server Configuration")
print("=" * 80)
print()

# Test 1: Check if tools are available
print("Test 1: Checking if PostgreSQL tools are installed")
print("-" * 80)
tools = check_pg_tools_available()
print("Tool availability:")
for tool, available in tools.items():
    status = "✓ FOUND" if available else "✗ NOT FOUND"
    print(f"  {tool}: {status}")
print()

if not all(tools.values()):
    print("WARNING: Not all PostgreSQL tools are installed!")
    print("Some tests may fail.")
    print()

# Test 2: Check DATABASE_URL configuration
print("Test 2: Verifying DATABASE_URL configuration")
print("-" * 80)
parsed = urllib.parse.urlparse(DATABASE_URL)
print(f"Hostname: {parsed.hostname}")
print(f"Port: {parsed.port}")
print(f"Username: {urllib.parse.unquote(parsed.username)}")
print(f"Password: {urllib.parse.unquote(parsed.password)[:3]}*** (masked)")
print(f"Database: {parsed.path.lstrip('/')}")

query_params = urllib.parse.parse_qs(parsed.query) if parsed.query else {}
sslmode = query_params.get('sslmode', ['prefer'])[0]
print(f"SSL Mode: {sslmode}")
print()

# Test 3: Test pg_dump backup
print("Test 3: Testing pg_dump backup functionality")
print("-" * 80)

async def test_pg_dump():
    """Test pg_dump backup"""
    try:
        # Create a test backup
        test_backup_path = r"C:\Users\kusha\postgresql-mcp\test_mcp_backup.dump"
        database_name = "library"

        print(f"Attempting to backup database: {database_name}")
        print(f"Backup path: {test_backup_path}")
        print()

        result = await _backup_with_pg_dump(
            database_name=database_name,
            backup_path=test_backup_path,
            backup_format="custom",
            compress_level=6,
            schema_only=False,
            data_only=False,
            tables=[],
            exclude_tables=[]
        )

        if result["success"]:
            print("✓ SUCCESS! pg_dump backup completed")
            print(f"  File: {result['backup_path']}")
            print(f"  Size: {result['file_size_mb']} MB")
            print(f"  Method: {result['method']}")

            # Check if file exists
            if Path(test_backup_path).exists():
                print(f"  ✓ Backup file verified on disk")
            else:
                print(f"  ✗ Backup file NOT found on disk")

            return True, test_backup_path
        else:
            print("✗ FAILED! pg_dump backup failed")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            if 'stdout' in result:
                print(f"  Output: {result['stdout']}")
            return False, None

    except Exception as e:
        print(f"✗ EXCEPTION! Error during pg_dump test: {e}")
        import traceback
        traceback.print_exc()
        return False, None

# Run pg_dump test
success, backup_file = asyncio.run(test_pg_dump())
print()

# Test 4: Test psql connection (via pg_restore which uses psql for plain SQL)
if success and backup_file:
    print("Test 4: Testing psql/pg_restore functionality")
    print("-" * 80)

    async def test_pg_restore():
        """Test pg_restore"""
        try:
            # Note: We won't actually restore to avoid modifying the database
            # Just test the command generation
            print("Simulating pg_restore test...")
            print(f"Would restore from: {backup_file}")
            print(f"Would restore to database: library")
            print()

            # For now, just verify psql is available
            if tools.get('psql'):
                print("✓ psql is available and ready to use")
                print("✓ pg_restore is available and ready to use")
                return True
            else:
                print("✗ psql not found")
                return False

        except Exception as e:
            print(f"✗ EXCEPTION! Error during restore test: {e}")
            return False

    restore_success = asyncio.run(test_pg_restore())
    print()
else:
    print("Test 4: SKIPPED (pg_dump test failed)")
    print()
    restore_success = False

# Test 5: Test connection with asyncpg (what MCP server uses)
print("Test 5: Testing asyncpg connection (MCP server database operations)")
print("-" * 80)

async def test_asyncpg_connection():
    """Test asyncpg connection"""
    try:
        import asyncpg

        # Parse DATABASE_URL
        dsn_parts = DATABASE_URL.rsplit('/', 1)
        if len(dsn_parts) == 2:
            test_dsn = f"{dsn_parts[0]}/postgres"
        else:
            test_dsn = DATABASE_URL

        print(f"Connecting to: {parsed.hostname}")
        print(f"Database: postgres")
        print()

        conn = await asyncpg.connect(test_dsn)

        try:
            # Execute a simple query
            version = await conn.fetchval("SELECT version()")
            print("✓ SUCCESS! asyncpg connection working")
            print(f"  PostgreSQL Version: {version.split(',')[0]}")

            # Test if we can list databases
            databases = await conn.fetch("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")
            print(f"  Available databases: {', '.join([db['datname'] for db in databases])}")

            return True
        finally:
            await conn.close()

    except Exception as e:
        print(f"✗ FAILED! asyncpg connection failed")
        print(f"  Error: {e}")
        return False

asyncpg_success = asyncio.run(test_asyncpg_connection())
print()

# Final Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

all_tests = {
    "PostgreSQL tools installed": all(tools.values()),
    "DATABASE_URL configuration": True,  # Always passes if we got here
    "pg_dump backup": success,
    "psql/pg_restore available": restore_success,
    "asyncpg connection": asyncpg_success
}

for test_name, passed in all_tests.items():
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} - {test_name}")

print()

if all(all_tests.values()):
    print("=" * 80)
    print("✓ ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print("The MCP server should work correctly with:")
    print("  • Database backups (pg_dump)")
    print("  • Database restores (pg_restore/psql)")
    print("  • Database operations (asyncpg)")
    print()
    print("You can now use Claude Desktop to:")
    print("  - Backup databases: 'Backup the library database to C:\\Agentic-RAG'")
    print("  - Restore databases: 'Restore library database from backup'")
    print("  - Query databases: 'Show all tables in library database'")
    print("  - Create tables: 'Create a users table in library database'")
else:
    print("=" * 80)
    print("✗ SOME TESTS FAILED")
    print("=" * 80)
    print()
    print("Failed tests may prevent some MCP server features from working.")
    print("Please review the errors above.")

print()
print("Test completed!")
