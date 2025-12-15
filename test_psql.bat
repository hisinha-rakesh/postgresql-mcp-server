@echo off
echo Testing psql connection...
echo.

set PGPASSWORD=XXXXXXXXXXX@123
set PGSSLMODE=require

echo Connecting to Azure PostgreSQL...
psql -h pgs-youtube-app.postgres.database.azure.com -U "pgadmina@pgs-youtube-app" -d postgres -c "SELECT version();"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! psql connected successfully
) else (
    echo.
    echo FAILED! psql connection failed with error code %ERRORLEVEL%
)

pause
