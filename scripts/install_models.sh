#!/bin/bash
set -e

echo "📦 Downloading Whisper models..."

# Use project venv if present so cache is in one place
if [ -d "venv" ]; then
    . venv/bin/activate
fi

# Install download utilities
pip install -q huggingface_hub tqdm 2>/dev/null || true
# Enable faster downloads if possible
pip install -q hf_transfer 2>/dev/null && export HF_HUB_ENABLE_HF_TRANSFER=1 || true

echo ""
echo "  → Downloading mlx-community/whisper-tiny-mlx..."
python3 -c "
from huggingface_hub import snapshot_download
try:
    snapshot_download(repo_id='mlx-community/whisper-tiny-mlx')
    print('  ✓ Done')
except Exception as e:
    print(f'  x Failed: {e}')
"

echo ""
echo "  → Downloading Systran/faster-whisper-tiny..."
python3 -c "
from huggingface_hub import snapshot_download
try:
    snapshot_download(repo_id='Systran/faster-whisper-tiny')
    print('  ✓ Download done')
except Exception as e:
    print(f'  x Failed: {e}')
"

echo "  → Verifying faster-whisper model load..."
python3 -c "
from faster_whisper import WhisperModel
try:
    WhisperModel('tiny', device='cpu', compute_type='int8')
    print('  ✓ Model loaded successfully')
except Exception as e:
    print(f'  x Load failed: {e}')
"

echo "✅ Models ready."
