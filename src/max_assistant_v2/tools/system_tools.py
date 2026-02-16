import subprocess
import os
import webbrowser
from datetime import datetime
import mss
from PIL import Image

class SystemTools:
    def __init__(self, registry):
        self.registry = registry
        self.registry.register("open_app", self.open_app)
        self.registry.register("open_url", self.open_url)

    def screenshot(self, filename: str = None) -> str:
        """
        Capture l'écran principal et sauvegarde l'image.
        """

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)

        filepath = os.path.join(screenshots_dir, filename)

        with mss.mss() as sct:
            monitor = sct.monitors[1]  # écran principal
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            img.save(filepath)

        return f"Screenshot enregistré : {filepath}"

        
    def open_app(self, app_name: str):
        app = app_name.lower()
        apps = self.registry.apps

        if app not in apps:
            return f"Application inconnue: {app}"

        config = apps[app]

        if config["type"] == "exe":
            path = config["path"]
            subprocess.Popen(path)
            return f"Ouverture de {app}."

        if config["type"] == "system":
            subprocess.Popen(config["command"], shell=True)
            return f"Ouverture de {app}."

        return "Type non supporté."


    def open_url(self, url: str):
        webbrowser.open(url)
        return f"Ouverture de {url}"
