#!/bin/bash
# Quick start script for Haven AI agents

clear
echo "=============================================================================="
echo "🏥 HAVEN AI - MULTI-AGENT SYSTEM"
echo "=============================================================================="
echo ""
echo "Built with Fetch.ai uAgents + Anthropic Claude"
echo ""
echo "=============================================================================="
echo ""

# Check if we're in the right directory
if [ ! -d "haven-agents" ]; then
    echo "❌ Error: haven-agents directory not found"
    echo "   Please run this script from the haven/ directory"
    exit 1
fi

cd haven-agents

echo "🔍 Checking setup..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Running setup..."
    ./setup_env.sh
    echo ""
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Agents will run with fallback logic (no Claude AI)"
    echo ""
    echo "   To enable Claude AI:"
    echo "   1. Copy .env.example to .env"
    echo "   2. Add your ANTHROPIC_API_KEY"
    echo ""
    read -p "Continue anyway? (y/n): " continue
    if [ "$continue" != "y" ] && [ "$continue" != "Y" ]; then
        exit 1
    fi
fi

echo "=============================================================================="
echo "🚀 STARTING HAVEN AI AGENTS"
echo "=============================================================================="
echo ""
echo "Select mode:"
echo ""
echo "1. Run ALL 5 agents (full demo)"
echo "2. Run single Patient Guardian (testing)"
echo "3. View deployment info (Agentverse)"
echo "4. Verify setup only"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "=============================================================================="
        echo "🎬 STARTING FULL DEMO - ALL 5 AGENTS"
        echo "=============================================================================="
        echo ""
        echo "Agents starting:"
        echo "  • Patient Guardian (P-001, P-002, P-003)"
        echo "  • Nurse Coordinator"
        echo "  • Emergency Response"
        echo "  • Protocol Compliance"
        echo "  • Research Insights"
        echo ""
        echo "Demo will auto-progress through scenarios:"
        echo "  Minute 0-1: Normal operations"
        echo "  Minute 1-2: Concerning alert (P-002)"
        echo "  Minute 2-3: Critical emergency (P-003)"
        echo "  Minute 3-4: Pattern detection"
        echo "  Minute 4+:  Continue monitoring"
        echo ""
        echo "Press Ctrl+C to stop all agents"
        echo ""
        echo "=============================================================================="
        echo ""
        sleep 2
        source venv/bin/activate
        python main.py
        ;;
    2)
        echo ""
        echo "=============================================================================="
        echo "🧪 STARTING SINGLE PATIENT GUARDIAN (TESTING)"
        echo "=============================================================================="
        echo ""
        echo "This will monitor Patient P-001 only."
        echo "Good for testing and seeing Claude reasoning."
        echo ""
        echo "Press Ctrl+C to stop"
        echo ""
        echo "=============================================================================="
        echo ""
        sleep 2
        source venv/bin/activate
        python agents/patient_guardian.py
        ;;
    3)
        echo ""
        source venv/bin/activate
        python deploy.py
        ;;
    4)
        echo ""
        source venv/bin/activate
        python test_setup.py
        ;;
    *)
        echo ""
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

