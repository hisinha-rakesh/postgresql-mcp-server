# Database Targeting in PostgreSQL MCP Server

## Overview

The MCP server now supports targeting specific databases for all operations. You can specify which database to work with, or it will use the default database from `DATABASE_URL`.

## How It Works

### Default Behavior
Your `.env` file has:
```env
DATABASE_URL=postgresql://...@hostname:5432/postgres?sslmode=require
```

This connects to the `postgres` database by default.

### Current Status

**✅ What Actually Happens:**
- The server connects to **ONE** database at a time (specified in DATABASE_URL)
- It does **NOT** create tables in all databases
- It only operates on the connected database

**❌ Your Concern:**
- You suspected it creates tables in ALL databases - **This is NOT true**
- It only creates in the ONE database you're connected to

## New Feature: Database-Specific Operations

### What Was Added

Now you can specify `database_name` parameter for operations like:
- `execute_create_table` - Create tables in specific databases
- `execute_select` - Query specific databases
- (More operations can be added similarly)

### Usage in Claude Desktop

#### Before (connects to 'postgres' database):
```
"Create a users table with id, name, and email columns"
```
Result: Creates table in `postgres` database (from DATABASE_URL)

#### After (can specify target database):
```
"Create a users table in the library database with id, name, and email columns"
```
Result: Creates table in `library` database

```
"Show me all books from the library database"
```
Result: Queries the `library` database

```
"Create a videos table in the youtube_db database"
```
Result: Creates table in `youtube_db` database

## Technical Details

### Helper Function
Added `get_database_connection()` helper that:
1. Takes an optional `database_name` parameter
2. If provided, creates a temporary connection to that database
3. If not provided, uses the default connection pool (postgres)

### Modified Operations
- `execute_create_table` - Now accepts `database_name` parameter
- `execute_select` - Now accepts `database_name` parameter
- More operations can be updated similarly

### Connection Management
- Default database: Uses connection pool (efficient, persistent)
- Specific database: Creates temporary connection (on-demand)
- Connections are properly closed after use

## Examples

### Example 1: Create Table in Specific Database
**Command:**
```
"Create a books table in the library database"
```

**What happens:**
1. Claude calls `execute_create_table` with:
   - `query`: CREATE TABLE statement
   - `database_name`: "library"
2. Server connects to `library` database
3. Creates the table
4. Closes connection

### Example 2: Query Specific Database
**Command:**
```
"Show me all records from users table in the youtube_db database"
```

**What happens:**
1. Claude calls `execute_select` with:
   - `query`: SELECT * FROM users
   - `database_name`: "youtube_db"
2. Server connects to `youtube_db` database
3. Executes query
4. Returns results

### Example 3: Default Database
**Command:**
```
"Create a logs table"
```

**What happens:**
1. Claude calls `execute_create_table` with:
   - `query`: CREATE TABLE statement
   - `database_name`: (not specified)
2. Server uses default connection (postgres database)
3. Creates table in postgres database

## Important Notes

### ✅ Clarification
**The server does NOT create tables in all databases!**
- It only creates in the ONE database you specify (or default)
- Each operation targets a single database

### 🎯 Best Practice
When working with multiple databases:
1. **Be explicit** - Always mention the database name: "in library database", "in youtube_db", etc.
2. **Default for admin tasks** - Use default (postgres) for admin operations
3. **Specific for app data** - Use specific databases (library, youtube_db) for application tables

### 📋 Database List
To see all your databases:
```
"List all databases"
```

## Configuration

### Current Setup (.env)
```env
DATABASE_URL=postgresql://username:password@hostname:5432/postgres?sslmode=require
```
- Default database: `postgres`
- Can connect to: Any database on the server (library, youtube_db, etc.)

### No Changes Needed
The `.env` configuration doesn't need to change. The `database_name` parameter lets you target any database dynamically.

## Summary

**Before this update:**
- ❌ All operations went to `postgres` database only
- ❌ No way to target specific databases
- ❌ Suspected (incorrectly) that it creates in all databases

**After this update:**
- ✅ Can specify target database for each operation
- ✅ Still uses default (postgres) when not specified
- ✅ Confirmed: Only operates on ONE database at a time
- ✅ More flexible and powerful!
