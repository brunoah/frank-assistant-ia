# 🤖 FRANK Assistant

**FRANK** est un assistant IA local modulaire, conçu pour les
développeurs avancés. Architecture propre, système de plugins, mémoire
persistante, RAG local et HUD dynamique.

------------------------------------------------------------------------

## 🚀 Vision

Construire un assistant IA **offline-first**, extensible, robuste et
professionnel.

FRANK n'est pas un simple script vocal. C'est une base technique pour un
assistant intelligent évolutif.

------------------------------------------------------------------------

## ✨ Fonctionnalités principales

-   🎙 Wake-word + reconnaissance vocale
-   🧠 Orchestrator intelligent
-   🛠 Système de plugins (Tool Registry)
-   💾 Mémoire persistante (projets, préférences, état)
-   📚 RAG local (vector store)
-   🎨 HUD animé avec états dynamiques
-   🔌 Architecture modulaire extensible
-   🧾 Logs structurés et lisibles

------------------------------------------------------------------------

## 🏗 Architecture

    src/
     ├── core/          # Orchestrator & logique centrale
     ├── tools/         # Plugins & outils
     ├── memory/        # Mémoire long terme & profil
     ├── rag/           # Indexation & recherche
     ├── ui/            # HUD & interface visuelle
     └── config/        # Configuration centralisée

------------------------------------------------------------------------

## ⚙ Installation

``` bash
git clone https://github.com/brunoah/frank-assistant-ia.git
cd frank-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/run.py
```

------------------------------------------------------------------------

## 🔌 Système de Plugins

FRANK supporte une architecture plugin :

``` python
class ToolPlugin:
    name = "weather"
    description = "Get weather info"

    def run(self, **kwargs):
        pass
```

Les plugins peuvent être chargés dynamiquement pour étendre les
capacités.

------------------------------------------------------------------------

## 🗺 Roadmap

Consulter la roadmap stratégique :\
👉 [ROADMAP](ROADMAP.md)

------------------------------------------------------------------------

## 📦 Objectif v1.0

-   Assistant local stable
-   Système plugin officiel
-   Packaging pip installable
-   CLI officielle
-   Release publique documentée

------------------------------------------------------------------------

## 🤝 Contribution

Les contributions sont bienvenues.\
Voir : [CONTRIBUTING.md](CONTRIBUTING.md)

------------------------------------------------------------------------

## 📜 Licence

MIT License --- voir LICENSE.txt

------------------------------------------------------------------------

## 👤 Auteur

Bruno Ahée\
Projet initié en 2026

------------------------------------------------------------------------

**FRANK Assistant -- Assistant IA local modulaire, pensé pour durer.**

