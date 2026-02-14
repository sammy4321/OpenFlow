import ctypes
import numpy as np
import os
import logging
from .config import ROOT_DIR

logger = logging.getLogger(__name__)

class RNNoise:
    """
    Python wrapper for the RNNoise C library.
    Handles loading the shared library and processing audio frames for noise suppression.
    """

    def __init__(self):
        lib_path = os.path.join(ROOT_DIR, "librnnoise.dylib")
        if not os.path.exists(lib_path):
            logger.error(f"RNNoise library not found at: {lib_path}")
            raise FileNotFoundError(f"RNNoise library not found at {lib_path}. Run install_rnnoise.sh first.")

        try:
            self.lib = ctypes.cdll.LoadLibrary(lib_path)
            
            # rnnoise_create() -> DenoiseState*
            self.lib.rnnoise_create.restype = ctypes.c_void_p
            self.state = self.lib.rnnoise_create(None)

            # rnnoise_process_frame(DenoiseState *st, float *out, const float *in)
            # We must define argtypes to ensure correct pointer passing
            self.lib.rnnoise_process_frame.argtypes = [
                ctypes.c_void_p, 
                ctypes.POINTER(ctypes.c_float), 
                ctypes.POINTER(ctypes.c_float)
            ]
            self.lib.rnnoise_process_frame.restype = ctypes.c_float
            
            logger.info("RNNoise library loaded successfully.")

        except Exception as e:
            logger.error(f"Failed to load RNNoise library: {e}")
            raise

    def process(self, frame):
        """
        Processes a single audio frame (480 samples typical for RNNoise, but here we likely pass chunks).
        Note: RNNoise typically expects specific frame sizes (e.g. 480 samples at 48kHz), 
        but implementation details depend on the compiled library.
        """
        try:
            # Ensure input is float32
            frame_float = frame.astype(np.float32)
            out_float = np.zeros_like(frame_float)
            
            # Create ctypes pointers for the underlying C function
            in_ptr = frame_float.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            out_ptr = out_float.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            
            self.lib.rnnoise_process_frame(self.state, out_ptr, in_ptr)
            
            return out_float
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return frame # Fallback to original audio on error
