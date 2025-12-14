# mcp_postgres_server.py

import os
import uvicorn
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://ai-premmalothu0362ai608205493981.cognitiveservices.azure.com")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME", "claude-sonnet-4-5-2")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")
if not AZURE_API_KEY:
    raise ValueError("AZURE_API_KEY environment variable is not set.")

# Ensure endpoint format is correct for Claude in Azure AI Foundry
AZURE_ENDPOINT = AZURE_ENDPOINT.rstrip('/')
if not AZURE_ENDPOINT.endswith('/anthropic'):
    AZURE_ENDPOINT += '/anthropic'

# --- Database Setup ---
try:
    engine = create_engine(DATABASE_URL)
    # Test connection
    with engine.connect() as connection:
        pass
except SQLAlchemyError as e:
    raise RuntimeError(f"Failed to connect to the database: {e}")


# --- FastAPI Application ---
app = FastAPI(
    title="MCP Natural Language to PostgreSQL Server",
    description="Translates natural language to SQL UPDATE statements and executes them.",
    version="0.1.0",
)


class NaturalLanguageQuery(BaseModel):
    """Request model for natural language queries (both SELECT and UPDATE)."""
    query: str


# --- Core Logic ---

def get_database_schema(db_engine) -> str:
    """
    Inspects the database and returns a string representation of its schema.
    """
    try:
        inspector = inspect(db_engine)
        schema_info = []
        schemas = inspector.get_schema_names()
        for schema in schemas:
            # Skip system schemas
            if schema.startswith('pg_') or schema in ['information_schema']:
                continue
            
            tables = inspector.get_table_names(schema=schema)
            if not tables:
                continue

            schema_info.append(f"Schema: {schema}")
            for table_name in tables:
                schema_info.append(f"  Table: {table_name}")
                columns = inspector.get_columns(table_name, schema=schema)
                for column in columns:
                    schema_info.append(f"    - {column['name']} ({column['type']})")
        
        return "\n".join(schema_info) if schema_info else "No user tables found in the database."

    except SQLAlchemyError as e:
        print(f"Error fetching database schema: {e}")
        raise HTTPException(status_code=500, detail="Could not inspect database schema.")


