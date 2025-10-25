#!/bin/bash

# Start the intake agent with Infisical secrets
# Usage: ./start_intake_agent.sh [dev|console]

MODE=${1:-dev}

echo "🚀 Starting Haven Intake Agent..."
echo "   Mode: $MODE"
echo "   Conda Environment: aegis"
echo ""

# Activate conda environment
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate aegis

# Check if Infisical CLI is available
if command -v infisical &> /dev/null; then
    echo "✅ Infisical CLI detected - loading secrets from Infisical"
    infisical run -- python app/agents/intake_agent.py $MODE
else
    echo "⚠️  Infisical CLI not found - using .env.local"
    echo "   Install Infisical CLI: https://infisical.com/docs/cli/overview"
    python app/agents/intake_agent.py $MODE
fi
