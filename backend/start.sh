#!/bin/bash
# Quick start script for Hospital BlockOps Backend

echo "🏥 Hospital BlockOps - Starting Backend with Blockchain"
echo "========================================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env and add your ANTHROPIC_API_KEY"
fi

echo ""
echo "🚀 Starting Flask server with blockchain..."
echo ""

python3 app.py
