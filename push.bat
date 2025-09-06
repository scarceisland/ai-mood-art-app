@echo off
echo ===============================
echo   Pushing to ALL repositories
echo ===============================
echo.

echo 1. Pushing to GitHub...
git push github main
if %errorlevel% neq 0 (
    echo ERROR: Failed to push to GitHub
    pause
    exit /b %errorlevel%
)
echo ✓ GitHub push successful!
echo.

echo 2. Pushing to GitLab...
git push origin main
if %errorlevel% neq 0 (
    echo ERROR: Failed to push to GitLab
    pause
    exit /b %errorlevel%
)
echo ✓ GitLab push successful!
echo.

echo ===============================
echo   SUCCESS: Pushed to both repositories!
echo ===============================
pause