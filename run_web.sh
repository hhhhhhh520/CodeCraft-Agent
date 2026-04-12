#!/bin/bash
cd "$(dirname "$0")"
echo "Starting CodeCraft Agent Web UI..."
python -m streamlit run frontend/app.py --server.port 8501
