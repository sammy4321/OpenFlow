import queue
import threading
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Minimum audio duration (in samples) to attempt transcription
# 1.5s at 16kHz = 24,000 samples
MIN_SAMPLES = 24_000


class StreamProcessor:
    """
    Manages audio buffering and threaded transcription processing.
    """

    def __init__(self, engine, accessibility=None, completion_callback=None):
        self.engine = engine
        self.accessibility = accessibility
        self.completion_callback = completion_callback
        self.audio_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.audio_buffer = np.array([], dtype=np.float32)

    def start(self):
        """Starts the background worker thread."""
        self.running = True
        self.reset()
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True # Ensure thread dies with app
        self.worker_thread.start()
        logger.debug("StreamProcessor started.")

    def stop(self):
        """Stops the worker thread."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        logger.debug("StreamProcessor stopped.")

    def reset(self):
        """Clears the current audio buffer."""
        self.audio_buffer = np.array([], dtype=np.float32)

    def process_chunk(self, chunk):
        """Adds a new audio chunk to the queue."""
        if self.running:
            self.audio_queue.put(chunk)

    def finish_recording(self):
        """Signals that recording has stopped; triggers final transcription."""
        if self.running:
            self.audio_queue.put(None)  # Sentinel

    def _worker(self):
        """Background thread to process audio chunks and transcribe."""
        while self.running:
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                
                if chunk is None:
                    self._handle_final_transcription()
                    continue

                self.audio_buffer = np.concatenate((self.audio_buffer, chunk))

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Stream processing error: {e}", exc_info=True)

    def _handle_final_transcription(self):
        """Transcribes the accumulated buffer and inserts text."""
        try:
            if len(self.audio_buffer) < MIN_SAMPLES:
                logger.debug("Audio too short, skipping transcription.")
                self.audio_buffer = np.array([], dtype=np.float32)
                if self.completion_callback:
                    self.completion_callback()
                return

            logger.info(f"Transcribing {len(self.audio_buffer)/16000:.2f}s of audio...")
            text_output = ""
            
            # Stream segments (or single shot for simpler engines)
            for text_segment in self.engine.transcribe_stream(self.audio_buffer):
                text_output += text_segment
            
            self.audio_buffer = np.array([], dtype=np.float32)
            text_output = (text_output or "").strip()
            
            if text_output:
                if self.accessibility:
                    self.accessibility.insert_text(text_output)
                    logger.info(f"Inserted text: {text_output[:50]}...")
                else:
                    logger.info(f"Transcription: {text_output}")
            else:
                logger.info("No text detected.")

        except Exception as e:
             logger.error(f"Transcription failed: {e}", exc_info=True)
        finally:
            if self.completion_callback:
                self.completion_callback()
