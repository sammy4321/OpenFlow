import sounddevice as sd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class AudioCapture:
    """
    Handles audio capture from the system's default input device.
    """

    def __init__(self):
        self.stream = None
        self.callback = None

    def start(self, callback):
        """Starts the audio capture stream."""
        self.callback = callback
        
        try:
            # Set default input device to system default
            default_input = sd.query_devices(kind='input')
            sd.default.device = (default_input['name'], None)
            
            self.stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype='float32',
                callback=self._audio_callback
            )
            self.stream.start()
            logger.info(f"Audio capture started using device: {default_input.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}", exc_info=True)

    def _audio_callback(self, indata, frames, time, status):
        """Internal callback for sounddevice."""
        if status:
            logger.warning(f"Audio status check: {status}")
        
        if self.callback:
            # Flatten to 1D array as expected by downstream consumers
            self.callback(indata.flatten().copy())

    def stop(self):
        """Stops and closes the audio stream."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            logger.info("Audio capture stopped.")
