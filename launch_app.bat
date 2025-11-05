@echo off
REM Launch the Geotechnical A-line Streamlit App
REM This script starts the Streamlit server on localhost:8501

echo.
echo ========================================
echo  Geotechnical A-line Plotting App
echo ========================================
echo.
echo Starting Streamlit server...
echo The app will open in your browser at http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
streamlit run app.py

pause
