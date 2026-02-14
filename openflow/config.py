import os
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.parent
MODELS_DIR = ROOT_DIR / "models"
RESOURCES_DIR = ROOT_DIR / "resources"

# Audio Settings
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DURATION_MS = 20
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

# Model Settings
DEFAULT_MODEL = "tiny"
MLX_MODEL_REPO = "mlx-community/whisper-tiny-mlx"

AUDIO_QUEUE_MAXSIZE = 20

# Hotkey settings
# This represents the key used in hotkey.py. 
# While currently relying on specific key codes, this config acts as a central reference.
HOTKEY = "<122>"  # Examples: F1, or specialized Fn usages depending on system config.
