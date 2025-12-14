#!/usr/bin/env python3
"""
Test script to verify psql connection with proper password handling
"""

import os
import subprocess
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 80)
print("Testing psql Connection Configuration")
print("=" * 80)
print()

# Parse the URL
parsed = urllib.parse.urlparse(DATABASE_URL)

print("Connection Details:")
print(f"  Hostname: {parsed.hostname}")
print(f"  Port: {parsed.port}")
print(f"  Username (raw): {parsed.username}")
print(f"  Username (decoded): {urllib.parse.unquote(parsed.username) if parsed.username else None}")
print(f"  Password (decoded): {urllib.parse.unquote(parsed.password)[:3]}*** (masked)")
print(f"  Database: {parsed.path.lstrip('/')}")
print()

# Parse query parameters
query_params = urllib.parse.parse_qs(parsed.query) if parsed.query else {}
sslmode = query_params.get('sslmode', ['prefer'])[0]
print(f"SSL Mode: {sslmode}")
print()

# Build psql command
psql_cmd = ["psql"]

if parsed.hostname:
    psql_cmd.extend(["-h", parsed.hostname])
if parsed.port:
    psql_cmd.extend(["-p", str(parsed.port)])
if parsed.username:
    username = urllib.parse.unquote(parsed.username)
    psql_cmd.extend(["-U", username])

# Add database name
database_name = parsed.path.lstrip('/')
psql_cmd.extend(["-d", database_name])

# Add simple query to test connection
psql_cmd.extend(["-c", "SELECT version();"])

print("Command that will be executed:")
print(" ".join(psql_cmd))
print()

# Set environment variables
env = os.environ.copy()
if parsed.password:
    password = urllib.parse.unquote(parsed.password)
    env["PGPASSWORD"] = password

if 'azure.com' in (parsed.hostname or '') or sslmode in ['require', 'verify-ca', 'verify-full']:
    env["PGSSLMODE"] = sslmode

print("Environment variables:")
print(f"  PGPASSWORD: ***masked***")
print(f"  PGSSLMODE: {env.get('PGSSLMODE', 'not set')}")
print()

# Try to execute
print("=" * 80)
print("Attempting to connect with psql...")
print("=" * 80)
print()

try:
    result = subprocess.run(
        psql_cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0:
        print("SUCCESS! Connection working!")
        print()
        print("Output:")
        print(result.stdout)
    else:
        print("FAILED! Connection error")
        print()
        print("Error output:")
        print(result.stderr)
        print()
        print("Return code:", result.returncode)

except subprocess.TimeoutExpired:
    print("TIMEOUT! Connection attempt timed out after 30 seconds")
except FileNotFoundError:
    print("ERROR! psql command not found in PATH")
    print()
    print("Please ensure PostgreSQL client tools are installed:")
    print("  Windows: Download from https://www.postgresql.org/download/windows/")
    print("  macOS: brew install postgresql")
    print("  Linux: sudo apt-get install postgresql-client")
except Exception as e:
    print(f"ERROR! Unexpected error: {e}")

print()
print("=" * 80)
print("Test completed")
print("=" * 80)
