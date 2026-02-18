import os
import subprocess
from datetime import datetime
import shutil
from typing import Dict

class CameraTools:
    """
    Tools caméra basés sur un flux RTSP (Tapo).
    - camera_snapshot : capture 1 frame et l'enregistre en fichier
    - camera_open_stream : ouvre le flux dans un lecteur (ffplay si dispo)
    """

    def __init__(self, registry):
        self.registry = registry
        self.registry.register("camera_snapshot", self.camera_snapshot)
        self.registry.register("camera_open_stream", self.camera_open_stream)

    def _get_rtsp_url(self, camera: str = "exterieure") -> str:

        key_map = {
            "exterieure": "TAPO_EXTERIEURE_RTSP_URL",
            "interieure": "TAPO_INTERIEURE_RTSP_URL",
        }

        camera = (camera or "").lower().strip()
        env_key = key_map.get(camera)

        if not env_key:
            raise RuntimeError(f"Caméra inconnue : {camera}")

        url = os.getenv(env_key, "").strip()

        if not url:
            raise RuntimeError(f"Variable d'environnement {env_key} manquante.")

        return url


    def camera_snapshot(self, camera: str = "éxterieure", filename: str | None = None) -> str:
        """
        Capture une image du flux RTSP et sauvegarde dans ./screenshots/
        """
        rtsp_url = self._get_rtsp_url(camera=camera)

        # Import ici pour éviter de casser le projet si opencv n'est pas installé
        import cv2

        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"camera_{camera}_{ts}.jpg"

        out_dir = "screenshots"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, filename)

        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            return {
                "status": "error",
                "message": "Impossible d'ouvrir le flux RTSP."
            }

        ok, frame = cap.read()
        cap.release()

        if not ok or frame is None:
            return {
                "status": "error",
                "message": "Flux ouvert mais aucune image récupérée."
            }

        cv2.imwrite(out_path, frame)

        return {
            "status": "success",
            "type": "snapshot",
            "path": out_path,
            "camera": camera
        }

    def camera_open_stream(self, camera: str = "tapo") -> Dict:
        try:
            url = self._get_rtsp_url(camera)

            # 1) Cherche ffplay
            ffplay = shutil.which("ffplay")
            vlc = shutil.which("vlc")

            if ffplay:
                cmd = [ffplay, "-rtsp_transport", "tcp", "-i", url]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return {"status": "success", "type": "stream", "camera": camera, "player": "ffplay"}

            # 2) Fallback VLC
            if vlc:
                cmd = [vlc, url]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return {"status": "success", "type": "stream", "camera": camera, "player": "vlc"}


            # 3) Rien trouvé -> erreur explicite
            print("❌ CAMERA ERROR:", e) 
            return {
                "status": "error",
                "type": "stream",
                "camera": camera,
                "message": "Aucun lecteur trouvé (ffplay ou vlc). Installe ffmpeg (ffplay) ou VLC et ajoute au PATH."
            }

        except Exception as e:
            return {"status": "error", "type": "stream", "camera": camera, "message": str(e)}
