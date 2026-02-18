import cv2
import threading


class WebcamTools:
    """
    Tools pour webcam locale (USB / intégrée)
    """

    def __init__(self, registry):
        self.registry = registry
        self.registry.register("webcam_open", self.webcam_open)
        self.registry.register("webcam_close", self.webcam_close)

        self.cap = None
        self.running = False
        self.thread = None

    def webcam_open(self, camera_index: int = 0):
        """
        Ouvre la webcam dans une fenêtre OpenCV.
        """
        if self.running:
            return "La webcam est déjà ouverte."

        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Forcer MJPG (très important sur Windows)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        if not self.cap.isOpened():
            return "Impossible d'ouvrir la webcam."

        self.running = True

        def _loop():
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    break

                cv2.imshow("FRANK - Webcam", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            self._cleanup()

        self.thread = threading.Thread(target=_loop, daemon=True)
        self.thread.start()

        return "Webcam ouverte."

    def webcam_close(self):
        """
        Ferme la webcam proprement.
        """
        if not self.running:
            return "La webcam n'est pas active."

        self.running = False
        return "Fermeture de la webcam."

    def _cleanup(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.running = False
