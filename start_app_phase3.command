#!/bin/bash
# Phase 3 Stock Analyzer Startup Script

cd "$(dirname "$0")"

echo "🚀 Starting Stock Analyzer Phase 3 (ML Prediction + Sentiment Analysis)"
echo "📊 Loading configuration..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install required dependencies if needed
if [ ! -f "requirements_phase3.txt.installed" ]; then
    echo "📦 Installing Phase 3 dependencies..."
    pip install -r requirements_phase3.txt
    touch requirements_phase3.txt.installed
fi

# Start the application
python stock_app_phase3.py

echo "✅ Stock Analyzer Phase 3 started successfully!"