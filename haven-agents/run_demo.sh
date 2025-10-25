#!/bin/bash
# Haven AI Multi-Agent System - Demo Runner
# Automatically sets up and runs the complete demo

echo "================================================================================"
echo "🏥 Haven AI Multi-Agent System - Demo Runner"
echo "================================================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if ! python -c "import uagents" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
    echo "   Get your key from: https://console.anthropic.com/"
    echo ""
    read -p "Press Enter once you've added your API key to .env..."
fi

# Verify API key is set
if grep -q "your_api_key_here" .env; then
    echo "❌ ERROR: Please edit .env and add your ANTHROPIC_API_KEY"
    echo "   Current .env still contains placeholder"
    exit 1
fi

echo ""
echo "================================================================================"
echo "🚀 Starting Haven AI Demo"
echo "================================================================================"
echo ""

# Run main orchestrator
python main.py

echo ""
echo "================================================================================"
echo "✅ Demo complete!"
echo "================================================================================"

