#!/bin/bash
set -e

echo "📦 Setting up RNNoise..."

if [ -f "librnnoise.dylib" ]; then
    echo "✅ RNNoise library already exists."
    exit 0
fi

# Clone RNNoise if not present
if [ ! -d "rnnoise_src" ]; then
    echo "  → Cloning xiph/rnnoise..."
    git clone https://github.com/xiph/rnnoise.git rnnoise_src > /dev/null 2>&1
fi

# Patch download_model.sh for macOS (curl instead of wget) if needed
if [[ "$OSTYPE" == "darwin"* ]] && [ -f "rnnoise_src/download_model.sh" ]; then
    sed -i '' 's/wget/curl -O/g' rnnoise_src/download_model.sh
fi

echo "  → Compiling..."
cd rnnoise_src
./autogen.sh > /dev/null
./configure > /dev/null
make > /dev/null

# Copy library to root
if [ -f ".libs/librnnoise.0.dylib" ]; then
    cp .libs/librnnoise.0.dylib ../librnnoise.dylib
    echo "✅ RNNoise compiled and installed."
else
    echo "❌ Compilation failed: Library not found."
    exit 1
fi
