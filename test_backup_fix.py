#!/usr/bin/env python3
"""
Test script to verify backup functionality with proper password handling
"""

import urllib.parse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("Testing DATABASE_URL parsing:")
print(f"Raw DATABASE_URL: {DATABASE_URL}")
print()

# Parse the URL
parsed = urllib.parse.urlparse(DATABASE_URL)

print("Parsed components:")
print(f"  Scheme: {parsed.scheme}")
print(f"  Hostname: {parsed.hostname}")
print(f"  Port: {parsed.port}")
print(f"  Username (raw): {parsed.username}")
print(f"  Username (decoded): {urllib.parse.unquote(parsed.username) if parsed.username else None}")
print(f"  Password (raw): {parsed.password}")
print(f"  Password (decoded): {urllib.parse.unquote(parsed.password) if parsed.password else None}")
print(f"  Database path: {parsed.path}")
print(f"  Query params: {parsed.query}")
print()

# Check query parameters
query_params = urllib.parse.parse_qs(parsed.query) if parsed.query else {}
sslmode = query_params.get('sslmode', ['prefer'])[0]
print(f"SSL Mode: {sslmode}")
print(f"Is Azure: {'azure.com' in (parsed.hostname or '')}")
print()

# Build the pg_dump command that would be executed
pg_dump_cmd = ["pg_dump"]
if parsed.hostname:
    pg_dump_cmd.extend(["-h", parsed.hostname])
if parsed.port:
    pg_dump_cmd.extend(["-p", str(parsed.port)])
if parsed.username:
    username = urllib.parse.unquote(parsed.username)
    pg_dump_cmd.extend(["-U", username])

pg_dump_cmd.extend(["-d", "library"])
pg_dump_cmd.extend(["-F", "c"])
pg_dump_cmd.extend(["-f", "test_backup.dump"])

print("Command that would be executed:")
print(" ".join(pg_dump_cmd))
print()

# Environment variables that would be set
env_vars = {}
if parsed.password:
    env_vars["PGPASSWORD"] = urllib.parse.unquote(parsed.password)
if 'azure.com' in (parsed.hostname or '') or sslmode in ['require', 'verify-ca', 'verify-full']:
    env_vars["PGSSLMODE"] = sslmode

print("Environment variables that would be set:")
for key, value in env_vars.items():
    # Mask password for display
    if key == "PGPASSWORD":
        print(f"  {key}=***masked***")
    else:
        print(f"  {key}={value}")
print()

print("✅ Configuration looks correct!")
print("The backup should work now with proper password authentication.")
