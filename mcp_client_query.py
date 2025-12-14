# mcp_client_query.py
# Test client for the query_table endpoint

import requests
import json

# The URL where your mcp_postgres_server is running
MCP_QUERY_URL = "http://127.0.0.1:8000/mcp/query_table"

def query_database_with_natural_language(query: str) -> dict:
    """
    Acts as a tool to send a natural language SELECT query to the MCP PostgreSQL server.

    Args:
        query: A string containing the natural language query for the database.

    Returns:
        A dictionary containing the server's response with data.
    """
    print(f"CLIENT: Sending query to server: '{query}'")
    try:
        payload = {"query": query}
        response = requests.post(MCP_QUERY_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"CLIENT: An error occurred while communicating with the server: {e}")
        return {
            "error": "Failed to communicate with the MCP server.",
            "details": str(e)
        }
    except json.JSONDecodeError:
        return {
            "error": "Failed to decode the server's response.",
            "details": response.text
        }


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("MCP PostgreSQL Query Client")
    print("=" * 70)
    print("IMPORTANT: Make sure mcp_postgres_server.py is running!\n")

    # Example 1: List all tables
    print("=" * 70)
    print("Example 1: List all tables in the database")
    print("=" * 70)
    query1 = "show me list of all tables in the database"
    result1 = query_database_with_natural_language(query1)

    print("\n--- CLIENT: Received response ---")
    print(json.dumps(result1, indent=2))
    print("-" * 70 + "\n")

    # Example 2: Query information_schema
    print("=" * 70)
    print("Example 2: Show table schemas")
    print("=" * 70)
    query2 = "show me table names and their column counts from information_schema"
    result2 = query_database_with_natural_language(query2)

    print("\n--- CLIENT: Received response ---")
    print(json.dumps(result2, indent=2))
    print("-" * 70 + "\n")

    # Example 3: Try an invalid query (should be rejected)
    print("=" * 70)
    print("Example 3: Try an UPDATE query (should fail)")
    print("=" * 70)
    query3 = "update users set status to active"
    result3 = query_database_with_natural_language(query3)

    print("\n--- CLIENT: Received response (should show error) ---")
    print(json.dumps(result3, indent=2))
    print("-" * 70 + "\n")

    print("=" * 70)
    print("Testing Complete!")
    print("=" * 70)
