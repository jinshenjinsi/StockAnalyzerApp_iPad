#!/bin/bash
# Unified startup script for Stock Analyzer App

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if required dependencies are installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    exit 1
fi

# Install requirements if needed
if [ ! -f "requirements_installed" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
    touch requirements_installed
fi

# Start the application
echo "Starting Stock Analyzer App (Phase 3)..."
python3 app.py

echo "Application started successfully!"