def generate_sql_from_natural_language(natural_language_query: str, db_schema: str) -> str:
    """
    Uses an LLM to translate a natural language query into a SQL SELECT or UPDATE statement.

    🛑 IMPORTANT: This is the most critical and sensitive part of the application.
    The prompt is engineered to be as safe as possible, but it's not foolproof.
    """
    prompt = f"""
    You are a highly intelligent and secure AI assistant that translates natural language into SQL.
    Your function is to generate a single, precise SQL statement (either SELECT or UPDATE).

    You must adhere to the following strict rules:
    1.  **ONLY generate a `SELECT` or `UPDATE` statement.** Never generate `INSERT`, `DELETE`, `DROP`, `CREATE`, `ALTER`, or any other type of SQL command.
    2.  For queries asking to "show", "list", "display", "get", "find", or "retrieve" data, generate a SELECT statement.
    3.  For queries asking to "update", "change", "modify", or "set" data, generate an UPDATE statement.
    4.  For SELECT queries, use appropriate WHERE clauses if filters are mentioned. If no filter is mentioned, you can omit the WHERE clause.
    5.  Do not generate any text, explanation, or markdown formatting around the SQL. Your entire response must be only the SQL statement itself.
    6.  Analyze the database schema provided below to ensure the table and column names in your query are correct.
    7.  If the user's request asks to DELETE, DROP, CREATE, ALTER, INSERT or any destructive operation, you MUST respond with "Error: Invalid request."
    8.  The final query must not have a semicolon at the end.
    9.  For listing tables in PostgreSQL, use: SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'

    **Database Schema:**
    ```
    {db_schema}
    ```

    **User's Natural Language Request:**
    "{natural_language_query}"

    **Your Task:**
    Generate ONLY the SQL statement (SELECT or UPDATE). Do not include any explanations or markdown.

    **Generated SQL:**
    """
    try:
        # Make API call to Azure-hosted Claude using REST API
        headers = {
            "Content-Type": "application/json",
            "x-api-key": AZURE_API_KEY,
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": DEPLOYMENT_NAME,
            "max_tokens": 1024,
            "temperature": 0.0,  # Use 0 for deterministic SQL generation
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        with httpx.Client(timeout=30.0) as http_client:
            response = http_client.post(
                f"{AZURE_ENDPOINT}/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

        response_data = response.json()
        generated_sql = response_data["content"][0]["text"].strip()

        # Log the response for debugging
        print(f"Claude's response: {generated_sql}")

        # Strip markdown code blocks if present
        if generated_sql.startswith("```"):
            # Remove opening ```sql or ``` and closing ```
            lines = generated_sql.split('\n')
            # Remove first line if it's ```sql or ```
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            generated_sql = '\n'.join(lines).strip()
            print(f"Cleaned SQL (removed markdown): {generated_sql}")

        # Additional safety check
        if "Error: Invalid request." in generated_sql or "error:" in generated_sql.lower()[:50]:
            raise ValueError("The LLM classified the request as invalid or ambiguous.")

        return generated_sql

    except httpx.HTTPStatusError as e:
        print(f"HTTP error during LLM call: {e}")
        print(f"Response body: {e.response.text}")
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL from natural language: HTTP {e.response.status_code}")
    except Exception as e:
        print(f"Error during LLM call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL from natural language: {str(e)}")


# --- API Endpoints ---

@app.get("/", summary="Health Check")
async def root():
    """A simple health check endpoint."""
    return {"status": "ok", "message": "MCP PostgreSQL Server is running."}


@app.post("/mcp/update_table", summary="Execute a natural language update query")
async def update_table(update_query: NaturalLanguageQuery):
    """
    Accepts a natural language query, translates it to a SQL UPDATE statement,
    and executes it on the database.
    """
    print("Fetching database schema...")
    db_schema = get_database_schema(engine)

    print(f"Generating SQL for query: '{update_query.query}'")
    generated_sql = generate_sql_from_natural_language(update_query.query, db_schema)
    print(f"Generated SQL: {generated_sql}")

    # --- CRITICAL SECURITY VALIDATION ---
    sql_upper = generated_sql.lstrip().upper()
    if not sql_upper.startswith("UPDATE"):
        print("Validation failed: Generated SQL is not an UPDATE statement.")
        raise HTTPException(
            status_code=400,
            detail="Generated query was not a valid UPDATE statement. For security, only UPDATE operations are allowed."
        )

    # --- EXECUTE SQL IN A TRANSACTION ---
    try:
        with engine.begin() as connection: # .begin() starts a transaction
            print("Executing SQL statement in a transaction...")
            result = connection.execute(text(generated_sql))
            print(f"Execution complete. {result.rowcount} row(s) affected.")

    except SQLAlchemyError as e:
        print(f"Database execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    return {
        "message": "Update executed successfully.",
        "generated_sql": generated_sql,
        "rows_affected": result.rowcount
    }


@app.post("/mcp/query_table", summary="Execute a natural language select query")
async def query_table(query: NaturalLanguageQuery):
    """
    Accepts a natural language query, translates it to a SQL SELECT statement,
    and executes it on the database, returning the results.
    """
    print("Fetching database schema...")
    db_schema = get_database_schema(engine)

    print(f"Generating SQL for query: '{query.query}'")
    generated_sql = generate_sql_from_natural_language(query.query, db_schema)
    print(f"Generated SQL: {generated_sql}")

    # --- CRITICAL SECURITY VALIDATION ---
    sql_upper = generated_sql.lstrip().upper()
    if not sql_upper.startswith("SELECT"):
        print("Validation failed: Generated SQL is not a SELECT statement.")
        raise HTTPException(
            status_code=400,
            detail="Generated query was not a valid SELECT statement. For security, only SELECT operations are allowed on this endpoint."
        )

    # --- EXECUTE SQL QUERY ---
    try:
        with engine.connect() as connection:
            print("Executing SQL query...")
            result = connection.execute(text(generated_sql))

            # Fetch all results
            rows = result.fetchall()
            columns = result.keys()

            # Convert to list of dictionaries
            data = [dict(zip(columns, row)) for row in rows]

            print(f"Query complete. {len(data)} row(s) returned.")

    except SQLAlchemyError as e:
        print(f"Database execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    return {
        "message": "Query executed successfully.",
        "generated_sql": generated_sql,
        "row_count": len(data),
        "data": data
    }


# --- Main entry point for Uvicorn ---
if __name__ == "__main__":
    print("Starting server...")
    uvicorn.run("mcp_postgres_server:app", host="127.0.0.1", port=8000, reload=True)
