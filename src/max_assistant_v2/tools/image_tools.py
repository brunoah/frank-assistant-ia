import os
import base64
from datetime import datetime
from pathlib import Path

from openai import OpenAI


class ImageTools:
    """
    Génération d'images via OpenAI.
    Enregistre un PNG dans: data/generated_images/
    """

    def __init__(self, registry):
        self.registry = registry
        self.registry.register("image_generate", self.image_generate)

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY manquante dans data/.env")

        self.client = OpenAI(api_key=api_key)

        # On garde tout dans /data (cohérent avec ton projet)
        project_root = Path(__file__).resolve().parents[3]
        self.output_dir = project_root / "data" / "generated_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def image_generate(self, prompt: str, size: str = "1024x1024") -> str:
        """
        prompt: description de l'image
        size: "1024x1024" (par défaut), "512x512" etc.
        """
        prompt = (prompt or "").strip()
        if not prompt:
            return "Prompt manquant. Dis-moi quoi générer."

        try:
            result = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,
            )

            b64 = result.data[0].b64_json
            img_bytes = base64.b64decode(b64)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{ts}.png"
            out_path = self.output_dir / filename

            out_path.write_bytes(img_bytes)

            return f"Image générée : {out_path}"

        except Exception as e:
            return f"Erreur génération image : {e}"
