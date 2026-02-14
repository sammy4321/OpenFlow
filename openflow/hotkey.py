from pynput import keyboard
import logging

logger = logging.getLogger(__name__)

class HotkeyListener:
    """
    Listens for global hotkey events to trigger dictation.
    Currently configured to use the Right Command key (cmd_r).
    """

    def __init__(self, on_press, on_release):
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        self.is_holding = False # Prevent repeat triggers
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        logger.info("Hotkey listener started (Target: Right Command).")

    def _on_press(self, key):
        if key == keyboard.Key.cmd_r:
            if not self.is_holding:
                logger.debug("Hotkey pressed (Right Command)")
                self.is_holding = True
                self.on_press_callback()

    def _on_release(self, key):
        if key == keyboard.Key.cmd_r:
            if self.is_holding:
                logger.debug("Hotkey released (Right Command)")
                self.is_holding = False
                self.on_release_callback()
