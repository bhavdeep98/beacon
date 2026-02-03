@echo off
echo ========================================
echo Fixing Counselor Dashboard Data Issues
echo ========================================
echo.

echo Step 1: Clearing old conversation data...
python clear_and_reseed.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to clear data
    pause
    exit /b 1
)
echo.

echo Step 2: Reseeding with correct session hashes...
python tools\seed_demo_conversations.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to seed conversations
    pause
    exit /b 1
)
echo.

echo Step 3: Verifying data...
python test_dashboard_data.py
if %errorlevel% neq 0 (
    echo ERROR: Data verification failed
    pause
    exit /b 1
)
echo.

echo ========================================
echo ✅ Dashboard data fixed successfully!
echo ========================================
echo.
echo IMPORTANT: You must restart the backend server!
echo.
echo 1. Stop the backend (Ctrl+C in the backend terminal)
echo 2. Restart: cd backend ^&^& python main.py
echo 3. Refresh the frontend dashboard
echo.
pause
