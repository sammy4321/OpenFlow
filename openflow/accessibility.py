import subprocess
import time
import logging

logger = logging.getLogger(__name__)

# Constants
KVK_ANSI_V = 9
KCG_EVENT_FLAG_MASK_COMMAND = 0x100000

def _paste_via_shortcut():
    """Simulates Cmd+V to paste content."""
    try:
        from Quartz import (
            CGEventCreateKeyboardEvent,
            CGEventPost,
            CGEventSetFlags,
            kCGHIDEventTap,
        )
        source = None
        down = CGEventCreateKeyboardEvent(source, KVK_ANSI_V, True)
        CGEventSetFlags(down, KCG_EVENT_FLAG_MASK_COMMAND)
        up = CGEventCreateKeyboardEvent(source, KVK_ANSI_V, False)

        CGEventPost(kCGHIDEventTap, down)
        time.sleep(0.05)
        CGEventPost(kCGHIDEventTap, up)
        return True
    except Exception as e:
        logger.debug(f"Failed to simulate paste shortcut: {e}")
        return False


class AccessibilityInserter:
    """Methods to insert text into active applications."""

    def _copy_to_clipboard(self, text):
        try:
            p = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            p.communicate(input=text.encode("utf-8"), timeout=1)
            return p.returncode == 0
        except Exception as e:
            logger.error(f"Clipboard copy failed: {e}")
            return False

    def _fallback_clipboard_only(self, text):
        if self._copy_to_clipboard(text):
            logger.info("Copied to clipboard (direct paste failed or disabled).")

    def insert_text(self, text):
        if not (text or "").strip():
            return
        
        text = text.strip()
        
        # 1. Copy to clipboard
        if not self._copy_to_clipboard(text):
            return
            
        # 2. Simulate paste
        if _paste_via_shortcut():
            return
            
        # 3. Fallback
        self._fallback_clipboard_only(text)
