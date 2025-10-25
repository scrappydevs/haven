#!/bin/bash
# Setup script for Haven AI agents

echo "=============================================================================="
echo "🚀 HAVEN AI - ENVIRONMENT SETUP"
echo "=============================================================================="
echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo "✅ .env file found"
else
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
fi

echo ""
echo "=============================================================================="
echo "🔑 API KEY CONFIGURATION"
echo "=============================================================================="
echo ""
echo "You need an Anthropic API key for Claude AI reasoning."
echo ""
echo "Get your key from: https://console.anthropic.com/settings/keys"
echo ""
read -p "Do you have an Anthropic API key? (y/n): " has_key

if [ "$has_key" = "y" ] || [ "$has_key" = "Y" ]; then
    read -p "Enter your Anthropic API key: " api_key
    
    # Update .env file
    if grep -q "ANTHROPIC_API_KEY=" .env; then
        # Replace existing
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$api_key|g" .env
        else
            # Linux
            sed -i "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$api_key|g" .env
        fi
    else
        # Add new
        echo "ANTHROPIC_API_KEY=$api_key" >> .env
    fi
    
    echo "✅ API key saved to .env"
else
    echo "⚠️  Skipping API key setup"
    echo "   Agents will use fallback rule-based logic"
    echo "   Add ANTHROPIC_API_KEY to .env later to enable Claude AI"
fi

echo ""
echo "=============================================================================="
echo "📦 INSTALLING DEPENDENCIES"
echo "=============================================================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing packages..."
pip install -r requirements.txt --quiet

echo "✅ Dependencies installed"

echo ""
echo "=============================================================================="
echo "🧪 RUNNING SETUP VERIFICATION"
echo "=============================================================================="
echo ""

python test_setup.py

echo ""
echo "=============================================================================="
echo "✅ SETUP COMPLETE!"
echo "=============================================================================="
echo ""
echo "🚀 Quick Start Commands:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run full demo (all 5 agents):"
echo "   python main.py"
echo ""
echo "3. Run single agent for testing:"
echo "   python agents/patient_guardian.py"
echo ""
echo "4. View deployment info:"
echo "   python deploy.py"
echo ""
echo "=============================================================================="
echo ""

