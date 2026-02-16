import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk, ImageSequence
from typing import Tuple, Dict

class SpeakingHUD:
    def __init__(self, gif_rel_path="assets/speaking.gif", size=(600, 337), delay_ms=40):

        # --- ÉTAT EN PREMIER ---
        self.state = "calme"
        self.volume = 0.0

        # ---- NOUVEL ETAT HUD INTERNE ----
        self.hud_mode = "idle"       # idle / analyzing / speaking / error
        self.hud_source = None       # llm / tool / web / system / voice


        self.STATE_COLORS = {
            "calme": (0, 120, 255),
            "focus": (140, 0, 255),
            "reflexion": (255, 170, 0),
            "erreur": (255, 0, 0),
        }

        self.TINT_ALPHA = 120

        # --- Ensuite seulement le reste ---
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.attributes("-transparentcolor", "black")

        self.canvas = tk.Canvas(
        self.root,
            bg="black",
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True)


        self.delay = int(delay_ms)
        self.size = size

        self.running = False
        self.frame_index = 0
        self.frames = []

        self._load_gif(gif_rel_path)


        self.volume = 0.0

        
        # Couleurs RGB par état (tu peux ajuster)
        self.STATE_COLORS: Dict[str, Tuple[int, int, int]] = {
            "calme": (0, 120, 255),       # bleu doux
            "focus": (140, 0, 255),       # violet
            "reflexion": (255, 170, 0),   # ambre
            "erreur": (255, 0, 0),        # rouge
        }

        # Force de la teinte (0-255). 110-140 marche bien.
        self.TINT_ALPHA = 120


    def set_volume(self, value):
        self.volume = min(max(value * 4.0, 0), 1.0)    

    def set_state(self, state: str):
        """Thread-safe: change l'état visuel (calme/focus/reflexion/erreur)."""
        self.root.after(0, self._set_state_on_ui_thread, state)

    def _set_state_on_ui_thread(self, state: str):
        state = (state or "").lower().strip()
        if state in self.STATE_COLORS:
            self.state = state
        else:
            # Fallback sécurité
            self.state = "calme"


    def _project_root(self) -> Path:
        # hud.py = .../src/max_assistant_v2/ui/hud.py => parents[3] = racine projet
        return Path(__file__).resolve().parents[3]

    def _load_gif(self, gif_rel_path: str):
        self.original_frames = []
        self.frames = []

        gif_path = self._project_root() / gif_rel_path
        if not gif_path.exists():
            raise FileNotFoundError(f"GIF introuvable: {gif_path}")

        gif = Image.open(gif_path)

        for frame in ImageSequence.Iterator(gif):
            frame = frame.convert("RGBA").resize(self.size)

            self.original_frames.append(frame.copy())  # 🟢 Image PIL pour scaling
            self.frames.append(ImageTk.PhotoImage(frame))  # 🟢 Version Tk pour affichage

        if not self.frames:
            raise RuntimeError("Aucune frame chargée depuis le GIF.")


    # ---------- Thread-safe API ----------
    # Ces méthodes peuvent être appelées depuis n'importe quel thread.
    def show(self):
        self.root.after(0, self._show_on_ui_thread)

    def hide(self):
        self.root.after(0, self._hide_on_ui_thread)

    # ---------- UI thread only ----------
    def _show_on_ui_thread(self):
        if self.running:
            return

        self.running = True
        self.frame_index = 0

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.screen_width = sw
        self.screen_height = sh
        w = self.frames[0].width()
        h = self.frames[0].height()

        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.deiconify()
        self.animate_step()

    def _hide_on_ui_thread(self):
        self.running = False
        self.root.withdraw()

    def _tint_rgba_keep_transparency(self, img: Image.Image, rgb: Tuple[int, int, int], tint_alpha: int) -> Image.Image:
        """
        Applique une teinte colorée sur une image RGBA en conservant la transparence originale.
        - Les pixels totalement transparents restent totalement transparents.
        """
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        r, g, b = rgb
        tint_alpha = max(0, min(int(tint_alpha), 255))

        # Masque = alpha original, modulé par tint_alpha
        a = img.getchannel("A")
        mask = a.point(lambda px: (px * tint_alpha) // 255)

        overlay = Image.new("RGBA", img.size, (r, g, b, 0))
        overlay.putalpha(mask)

        return Image.alpha_composite(img, overlay)


    def animate_step(self):
        if not self.running:
            return

        orig = self.original_frames[self.frame_index]

        scale = 1.0 + (self.volume * 0.2)
        w = int(orig.width * scale)
        h = int(orig.height * scale)

        resized = orig.resize((w, h))

        # --- Teinte dynamique ---
        if self.state == "calme":
            tinted = resized
        else:
            rgb = self.STATE_COLORS[self.state]
            tinted = self._tint_rgba_keep_transparency(
                resized,
                rgb,
                self.TINT_ALPHA
            )

        photo = ImageTk.PhotoImage(tinted)



        self.canvas.delete("gif")

        self.canvas.create_image(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            image=photo,
            tags="gif"
        )

        self.canvas.image = photo



        self.frame_index = (self.frame_index + 1) % len(self.original_frames)

        self.root.after(self.delay, self.animate_step)

