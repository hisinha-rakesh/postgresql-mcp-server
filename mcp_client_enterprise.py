#!/usr/bin/env python3
"""
Enterprise MCP Client for testing the PostgreSQL MCP Server
Demonstrates how to interact with the MCP server using the MCP SDK
"""

import asyncio
import json
import logging
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-client")


class PostgreSQLMCPClient:
    """MCP Client for PostgreSQL operations"""

    def __init__(self):
        self.session: ClientSession = None
        self.exit_stack = AsyncExitStack()

    async def connect(self, server_script_path: str = "mcp_server_enterprise.py"):
        """Connect to the MCP server"""
        logger.info("Connecting to MCP server...")

        # Server parameters for stdio connection
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
            env=None
        )

        # Create stdio client connection
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport

        # Initialize session
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        # Initialize the connection
        await self.session.initialize()

        logger.info("Connected to MCP server successfully")

    async def disconnect(self):
        """Disconnect from the MCP server"""
        await self.exit_stack.aclose()
        logger.info("Disconnected from MCP server")

    async def list_tools(self):
        """List all available tools"""
        response = await self.session.list_tools()
        return response.tools

    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool on the MCP server"""
        logger.info(f"Calling tool: {tool_name}")
        logger.debug(f"Arguments: {json.dumps(arguments, indent=2)}")

        response = await self.session.call_tool(tool_name, arguments)

        # Parse the response
        if response.content:
            result = json.loads(response.content[0].text)
            return result
        else:
            return {"error": "No content in response"}


async def demo_ddl_operations(client: PostgreSQLMCPClient):
    """Demonstrate DDL operations (CREATE, ALTER, DROP)"""
    print("\n" + "="*60)
    print("DDL OPERATIONS DEMO")
    print("="*60)

    # 1. Create a test table
    print("\n1. Creating test table 'users'...")
    result = await client.call_tool("execute_create_table", {
        "query": """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    })
    print(f"Result: {json.dumps(result, indent=2)}")

    # 2. Create an index
    print("\n2. Creating index on email column...")
    result = await client.call_tool("execute_create_index", {
        "query": "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
    })
    print(f"Result: {json.dumps(result, indent=2)}")

    # 3. Alter table - add new column
    print("\n3. Altering table - adding 'status' column...")
    result = await client.call_tool("execute_alter_table", {
        "query": "ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'"
    })
    print(f"Result: {json.dumps(result, indent=2)}")


async def demo_dml_operations(client: PostgreSQLMCPClient):
    """Demonstrate DML operations (INSERT, SELECT, UPDATE, DELETE)"""
    print("\n" + "="*60)
    print("DML OPERATIONS DEMO")
    print("="*60)

    # 1. Insert data
    print("\n1. Inserting users...")
    result = await client.call_tool("execute_insert", {
        "query": """
            INSERT INTO users (username, email, age)
            VALUES
                ('john_doe', 'john@example.com', 30),
                ('jane_smith', 'jane@example.com', 25),
                ('bob_wilson', 'bob@example.com', 35)
            RETURNING id, username, email
        """
    })
    print(f"Result: {json.dumps(result, indent=2)}")

    # 2. Select data
    print("\n2. Selecting all users...")
    result = await client.call_tool("execute_select", {
        "query": "SELECT id, username, email, age, status FROM users ORDER BY id"
    })
    print(f"Result: {json.dumps(result, indent=2)}")

    # 3. Update data with parameterized query
    print("\n3. Updating user age...")
    result = await client.call_tool("execute_update", {
        "query": "UPDATE users SET age = $1 WHERE username = $2",
        "params": [31, "john_doe"]
    })
    print(f"Result: {json.dumps(result, indent=2)}")

    # 4. Select with WHERE clause
    print("\n4. Selecting users older than 28...")
    result = await client.call_tool("execute_select", {
        "query": "SELECT username, email, age FROM users WHERE age > $1",
        "params": [28]
    })
    print(f"Result: {json.dumps(result, indent=2)}")

    # 5. Delete data
    print("\n5. Deleting a user...")
    result = await client.call_tool("execute_delete", {
        "query": "DELETE FROM users WHERE username = $1",
        "params": ["bob_wilson"]
    })
    print(f"Result: {json.dumps(result, indent=2)}")


async def demo_tcl_operations(client: PostgreSQLMCPClient):
    """Demonstrate TCL operations (Transactions)"""
    print("\n" + "="*60)
    print("TCL OPERATIONS DEMO (Transactions)")
    print("="*60)

    # Execute multiple statements in a transaction
    print("\n1. Executing transaction with multiple statements...")
    result = await client.call_tool("execute_transaction", {
        "statements": [
            {
                "query": "INSERT INTO users (username, email, age) VALUES ($1, $2, $3) RETURNING id",
                "params": ["alice_wonder", "alice@example.com", 28]
            },
            {
                "query": "INSERT INTO users (username, email, age) VALUES ($1, $2, $3) RETURNING id",
                "params": ["charlie_brown", "charlie@example.com", 32]
            },
            {
                "query": "UPDATE users SET status = $1 WHERE age > $2",
                "params": ["senior", 30]
            },
            {
                "query": "SELECT username, age, status FROM users WHERE status = $1",
                "params": ["senior"]
            }
        ],
        "isolation_level": "read_committed"
    })
    print(f"Result: {json.dumps(result, indent=2, default=str)}")


