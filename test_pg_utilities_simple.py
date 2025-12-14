#!/usr/bin/env python3
"""
Simple test for PostgreSQL utilities (pg_dump, pg_restore, psql)
without importing MCP server modules
"""

import os
import subprocess
import shutil
import asyncio
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 80)
print("Testing PostgreSQL Utilities (psql, pg_dump, pg_restore)")
print("=" * 80)
print()

# Test 1: Check if tools are available
print("Test 1: Checking if PostgreSQL tools are installed")
print("-" * 80)

tools = {
    'pg_dump': shutil.which('pg_dump') is not None,
    'pg_restore': shutil.which('pg_restore') is not None,
    'psql': shutil.which('psql') is not None
}

for tool, available in tools.items():
    status = "✓ FOUND" if available else "✗ NOT FOUND"
    print(f"  {tool}: {status}")

    if available:
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip().split('\n')[0]
            print(f"    Version: {version}")
        except:
            pass

print()

if not all(tools.values()):
    print("WARNING: Not all PostgreSQL tools are installed!")
    print()

# Test 2: Parse DATABASE_URL
print("Test 2: Verifying DATABASE_URL configuration")
print("-" * 80)
parsed = urllib.parse.urlparse(DATABASE_URL)
username = urllib.parse.unquote(parsed.username)
password = urllib.parse.unquote(parsed.password)
hostname = parsed.hostname
port = parsed.port or 5432
database = parsed.path.lstrip('/')

print(f"Hostname: {hostname}")
print(f"Port: {port}")
print(f"Username: {username}")
print(f"Password: {password[:3]}*** (masked)")
print(f"Database: {database}")

query_params = urllib.parse.parse_qs(parsed.query) if parsed.query else {}
sslmode = query_params.get('sslmode', ['prefer'])[0]
print(f"SSL Mode: {sslmode}")
print()

# Test 3: Test psql connection
print("Test 3: Testing psql connection")
print("-" * 80)

