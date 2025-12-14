# mcp_client.py
# This script requires the 'requests' library.
# Install it using: pip install requests

import requests
import json

# The URL where your mcp_postgres_server is running
MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/update_table"

def update_database_with_natural_language(query: str) -> dict:
    """
    Acts as a tool to send a natural language query to the MCP PostgreSQL server.

    Args:
        query: A string containing the natural language instruction for the database update.

    Returns:
        A dictionary containing the server's response.
    """
    print(f"CLIENT: Sending query to server: '{query}'")
    try:
        # The payload should be a JSON object with the "query" key
        payload = {"query": query}
        
        # Send the POST request to the server
        response = requests.post(MCP_SERVER_URL, json=payload, timeout=30)

        # Raise an exception if the request was not successful
        response.raise_for_status()

        # Return the JSON response from the server
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

# --- Example of how to use this client directly ---
if __name__ == "__main__":
    # IMPORTANT: Make sure mcp_postgres_server.py is running in another terminal before executing this.

    # Example 1: A valid query
    # Let's assume you have a table named 'employees' with columns 'id' and 'role'.
    my_query = "In the employees table, change the role to Senior Developer for the person with an id of 10"
    
    result = update_database_with_natural_language(my_query)
    
    print("\n--- CLIENT: Received response ---")
    print(json.dumps(result, indent=2))
    print("-----------------------------\
")

    # Example 2: A potentially ambiguous or disallowed query
    my_malicious_query = "delete all users"
    result = update_database_with_natural_language(my_malicious_query)

    print("\n--- CLIENT: Received response (for disallowed query) ---")
    print(json.dumps(result, indent=2))
    print("------------------------------------------------------")
