import platform
import logging
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Determine compute backend (MLX on Apple Silicon vs Faster-Whisper on CPU)
# On macOS, MLX can trigger FFT crashes in specific mel/STFT paths. 
# We default to faster-whisper (CPU) on Darwin to ensure stability unless configured otherwise.
_force_faster_whisper = platform.system() == "Darwin"

try:
    import mlx_whisper
    USE_MLX = True and not _force_faster_whisper
    if _force_faster_whisper:
        logger.info("macOS detected: Defaulting to faster-whisper (CPU) for stability.")
    else:
        logger.info("Using MLX Whisper (GPU accelerated).")
except ImportError:
    USE_MLX = False
    logger.warning("MLX Whisper not found. Falling back to faster-whisper (CPU mode).")

if not USE_MLX:
    from faster_whisper import WhisperModel

class WhisperEngine:
    """
    Handles speech-to-text transcription using either MLX (Apple Silicon) or faster-whisper (CPU).
    """
    
    MLX_MODELS = {
        "tiny": "mlx-community/whisper-tiny-mlx",
        "base": "mlx-community/whisper-base-mlx",
        "small": "mlx-community/whisper-small-mlx",
        "medium": "mlx-community/whisper-medium-mlx",
        "large": "mlx-community/whisper-large-v3-mlx"
    }

    def __init__(self, model="tiny"):
        self.use_mlx = USE_MLX
        
        if self.use_mlx:
            self.model_name = self.MLX_MODELS.get(model, model)
            logger.info(f"Configured MLX Model: {self.model_name}")
            self.model = None
            self._warmup_mlx()
        else:
            self.model_name = model
            # Load model at startup to prevent latency during first transcription
            self.model = WhisperModel(model, device="cpu", compute_type="int8")
            logger.info(f"Loaded faster-whisper model: {model}")

    def _warmup_mlx(self):
        """Triggers a dummy transcription to ensure the model is downloaded and cached."""
        try:
            # Minimal 1s of silence at 16kHz
            silent = np.zeros(16000, dtype=np.float32)
            mlx_whisper.transcribe(
                silent,
                path_or_hf_repo=self.model_name,
                language="en",
            )
        except Exception as e:
            logger.warning(f"MLX warmup failed (non-fatal): {e}")

    def transcribe_stream(self, audio_chunk):
        """
        Generates transcription for the given audio chunk.
        Yields text segments as they are decoded.
        """
        if self.use_mlx:
            try:
                # Ensure audio is float32 and 1D for MLX
                if isinstance(audio_chunk, np.ndarray):
                    if audio_chunk.ndim > 1:
                        audio_chunk = audio_chunk.flatten()
                    if audio_chunk.dtype != np.float32:
                        audio_chunk = audio_chunk.astype(np.float32)
                        
                result = mlx_whisper.transcribe(
                    audio_chunk, 
                    path_or_hf_repo=self.model_name, 
                    language="en",
                )
                yield result['text']
            
            except ValueError as e:
                # Handle potential MLX array indexing errors
                if "Cannot index mlx array" in str(e):
                    logger.warning(f"MLX Index Error (skipping chunk): {e}")
                else:
                    raise e
            except Exception as e:
                logger.error(f"Whisper Transcribe Error: {e}", exc_info=True)
        else:
            # Faster-whisper logic
            segments, _ = self.model.transcribe(audio_chunk, beam_size=5)
            for segment in segments:
                yield segment.text
