#!/bin/bash
set -e

echo "🚀 Installing OpenFlow dependencies..."

# 0. Install wget if missing
if ! command -v wget &> /dev/null; then
    echo "📦 Installing wget..."
    brew install wget
fi

# 1. Bootstrap Python
bash scripts/bootstrap_python.sh

# 2. Install Build Tools (for RNNoise)
if ! command -v autoconf &> /dev/null; then
    echo "🛠 Installing build tools..."
    brew install autoconf automake libtool
fi

# 3. Create Virtual Environment
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo "✅ Created virtual environment."
fi

source venv/bin/activate

# 4. Install Dependencies
pip install -r requirements.txt

# 5. Compile RNNoise
bash scripts/install_rnnoise.sh

# 6. Download Models
bash scripts/install_models.sh

# 7. Install OpenFlow package in editable mode
pip install -e .

echo "🎉 OpenFlow installed successfully!"
echo "Run with: make run"
