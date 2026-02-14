#!/bin/bash
set -e

echo "🐍 Checking Python version..."

if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 not found. Attempting install via brew..."
    brew install python@3.11
else
    echo "✅ Python 3.11 found."
fi

# Ensure pip is up to date
python3.11 -m ensurepip --upgrade
python3.11 -m pip install --upgrade pip

echo "✅ Python environment ready."
