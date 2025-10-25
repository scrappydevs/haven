#!/bin/bash

echo "🏥 Haven AI - Installing Enhancements"
echo "====================================="
echo ""

# Backend
echo "📦 Installing backend dependencies..."
cd backend
source venv/bin/activate
pip install reportlab>=4.0.0
echo "✅ Backend dependencies installed"
echo ""

# Check if frontend dependencies need updating
echo "📦 Checking frontend dependencies..."
cd ../frontend
if ! grep -q "react-markdown" package.json; then
    echo "Installing react-markdown and remark-gfm..."
    npm install react-markdown remark-gfm
fi

if ! grep -q "zustand" package.json; then
    echo "Installing zustand..."
    npm install zustand
fi

echo "✅ Frontend dependencies ready"
echo ""

echo "🎉 All enhancements installed!"
echo ""
echo "Next steps:"
echo "1. Restart backend: cd backend && python -m uvicorn app.main:app --reload"
echo "2. Refresh frontend: Cmd+Shift+R in browser"
echo "3. Read HAVEN_AI_COMPLETE_FEATURES.md for full feature list"
echo ""
echo "🚀 Ready to test!"

