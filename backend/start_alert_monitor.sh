#!/bin/bash

# Start Alert Monitor for automatic nurse calling

cd "$(dirname "$0")"

echo "🚀 Starting Haven Alert Monitor..."
echo "   This will monitor for critical alerts and call nurses automatically"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No virtual environment found - using system Python"
fi

# Check if Vonage is installed
python3 -c "import vonage" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Vonage library not found - installing..."
    pip install vonage
fi

# Run the alert monitor
echo ""
echo "📞 Alert Monitor running..."
echo "   Nurse: +1-385-401-9951"
echo "   Press Ctrl+C to stop"
echo ""

python3 -m app.alert_monitor

