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

# Hotkey settings
HOTKEY = "cmd_r"  # Right Command key
