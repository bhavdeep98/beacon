@echo off
echo ========================================
echo Seeding Demo Data for PsyFlo Dashboard
echo ========================================
echo.

echo Step 1: Seeding demo students...
python tools\seed_demo_students.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to seed students
    pause
    exit /b 1
)
echo.

echo Step 2: Seeding realistic conversations...
python tools\seed_demo_conversations.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to seed conversations
    pause
    exit /b 1
)
echo.

echo ========================================
echo ✅ Demo data seeded successfully!
echo ========================================
echo.
echo You can now:
echo 1. Start the backend: cd backend ^&^& python main.py
echo 2. Start the frontend: cd frontend ^&^& npm run dev
echo 3. View the Counselor Dashboard with realistic data
echo.
pause
