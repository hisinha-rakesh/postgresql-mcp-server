#!/usr/bin/env python3
"""Test script for the query_table endpoint"""

import requests
import json

# The URL where your mcp_postgres_server is running
MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/query_table"

def test_query(query: str):
    """
    Send a natural language query to the MCP server's query endpoint
    """
    print("=" * 70)
    print(f"Testing query: '{query}'")
    print("=" * 70)

    try:
        payload = {"query": query}
        response = requests.post(MCP_SERVER_URL, json=payload, timeout=30)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n[OK] Success!")
            print(f"Generated SQL: {result.get('generated_sql')}")
            print(f"Row Count: {result.get('row_count')}")
            print("\nData:")
            print(json.dumps(result.get('data'), indent=2))
        else:
            print(f"\n[X] Error: {response.status_code}")
            print(response.json())

    except requests.exceptions.RequestException as e:
        print(f"\n[X] Connection error: {e}")
        print("\nMake sure your server is running:")
        print("  uvicorn mcp_postgres_server:app --reload --host 127.0.0.1 --port 8000")

    print("=" * 70)
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("MCP Query Table Test Script")
    print("=" * 70)
    print("\nMake sure the server is running before executing tests!")
    print("=" * 70 + "\n")

    # Test 1: List tables
    test_query("show me list of tables in the database")

    # Test 2: Query specific data (adjust table name based on your schema)
    test_query("show me all data from the users table")

    # Test 3: Query with filter (adjust based on your schema)
    test_query("show me users where status is active")

    print("\n" + "=" * 70)
    print("Tests Complete!")
    print("=" * 70)
