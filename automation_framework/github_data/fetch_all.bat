@echo off
REM Fetch all GitHub data for touchHLE automation
REM Run from the github_data directory

echo ============================================================
echo touchHLE GitHub Data Fetcher
echo ============================================================
echo.

REM Check for GitHub token
if defined GITHUB_TOKEN (
    echo Using GitHub token for authenticated requests
) else (
    echo WARNING: No GITHUB_TOKEN set. Limited to 60 requests/hour.
    echo Set GITHUB_TOKEN environment variable for 5000 requests/hour.
    echo.
)

REM Fetch upstream data
echo Fetching upstream repository data...
python fetch_github_data.py --upstream

echo.
echo Fetching fork data...
python fetch_github_data.py --forks

echo.
echo Running relevant searches...
python fetch_github_data.py --search "black screen"
python fetch_github_data.py --search "rendering"
python fetch_github_data.py --search "glMaterial"
python fetch_github_data.py --search "viewport"
python fetch_github_data.py --search "texture"
python fetch_github_data.py --search "OpenGL ES"

echo.
echo ============================================================
echo Fetch complete! Check summary.json for results.
echo ============================================================
pause
