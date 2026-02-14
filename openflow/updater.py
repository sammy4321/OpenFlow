import requests
import subprocess
import rumps
import logging

logger = logging.getLogger(__name__)

class Updater:
    """
    Checks for updates via GitHub Releases and triggers brew upgrade.
    """

    def check(self):
        try:
            repo_url = "https://api.github.com/repos/sammy4321/OpenFlow/releases/latest"
            r = requests.get(repo_url, timeout=5)
            
            if r.status_code == 200:
                latest = r.json().get("tag_name")
                return latest
            else:
                logger.debug(f"Update check returned status: {r.status_code}")
                
        except Exception as e:
            logger.error(f"Update check failed: {e}")
        return None

    def update(self):
        try:
            logger.info("Starting update process via brew...")
            # Assumes brew is installed and openflow was installed via brew
            subprocess.run(["brew", "upgrade", "openflow"], check=True)
            rumps.alert("Updated!", "OpenFlow has been updated. Please restart.")
            rumps.quit_application()
        except Exception as e:
            logger.error(f"Update failed: {e}")
            rumps.alert("Update Failed", str(e))
