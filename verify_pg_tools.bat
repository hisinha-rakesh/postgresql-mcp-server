@echo off
echo ========================================
echo PostgreSQL Client Tools Verification
echo ========================================
echo.

echo Checking for pg_dump...
where pg_dump
if %errorlevel% equ 0 (
    pg_dump --version
    echo [OK] pg_dump is installed
) else (
    echo [ERROR] pg_dump not found in PATH
)
echo.

echo Checking for pg_restore...
where pg_restore
if %errorlevel% equ 0 (
    pg_restore --version
    echo [OK] pg_restore is installed
) else (
    echo [ERROR] pg_restore not found in PATH
)
echo.

echo Checking for psql...
where psql
if %errorlevel% equ 0 (
    psql --version
    echo [OK] psql is installed
) else (
    echo [ERROR] psql not found in PATH
)
echo.

echo ========================================
echo Verification Complete
echo ========================================
echo.
echo If any tools show [ERROR], please:
echo 1. Install PostgreSQL client tools
echo 2. Make sure C:\Users\kusha\Downloads\postgresql-18.1-1-windows-x64-binaries\pgsql\bin is in your PATH
echo 3. Restart your Command Prompt after installation
echo.

pause
