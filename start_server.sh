#!/bin/bash

echo "========================================"
echo " PhysioClinic Backend API Startup"
echo "========================================"
echo ""

echo "[1/3] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi
echo "Python found: $(python3 --version)"
echo ""

echo "[2/3] Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed!"
echo ""

echo "[3/3] Starting FastAPI server..."
echo ""
echo "========================================"
echo " Server will start at:"
echo " http://localhost:8000"
echo ""
echo " Swagger UI: http://localhost:8000/docs"
echo " ReDoc: http://localhost:8000/redoc"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 main.py
