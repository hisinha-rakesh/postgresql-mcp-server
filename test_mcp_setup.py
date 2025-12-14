#!/usr/bin/env python3
"""
Quick test script to verify MCP server setup
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    """Test database connection"""
    DATABASE_URL = os.getenv("DATABASE_URL")

    print("Testing database connection...")
    print(f"Database URL: {DATABASE_URL[:50]}...")

    try:
        # Try to connect
        conn = await asyncpg.connect(DATABASE_URL)
        print("[OK] Successfully connected to database!")

        # Test a simple query
        version = await conn.fetchval('SELECT version()')
        print(f"[OK] PostgreSQL version: {version[:80]}...")

        # List tables
        tables = await conn.fetch("""
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        print(f"\n[INFO] Found {len(tables)} tables in 'public' schema:")
        for table in tables[:10]:  # Show first 10
            print(f"   - {table['tablename']}")

        if len(tables) > 10:
            print(f"   ... and {len(tables) - 10} more")

        await conn.close()
        print("\n[OK] Database connection test passed!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Database connection failed: {e}")
        return False

async def main():
    print("="*60)
    print("MCP SERVER SETUP VERIFICATION")
    print("="*60)
    print()

    success = await test_connection()

    print("\n" + "="*60)
    if success:
        print("[SUCCESS] ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Configure Claude Desktop (see instructions below)")
        print("2. Restart Claude Desktop")
        print("3. Start using the MCP server!")
    else:
        print("[FAILED] TESTS FAILED!")
        print("\nPlease check:")
        print("1. DATABASE_URL in .env file is correct")
        print("2. Database is accessible from your network")
        print("3. Credentials are valid")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
