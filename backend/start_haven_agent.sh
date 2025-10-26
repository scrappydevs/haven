#!/bin/bash

# Start the Haven voice agent with Infisical secrets
# Usage: ./start_haven_agent.sh [dev|console]

MODE=${1:-dev}

echo "🚀 Starting Haven Voice Agent..."
echo "   Mode: $MODE"
echo "   Conda Environment: haven"
echo ""

# Activate conda environment - find conda dynamically
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/opt/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif command -v conda &> /dev/null; then
    # Try using conda init
    eval "$(conda shell.bash hook)"
else
    echo "❌ Could not find conda. Please ensure conda is installed."
    exit 1
fi

conda activate haven

# Check if Infisical CLI is available
if command -v infisical &> /dev/null; then
    echo "✅ Infisical CLI detected - loading secrets from Infisical"
    infisical run -- python app/agents/haven_agent.py $MODE
else
    echo "⚠️  Infisical CLI not found - using .env.local"
    echo "   Install Infisical CLI: https://infisical.com/docs/cli/overview"
    python app/agents/haven_agent.py $MODE
fi
