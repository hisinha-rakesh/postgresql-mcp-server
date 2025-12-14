@echo off
echo ================================================================================
echo Adding Filesystem MCP Server Globally to Claude Code
echo ================================================================================
echo.

REM Add filesystem MCP server with user scope (global across all projects)
echo Adding filesystem server with full system access...
claude mcp add --scope user --transport stdio filesystem -- npx -y @modelcontextprotocol/server-filesystem C:\Users\kusha

echo.
echo ================================================================================
echo Done! Verifying installation...
echo ================================================================================
echo.

REM List all MCP servers to verify
claude mcp list

echo.
echo ================================================================================
echo Filesystem MCP Server Installation Complete!
echo ================================================================================
echo.
echo The filesystem server is now available globally across all your projects.
echo It provides read/write access to: C:\Users\kusha
echo.
echo To test it, run:
echo   cd C:\Users\kusha\postgresql-mcp
echo   claude
echo   Then type: /mcp
echo.
pause
