from openflow.app import OpenFlowApp
import argparse
import sys
import os
import time
import logging
from AppKit import NSProcessInfo, NSApplication, NSImage
from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_accessibility():
    """Checks if the process has accessibility permissions, prompting if necessary."""
    options = {kAXTrustedCheckOptionPrompt: True}
    trusted = AXIsProcessTrustedWithOptions(options)
    
    if not trusted:
        logger.warning("Accessibility permissions denied. Prompting user.")
        print("\n" + "-" * 60)
        print("OpenFlow requires Accessibility permissions to function.")
        print("Please grant permission in the System Settings popup.")
        print("-" * 60)
        
        while not trusted:
            try:
                time.sleep(2)
                # Re-check status without prompting repeatedly
                trusted = AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: False})
                if trusted:
                    logger.info("Accessibility permissions granted.")
                    break
            except KeyboardInterrupt:
                sys.exit(1)
    else:
        logger.info("Accessibility permissions verified.")

def set_process_name():
    """Sets the process name to 'OpenFlow'."""
    proc_info = NSProcessInfo.processInfo()
    proc_info.setProcessName_("OpenFlow")

def set_dock_icon():
    """Sets the application icon in the Dock."""
    icon_path = os.path.abspath("resources/icon.png")
    if os.path.exists(icon_path):
        image = NSImage.alloc().initByReferencingFile_(icon_path)
        NSApplication.sharedApplication().setApplicationIconImage_(image)
    else:
        logger.warning(f"Icon not found at {icon_path}")

VALID_MODELS = ("tiny", "base", "small", "medium", "large")

def main():
    parser = argparse.ArgumentParser(description="OpenFlow — Open Source Speech-to-Text")
    parser.add_argument(
        "--model",
        type=str,
        default="tiny",
        choices=VALID_MODELS,
        help="Whisper model size (default: tiny). Model is downloaded automatically if not present.",
    )
    args = parser.parse_args()

    logger.info(f"Starting OpenFlow (model={args.model})...")
    set_process_name()
    set_dock_icon()
    check_accessibility()

    try:
        app = OpenFlowApp(model=args.model)
        app.run()
    except KeyboardInterrupt:
        logger.info("OpenFlow stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
