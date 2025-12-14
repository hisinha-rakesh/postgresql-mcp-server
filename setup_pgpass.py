#!/usr/bin/env python3
"""
Setup .pgpass file for PostgreSQL password authentication
"""

import os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 80)
print("Setting up .pgpass file for PostgreSQL")
print("=" * 80)
print()

# Parse DATABASE_URL
parsed = urllib.parse.urlparse(DATABASE_URL)

hostname = parsed.hostname
port = parsed.port or 5432
username = urllib.parse.unquote(parsed.username)
password = urllib.parse.unquote(parsed.password)

print("Extracted credentials:")
print(f"  Hostname: {hostname}")
print(f"  Port: {port}")
print(f"  Username: {username}")
print(f"  Password: {password[:3]}*** (masked)")
print()

# Determine .pgpass file location based on OS
if os.name == 'nt':  # Windows
    pgpass_dir = Path(os.environ['APPDATA']) / 'postgresql'
    pgpass_file = pgpass_dir / 'pgpass.conf'
else:  # Linux/Mac
    pgpass_file = Path.home() / '.pgpass'
    pgpass_dir = pgpass_file.parent

print(f"Pgpass file location: {pgpass_file}")
print()

# Create directory if it doesn't exist
if not pgpass_dir.exists():
    print(f"Creating directory: {pgpass_dir}")
    pgpass_dir.mkdir(parents=True, exist_ok=True)

# Create .pgpass entry
# Format: hostname:port:database:username:password
# Use * for database to apply to all databases
pgpass_entry = f"{hostname}:{port}:*:{username}:{password}"

print("Pgpass entry (password masked):")
print(f"{hostname}:{port}:*:{username}:***")
print()

# Check if file exists
if pgpass_file.exists():
    print(f"File {pgpass_file} already exists")

    # Read existing content
    with open(pgpass_file, 'r') as f:
        existing_content = f.read()

    # Check if entry already exists
    if hostname in existing_content and username in existing_content:
        print("Entry for this server and user already exists")
        response = input("Do you want to update it? (y/n): ")
        if response.lower() != 'y':
            print("Skipping update")
            print()
            print("=" * 80)
            print("Setup completed (no changes made)")
            print("=" * 80)
            exit(0)

        # Remove old entry
        lines = existing_content.split('\n')
        new_lines = [line for line in lines if not (hostname in line and username in line)]
        existing_content = '\n'.join(new_lines)

    # Append new entry
    with open(pgpass_file, 'w') as f:
        if existing_content and not existing_content.endswith('\n'):
            f.write(existing_content + '\n')
        elif existing_content:
            f.write(existing_content)
        f.write(pgpass_entry + '\n')

    print("Updated existing .pgpass file")
else:
    # Create new file
    with open(pgpass_file, 'w') as f:
        f.write(pgpass_entry + '\n')

    print(f"Created new .pgpass file: {pgpass_file}")

# Set permissions on Unix-like systems
if os.name != 'nt':
    os.chmod(pgpass_file, 0o600)
    print("Set file permissions to 600 (user read/write only)")

print()
print("=" * 80)
print("SUCCESS! .pgpass file setup completed")
print("=" * 80)
print()
print("Now you can run psql, pg_dump, and pg_restore without password prompts:")
print(f"  psql -h {hostname} -U \"{username}\" -d postgres")
print(f"  pg_dump -h {hostname} -U \"{username}\" -d library -F c -f backup.dump")
print()
print("The MCP server will also use this .pgpass file automatically!")