if tools['psql']:
    try:
        # Build psql command
        psql_cmd = [
            "psql",
            f"host={hostname}",
            f"port={port}",
            f"user={username}",
            f"dbname={database}",
            f"sslmode={sslmode}",
            "-c", "SELECT 'psql connection successful!' as status, version();"
        ]

        print(f"Executing: psql (connection string) -c 'SELECT...'")
        print()

        result = subprocess.run(
            psql_cmd,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            print("✓ SUCCESS! psql connection working")
            print()
            print("Output:")
            print(result.stdout)
            psql_success = True
        else:
            print("✗ FAILED! psql connection failed")
            print()
            print("Error:")
            print(result.stderr)
            psql_success = False

    except subprocess.TimeoutExpired:
        print("✗ TIMEOUT! psql connection timed out")
        psql_success = False
    except Exception as e:
        print(f"✗ EXCEPTION! {e}")
        psql_success = False
else:
    print("✗ SKIPPED - psql not installed")
    psql_success = False

print()

# Test 4: Test pg_dump backup
print("Test 4: Testing pg_dump backup")
print("-" * 80)

if tools['pg_dump']:
    try:
        # Test with library database
        test_database = "library"
        test_backup_file = "test_pg_utilities_backup.dump"

        pg_dump_cmd = [
            "pg_dump",
            "-h", hostname,
            "-p", str(port),
            "-U", username,
            "-d", test_database,
            "-F", "c",
            "-f", test_backup_file,
            "--verbose"
        ]

        # Set environment variables
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        env["PGSSLMODE"] = sslmode

        print(f"Backing up database: {test_database}")
        print(f"Backup file: {test_backup_file}")
        print()

        result = subprocess.run(
            pg_dump_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("✓ SUCCESS! pg_dump backup completed")

            # Check file
            if Path(test_backup_file).exists():
                size = Path(test_backup_file).stat().st_size
                size_mb = size / (1024 * 1024)
                print(f"  Backup file: {test_backup_file}")
                print(f"  File size: {size_mb:.2f} MB")
                print(f"  ✓ File verified on disk")
                pg_dump_success = True
            else:
                print("  ✗ Backup file NOT found")
                pg_dump_success = False
        else:
            print("✗ FAILED! pg_dump backup failed")
            print()
            print("Error:")
            print(result.stderr[:500])  # First 500 chars
            pg_dump_success = False

    except subprocess.TimeoutExpired:
        print("✗ TIMEOUT! pg_dump timed out")
        pg_dump_success = False
    except Exception as e:
        print(f"✗ EXCEPTION! {e}")
        pg_dump_success = False
else:
    print("✗ SKIPPED - pg_dump not installed")
    pg_dump_success = False

print()

# Test 5: Test pg_restore
print("Test 5: Testing pg_restore (check only, no actual restore)")
print("-" * 80)

if tools['pg_restore'] and pg_dump_success and Path(test_backup_file).exists():
    try:
        # Just test if we can read the backup file
        pg_restore_cmd = [
            "pg_restore",
            "--list",
            test_backup_file
        ]

        print(f"Reading backup file: {test_backup_file}")
        print()

        result = subprocess.run(
            pg_restore_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("✓ SUCCESS! pg_restore can read the backup file")
            lines = result.stdout.strip().split('\n')
            print(f"  Backup contains {len(lines)} objects")
            pg_restore_success = True
        else:
            print("✗ FAILED! pg_restore cannot read backup file")
            print()
            print("Error:")
            print(result.stderr[:500])
            pg_restore_success = False

    except subprocess.TimeoutExpired:
        print("✗ TIMEOUT! pg_restore timed out")
        pg_restore_success = False
    except Exception as e:
        print(f"✗ EXCEPTION! {e}")
        pg_restore_success = False
else:
    print("✗ SKIPPED - pg_restore not installed or no backup file")
    pg_restore_success = False

print()

# Test 6: Test asyncpg connection
print("Test 6: Testing asyncpg connection (Python PostgreSQL driver)")
print("-" * 80)

async def test_asyncpg():
    try:
        import asyncpg

        print(f"Connecting to: {hostname}")
        print(f"Database: {database}")
        print()

        conn = await asyncpg.connect(
            host=hostname,
            port=port,
            user=username,
            password=password,
            database=database,
            ssl='require'
        )

        try:
            # Execute a simple query
            version = await conn.fetchval("SELECT version()")
            print("✓ SUCCESS! asyncpg connection working")
            print(f"  PostgreSQL: {version.split(',')[0]}")

            # List databases
            databases = await conn.fetch(
                "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"
            )
            db_list = [db['datname'] for db in databases]
            print(f"  Databases: {', '.join(db_list)}")

            return True
        finally:
            await conn.close()

    except ImportError:
        print("✗ SKIPPED - asyncpg module not installed")
        print("  Install with: pip install asyncpg")
        return False
    except Exception as e:
        print(f"✗ FAILED! asyncpg connection failed")
        print(f"  Error: {e}")
        return False

asyncpg_success = asyncio.run(test_asyncpg())
print()

# Final Summary
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print()

test_results = {
    "psql connection": psql_success if tools['psql'] else None,
    "pg_dump backup": pg_dump_success if tools['pg_dump'] else None,
    "pg_restore read": pg_restore_success if tools['pg_restore'] else None,
    "asyncpg connection": asyncpg_success
}

for test_name, result in test_results.items():
    if result is True:
        status = "✓ PASS"
    elif result is False:
        status = "✗ FAIL"
    else:
        status = "⊘ SKIP"
    print(f"{status} - {test_name}")

print()

all_critical_passed = all([
    psql_success if tools['psql'] else False,
    pg_dump_success if tools['pg_dump'] else False,
    asyncpg_success
])

if all_critical_passed:
    print("=" * 80)
    print("✓ ALL CRITICAL TESTS PASSED!")
    print("=" * 80)
    print()
    print("The MCP server should work correctly!")
    print()
    print("You can now use Claude Desktop to:")
    print("  • Backup databases")
    print("  • Restore databases")
    print("  • Query and manipulate data")
    print("  • Create/modify tables")
else:
    print("=" * 80)
    print("✗ SOME TESTS FAILED")
    print("=" * 80)
    print()
    print("Review the errors above to troubleshoot.")

print()
print("Test completed!")
