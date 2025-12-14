#!/usr/bin/env python3
"""
Test pg_dump backup with Azure PostgreSQL
"""

import os
import sys
import subprocess
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def test_pg_dump():
    """Test pg_dump backup"""
    print("=" * 60)
    print("Testing pg_dump Backup for Azure PostgreSQL")
    print("=" * 60)

    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL not found")
        return False

    # Parse DATABASE_URL
    parsed = urllib.parse.urlparse(DATABASE_URL)

    print(f"\n[Connection Info]")
    print(f"   Host: {parsed.hostname}")
    print(f"   Port: {parsed.port}")
    print(f"   Username: {parsed.username}")
    print(f"   Database: postgres")

    # Create backup directory
    backup_dir = Path("C:/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / "test_backup.dump"

    print(f"\n[Backup Path]: {backup_path}")

    # Build pg_dump command
    pg_dump_cmd = [
        "pg_dump",
        "-h", parsed.hostname,
        "-p", str(parsed.port),
        "-U", parsed.username,
        "-d", "postgres",
        "-F", "c",  # Custom format
        "-Z", "6",  # Compression level
        "-f", str(backup_path),
        "--verbose"
    ]

    # Set environment variables
    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = urllib.parse.unquote(parsed.password)

    # Parse SSL mode from URL
    query_params = urllib.parse.parse_qs(parsed.query) if parsed.query else {}
    sslmode = query_params.get('sslmode', ['require'])[0]
    env["PGSSLMODE"] = sslmode

    print(f"\n[SSL Mode]: {sslmode}")
    print(f"\n[Executing pg_dump...]")
    print(f"Command: {' '.join(pg_dump_cmd[:10])}...")

    try:
        result = subprocess.run(
            pg_dump_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            # Check file size
            if backup_path.exists():
                file_size = backup_path.stat().st_size
                file_size_mb = file_size / (1024 * 1024)

                print(f"\n[SUCCESS] Backup completed!")
                print(f"   File: {backup_path}")
                print(f"   Size: {file_size_mb:.2f} MB")
                return True
            else:
                print(f"\n[ERROR] Backup file not created")
                return False
        else:
            print(f"\n[ERROR] pg_dump failed!")
            print(f"\nSTDERR:\n{result.stderr}")
            print(f"\nSTDOUT:\n{result.stdout}")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n[ERROR] Backup timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"\n[ERROR] Exception occurred: {e}")
        return False

if __name__ == "__main__":
    success = test_pg_dump()
    sys.exit(0 if success else 1)
