#!/bin/bash

# Enterprise Frontend Setup Script
# Run this to set up and start your new React UI

set -e  # Exit on error

echo ""
echo "================================================================================"
echo "🚀 GOLDEN CONFIG AI - Enterprise Frontend Setup"
echo "================================================================================"
echo ""

# Check if in correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Run this script from strands-multi-agent-system directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "   Install from: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js $(node --version) detected"
echo ""

# Navigate to frontend
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies (this may take 2-3 minutes)..."
    npm install
    echo "✅ Dependencies installed"
    echo ""
else
    echo "✅ Dependencies already installed"
    echo ""
fi

# Build frontend
echo "🔨 Building React frontend..."
npm run build
echo "✅ Frontend built successfully"
echo ""

# Go back to root
cd ..

echo "================================================================================"
echo "✅ Setup Complete!"
echo "================================================================================"
echo ""
echo "🌐 Starting server..."
echo "   Access your app at: http://localhost:3000"
echo ""
echo "   Press Ctrl+C to stop"
echo "================================================================================"
echo ""

# Start server
python3 main.py


