@echo off
echo ================================================================================
echo Testing MANUAL pg_dump (will prompt for password)
echo ================================================================================
echo.
echo This will prompt you for the password interactively.
echo Please type: Centurylink@123
echo.
echo Press any key to continue...
pause > nul
echo.

REM Clear any password environment variables
set PGPASSWORD=

pg_dump -h pgs-youtube-app.postgres.database.azure.com -U pgadmina@pgs-youtube-app -d library -F c -f manual_test_backup.dump --verbose

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS! Manual entry worked
    echo ================================================================================
    echo.
    echo Now testing with PGPASSWORD environment variable...
    echo.

    set PGPASSWORD=Centurylink@123
    set PGSSLMODE=require

    pg_dump -h pgs-youtube-app.postgres.database.azure.com -U pgadmina@pgs-youtube-app -d library -F c -f auto_test_backup.dump --verbose

    if %ERRORLEVEL% EQU 0 (
        echo.
        echo SUCCESS! PGPASSWORD environment variable also worked!
        echo This means the MCP server should work now.
    ) else (
        echo.
        echo FAILED! PGPASSWORD environment variable did not work
        echo This means there's something special about Azure PostgreSQL
    )
) else (
    echo.
    echo FAILED! Even manual entry failed
    echo Please check if the credentials are correct
)

echo.
pause
