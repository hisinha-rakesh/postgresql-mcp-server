#!/usr/bin/env python3
"""
Test pg_dump with connection URI format instead of separate parameters
"""

import os
import subprocess
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 80)
print("Testing pg_dump with Connection URI Format")
print("=" * 80)
print()

# Parse the URL
parsed = urllib.parse.urlparse(DATABASE_URL)

# Build connection URI for a specific database (e.g., library)
username = urllib.parse.quote(urllib.parse.unquote(parsed.username))
password = urllib.parse.quote(urllib.parse.unquote(parsed.password))
hostname = parsed.hostname
port = parsed.port or 5432
database = "library"  # Test with library database

# Build URI with properly encoded components
connection_uri = f"postgresql://{username}:{password}@{hostname}:{port}/{database}?sslmode=require"

print("Connection URI (password masked):")
masked_uri = f"postgresql://{username}:***@{hostname}:{port}/{database}?sslmode=require"
print(masked_uri)
print()

# Build pg_dump command using URI
backup_file = "test_uri_backup.dump"
pg_dump_cmd = [
    "pg_dump",
    connection_uri,
    "-F", "c",
    "-f", backup_file,
    "--verbose"
]

print("Command to execute:")
print(f"pg_dump {masked_uri} -F c -f {backup_file} --verbose")
print()

# Execute
print("=" * 80)
print("Executing pg_dump with URI format...")
print("=" * 80)
print()

try:
    result = subprocess.run(
        pg_dump_cmd,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode == 0:
        print("SUCCESS! Backup completed using connection URI format")
        print()
        print("This means the MCP server should use connection URI format instead of")
        print("separate parameters with PGPASSWORD environment variable.")
        print()
        if os.path.exists(backup_file):
            size = os.path.getsize(backup_file)
            print(f"Backup file created: {backup_file} ({size} bytes)")
    else:
        print("FAILED! Still getting authentication error")
        print()
        print("Error output:")
        print(result.stderr)
        print()
        print("This suggests the issue is not just about parameter format.")

except subprocess.TimeoutExpired:
    print("TIMEOUT! Command took longer than 60 seconds")
except FileNotFoundError:
    print("ERROR! pg_dump not found in PATH")
except Exception as e:
    print(f"ERROR! {e}")

print()
print("=" * 80)
print("Test completed")
print("=" * 80)
