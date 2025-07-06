@echo off
echo ========================================
echo ALGOBOT SETUP FOR WINDOWS
echo ========================================
echo.

echo 1. Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo.
echo 2. Running setup script...
python scripts/setup.py
if %errorlevel% neq 0 (
    echo ERROR: Setup script failed
    pause
    exit /b 1
)

echo.
echo 3. Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo 4. Validating setup...
python validate_setup.py
if %errorlevel% neq 0 (
    echo ERROR: Setup validation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your Delta Exchange API credentials
echo 2. Test connection: python scripts/test_connection.py
echo 3. Start bot: python src/main.py
echo.
pause