async def demo_utility_operations(client: PostgreSQLMCPClient):
    """Demonstrate utility operations (Schema info, Table info)"""
    print("\n" + "="*60)
    print("UTILITY OPERATIONS DEMO")
    print("="*60)

    # 1. Get schema information
    print("\n1. Getting schema information...")
    result = await client.call_tool("get_schema_info", {
        "schema_name": "public"
    })
    print(f"Result: {json.dumps(result, indent=2, default=str)}")

    # 2. Get specific table information
    print("\n2. Getting detailed info for 'users' table...")
    result = await client.call_tool("get_table_info", {
        "table_name": "users",
        "schema_name": "public"
    })
    print(f"Result: {json.dumps(result, indent=2, default=str)}")


async def demo_cleanup(client: PostgreSQLMCPClient):
    """Clean up test data"""
    print("\n" + "="*60)
    print("CLEANUP")
    print("="*60)

    # Drop the test table
    print("\n1. Dropping test table...")
    result = await client.call_tool("execute_drop_table", {
        "table_name": "users",
        "cascade": True,
        "if_exists": True
    })
    print(f"Result: {json.dumps(result, indent=2)}")


async def demo_complex_queries(client: PostgreSQLMCPClient):
    """Demonstrate complex query operations"""
    print("\n" + "="*60)
    print("COMPLEX QUERIES DEMO")
    print("="*60)

    # 1. Create multiple related tables
    print("\n1. Creating related tables (orders and order_items)...")
    await client.call_tool("execute_create_table", {
        "query": """
            CREATE TABLE IF NOT EXISTS orders (
                order_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(10, 2)
            )
        """
    })

    await client.call_tool("execute_create_table", {
        "query": """
            CREATE TABLE IF NOT EXISTS order_items (
                item_id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(order_id) ON DELETE CASCADE,
                product_name VARCHAR(100),
                quantity INTEGER,
                price DECIMAL(10, 2)
            )
        """
    })

    # 2. Insert test data using transaction
    print("\n2. Inserting order data with transaction...")
    result = await client.call_tool("execute_transaction", {
        "statements": [
            {
                "query": "INSERT INTO orders (user_id, total_amount) VALUES (1, 150.00) RETURNING order_id"
            },
            {
                "query": "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (1, 'Laptop', 1, 100.00)"
            },
            {
                "query": "INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (1, 'Mouse', 2, 25.00)"
            }
        ]
    })
    print(f"Result: {json.dumps(result, indent=2, default=str)}")

    # 3. Complex JOIN query
    print("\n3. Executing JOIN query...")
    result = await client.call_tool("execute_select", {
        "query": """
            SELECT
                o.order_id,
                o.user_id,
                o.order_date,
                oi.product_name,
                oi.quantity,
                oi.price,
                (oi.quantity * oi.price) as line_total
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            ORDER BY o.order_id, oi.item_id
        """
    })
    print(f"Result: {json.dumps(result, indent=2, default=str)}")

    # 4. Aggregate query
    print("\n4. Executing aggregate query...")
    result = await client.call_tool("execute_select", {
        "query": """
            SELECT
                o.order_id,
                COUNT(oi.item_id) as item_count,
                SUM(oi.quantity * oi.price) as calculated_total
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id
        """
    })
    print(f"Result: {json.dumps(result, indent=2, default=str)}")

    # Cleanup
    print("\n5. Cleaning up test tables...")
    await client.call_tool("execute_drop_table", {"table_name": "order_items", "cascade": True})
    await client.call_tool("execute_drop_table", {"table_name": "orders", "cascade": True})


async def main():
    """Main demo function"""
    client = PostgreSQLMCPClient()

    try:
        # Connect to the MCP server
        await client.connect()

        # List available tools
        print("\n" + "="*60)
        print("AVAILABLE TOOLS")
        print("="*60)
        tools = await client.list_tools()
        for tool in tools:
            print(f"\n{tool.name}:")
            print(f"  {tool.description}")

        # Run demonstrations
        await demo_ddl_operations(client)
        await demo_dml_operations(client)
        await demo_tcl_operations(client)
        await demo_utility_operations(client)
        await demo_complex_queries(client)

        # Cleanup
        await demo_cleanup(client)

        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)

    except Exception as e:
        logger.error(f"Error during demo: {e}", exc_info=True)
    finally:
        # Disconnect
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
