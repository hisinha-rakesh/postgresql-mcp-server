#!/usr/bin/env python3
"""
Test password decoding
"""

import os
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("Testing Password Decoding")
print("=" * 80)
print()

# Parse the URL
parsed = urllib.parse.urlparse(DATABASE_URL)

print(f"Raw DATABASE_URL: {DATABASE_URL}")
print()

print("Parsed components:")
print(f"  Username (raw): '{parsed.username}'")
print(f"  Username (decoded): '{urllib.parse.unquote(parsed.username)}'")
print(f"  Password (raw): '{parsed.password}'")
print(f"  Password (decoded): '{urllib.parse.unquote(parsed.password)}'")
print()

# Show byte representation
if parsed.password:
    password_decoded = urllib.parse.unquote(parsed.password)
    print("Password details:")
    print(f"  Length: {len(password_decoded)}")
    print(f"  Bytes: {password_decoded.encode('utf-8')}")
    print(f"  First 3 chars: {password_decoded[:3]}")
    print(f"  Contains @: {'@' in password_decoded}")
print()

# Test what happens when you manually enter it
print("Expected password for manual entry: Centurylink@123")
print()

# Check if they match
manual_password = "Centurylink@123"
decoded_password = urllib.parse.unquote(parsed.password)

if manual_password == decoded_password:
    print("✓ Decoded password MATCHES the manual password!")
else:
    print("✗ Decoded password DOES NOT MATCH the manual password!")
    print(f"  Expected: '{manual_password}'")
    print(f"  Got:      '{decoded_password}'")
