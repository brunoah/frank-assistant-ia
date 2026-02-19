import shutil
from max_assistant_v2.config.paths import (
    MEMORY_DIR,
    PROJECTS_DIR,
    DATA_DIR,
    RDV_DIR
)
from max_assistant_v2.utils.logger import get_logger

log = get_logger(__name__)


class DataManager:

    @staticmethod
    def reset_all():
        """
        Supprime toutes les données persistantes du système.
        """

        for folder in [MEMORY_DIR, PROJECTS_DIR, DATA_DIR, RDV_DIR]:
            if folder.exists():
                shutil.rmtree(folder)
                log.warning(f"🗑 Suppression dossier: {folder}")

        log.critical("🔥 FACTORY RESET COMPLET EFFECTUÉ")
