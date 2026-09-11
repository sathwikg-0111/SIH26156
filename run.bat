@echo off
echo ========================================================
echo  Universal Log Pre-processing Framework
echo ========================================================
echo.
echo Starting Ingestion Pipeline and Streamlit Dashboard...
cd /d "%~dp0"
python -m streamlit run UI\dashboard.py
pause
