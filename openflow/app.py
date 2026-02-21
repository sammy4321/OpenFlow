import rumps
import numpy as np
import logging
from PyObjCTools import AppHelper

from openflow.statusbar import StatusBar
from openflow.overlay import Overlay
from openflow.hotkey import HotkeyListener
from openflow.whisper_engine import WhisperEngine
from openflow.streamer import StreamProcessor
from openflow.audio import AudioCapture
from openflow.accessibility import AccessibilityInserter

logger = logging.getLogger(__name__)

class OpenFlowApp:
    """
    Main application controller for OpenFlow.
    Manages UI, audio capture, transcription engine, and user interactions.
    """

    def __init__(self, model="tiny"):
        logger.info("Initializing OpenFlow UI and components...")

        self._active = False

        # UI Components
        self.statusbar = StatusBar(self)
        self.overlay = Overlay()
        
        # Core Logic
        logger.info("Initializing audio capture...")
        self.audio = AudioCapture()
        
        logger.info(f"Loading Whisper model '{model}'...")
        self.engine = WhisperEngine(model)
        
        logger.info("Setting up accessibility services...")
        self.accessibility = AccessibilityInserter()
        
        # Connect components
        self.streamer = StreamProcessor(self.engine, self.accessibility, self._on_transcription_complete)
        self.streamer.start()

        # Hotkey
        logger.info("Registering global hotkey...")
        self.hotkey = HotkeyListener(self.start_listening, self.stop_listening)

    def _audio_callback(self, chunk):
        """
        Callback for audio chunks.
        Processes audio for transcription and computes RMS for visual feedback.
        """
        self.streamer.process_chunk(chunk)
        
        # Compute RMS amplitude for visualization
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        # Normalize level (0.0 - 1.0) for the overlay
        level = min(1.0, rms / 0.08)
        
        AppHelper.callAfter(self._push_audio_level, level)

    def _push_audio_level(self, level):
        self.overlay.update_audio_level(level)

    def start_listening(self):
        """Starts audio capture and updates UI."""
        if self._active:
            return
        self._active = True
        logger.debug("Start listening triggered.")
        self.streamer.reset()
        AppHelper.callAfter(self._update_ui_start, None)
        self.audio.start(self._audio_callback)

    def stop_listening(self):
        """Stops audio capture and finalizes processing."""
        if not self._active:
            return
        logger.debug("Stop listening triggered.")
        self.audio.stop()
        self.streamer.finish_recording()
        AppHelper.callAfter(self._update_ui_stop, None)

    def _update_ui_start(self, _):
        self.overlay.show_listening()

    def _update_ui_stop(self, _):
        self.overlay.show_transcribing()

    def _on_transcription_complete(self):
        """Callback when text insertion is complete."""
        self._active = False
        AppHelper.callAfter(self._update_ui_complete, None)

    def _update_ui_complete(self, _):
        self.overlay.show_done()

    def run(self):
        """Starts the main event loop."""
        logger.info("OpenFlow is ready. Press Right Command to dictate.")
        rumps.notification("OpenFlow", "Ready", "Press Right Command to dictate")
        self.statusbar.run()
