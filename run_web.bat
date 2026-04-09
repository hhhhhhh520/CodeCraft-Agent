@echo off
chcp 65001 >nul
echo Starting CodeCraft Agent Web UI...
streamlit run frontend/app.py --server.port 8501
