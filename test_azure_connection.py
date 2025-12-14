#!/usr/bin/env python3
"""
Test Azure PostgreSQL Connection
This script tests the connection to Azure PostgreSQL with proper SSL configuration
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def test_connection():
    """Test the database connection"""
    print("=" * 60)
    print("Azure PostgreSQL Connection Test")
    print("=" * 60)

    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL not found in .env file")
        return False

    print(f"\n[Connection Details]")
    print(f"   DATABASE_URL: {DATABASE_URL[:40]}...")

    try:
        print("\n[Attempting to connect to Azure PostgreSQL...]")
        conn = await asyncpg.connect(DATABASE_URL)

        print("[SUCCESS] Connection successful!")

        # Test query
        print("\n[Testing query execution...]")
        version = await conn.fetchval("SELECT version()")
        print(f"[SUCCESS] PostgreSQL Version: {version[:80]}...")

        # List databases
        print("\n[Listing databases...]")
        databases = await conn.fetch("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname
        """)

        print(f"[SUCCESS] Found {len(databases)} databases:")
        for db in databases:
            print(f"   - {db['datname']}: {db['size']}")

        await conn.close()
        print("\n[SUCCESS] All tests passed! Connection is working correctly.")
        return True

    except asyncpg.exceptions.InvalidPasswordError:
        print("\n[ERROR] Authentication failed!")
        print("   Check your username and password in DATABASE_URL")
        print("   Remember: Azure PostgreSQL username format is 'username@servername'")
        return False

    except asyncpg.exceptions.InvalidCatalogNameError as e:
        print(f"\n[ERROR] Database not found: {e}")
        print("   Check the database name in your DATABASE_URL")
        return False

    except Exception as e:
        print(f"\n[ERROR] Connection failed!")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
