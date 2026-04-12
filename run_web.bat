@echo off
cd %~dp0
echo Starting CodeCraft Agent Web UI...
python -m streamlit run frontend/app.py --server.port 8501
pause
