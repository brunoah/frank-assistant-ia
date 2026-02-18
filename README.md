# 🤖 F.R.A.N.K Assistant IA - (Flexible Reactive Autonomous Neural Kernel)
**F.R.A.N.K** est un assistant IA **local** et **modulaire**, pensé pour
servir de base solide à un assistant vocal évolutif : orchestration
d'outils (plugins), mémoire persistante, RAG local, HUD dynamique et
**API Web** (FastAPI).

⭐ Si ce projet t'intéresse, n'hésite pas à lui attribuer une étoile.

------------------------------------------------------------------------

## 🚀 Vision

Construire un assistant IA **offline-first**, extensible, robuste et
professionnel.

F.R.A.N.K n'est pas un simple script vocal : c'est une architecture complète
(core + tools + mémoire + UI + API) conçue pour durer.

------------------------------------------------------------------------

## ✨ Fonctionnalités principales

### 🎙️ Voix & interaction

-   Wake-word + boucle d'écoute
-   STT (transcription) intégré
-   TTS (Piper) pour la voix FR

### 🧠 Orchestration & "intelligence"

-   **Orchestrator** (boucle principale)
-   **Router + Planner** (décision d'action / outil à appeler)
-   **Analyse comportementale** (BehaviorAnalyzer)
-   **Mémoire persistante** (profil, projets, long terme)
-   **RAG local** (vector store FAISS)

### 🛠️ Tools (plugins)

-   **SystemTools** : ouverture d'apps, webbrowser, screenshot, etc.
-   **WebTools** :
    -   `weather(city)` via OpenWeather
    -   `web_search(query, num_results)` via Serper (Google Serper API)
-   **CameraTools** : RTSP (ex : Tapo) → snapshot + ouverture de flux
-   **ImageTools** : génération d'images via API OpenAI-compatible (ex :
    LM Studio)

### 🎨 UI / HUD

-   HUD animé (GIF) + états dynamiques (calme, focus, réflexion,
    speaking, erreur...)

### 🌐 API Web (FastAPI)

-   Interface Web statique (page `/`)
-   API `/ask` (texte), `/voice` (audio), `/health` (status)

------------------------------------------------------------------------

# 🏗 Architecture (vue simplifiée)

``` mermaid
flowchart TD
User -->|Voice| STT
User -->|Web UI / API| WebAPI

STT --> Orchestrator
WebAPI --> Orchestrator

Orchestrator --> Router
Router --> Planner
Router --> Tools
Router --> Memory
Router --> RAG
Orchestrator --> TTS
Orchestrator --> HUD

Tools --> Orchestrator
Memory --> Orchestrator
RAG --> Orchestrator
TTS -->|Voice| User
HUD -->|Visual| User
```

------------------------------------------------------------------------

# 🌐 API Web (FastAPI)

Le serveur est exposé depuis `src/max_assistant_v2/web/server.py` et
lancé via `scripts/run.py` (uvicorn).

## Endpoints

-   `GET /` : sert l'UI (`index.html` via `/static`)
-   `POST /ask` : envoie un texte à FRANK, retourne
    `{response, state, ...}`
-   `POST /voice` : upload audio (webm) → conversion wav → transcription
    STT → réponse
-   `GET /health` : endpoint santé

## Sécurité (token simple)

Un token est requis côté API : - Variable d'environnement :
`FRANK_WEB_TOKEN` - Si absent : valeur par défaut `frank-local-token` (à
changer en prod)

> ⚠️ Le endpoint `/voice` dépend de **ffmpeg** (conversion webm → wav 16
> kHz mono).

------------------------------------------------------------------------

# 🔌 Tools Web : météo + recherche

## 🌦 Météo (OpenWeather)

Tool : `weather(city="Paris")`\
Var env requise : `OPENWEATHER_API_KEY`

## 🔎 Web Search (Serper)

Tool : `web_search(query, num_results=5)`\
Var env requise : `SERPER_API_KEY`

------------------------------------------------------------------------

# 🖼 Générateur d'images

Tool : `ImageTools` (génération d'images)\
Variables d'environnement typiques : - `OPENAI_BASE_URL` (ex :
`http://localhost:1234/v1` pour LM Studio) - `OPENAI_API_KEY` (ex :
`lm-studio` si tu utilises LM Studio)

Les images sont sauvegardées dans : `data/generated_images/`

------------------------------------------------------------------------

# 📷 Caméras RTSP (Tapo / autre)

Tools : `camera_snapshot`, `camera_open_stream`

Variables d'environnement (exemples) : - `TAPO_EXTERIEURE_RTSP_URL` -
`TAPO_INTERIEURE_RTSP_URL`

> Le flux est ouvert via un lecteur (ex : ffplay si dispo) et les
> snapshots utilisent ffmpeg.

------------------------------------------------------------------------

# 📂 Structure du projet

    assets/                     # gifs, ressources HUD
    data/                       # mémoire, projets, vector_store, .env (local)
    scripts/
      └── run.py                # entrypoint (charge .env + lance API)
    src/max_assistant_v2/
      ├── agents/               # planner/executor
      ├── config/               # identity + settings
      ├── core/                 # assistant, orchestrator, router, project manager
      ├── llm/                  # client LM Studio
      ├── memory/               # profile, long_term, vector_store (FAISS)
      ├── stt/                  # whisper engine
      ├── tts/                  # piper engine
      ├── tools/                # system/web/camera/image tools + registry
      ├── ui/                   # HUD
      └── web/                  # fastapi server + static UI

------------------------------------------------------------------------

## ⚙️ Installation

``` bash
git clone https://github.com/brunoah/frank-assistant-ia.git
cd frank-assistant-ia
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/run.py
```

> Si tu as `update_requirements.bat`, il peut servir à régénérer un
> `requirements.txt` propre.

------------------------------------------------------------------------

## 🔐 Configuration (.env)

F.R.A.N.K charge `data/.env` au démarrage.

Exemple **sans secrets** :

``` env
# Web
FRANK_WEB_TOKEN=change-me

# Web tools
SERPER_API_KEY=your_key
OPENWEATHER_API_KEY=your_key

# OpenAI-compatible (LM Studio)
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio

# Cameras RTSP
TAPO_EXTERIEURE_RTSP_URL=rtsp://user:pass@192.168.1.xx:554/stream1
TAPO_INTERIEURE_RTSP_URL=rtsp://user:pass@192.168.1.yy:554/stream1
```

✅ Recommandé : **ne jamais commit** `data/.env` (ajoute-le au
`.gitignore`).

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

## 🧾 Notes importantes

-   `src/max_assistant_v2/config/settings.py` contient des chemins
    Windows (Piper, data dir, etc.) : adapte-les selon ta machine.
-   L'API `/voice` nécessite `ffmpeg` installé et accessible dans le
    PATH.
-   Le fichier `src/max_assistant_v2/tools/web_search.py` existe mais
    est **vide** : la recherche web est implémentée dans
    `WebTools.web_search()`.

------------------------------------------------------------------------

## 📜 Licence

MIT License --- voir `LICENSE.txt`

------------------------------------------------------------------------

## 👤 Auteur

Bruno Ahée

🔗 LinkedIn : https://www.linkedin.com/in/bruno-ah%C3%A9e-a8451a313/

Projet initié en 2026

------------------------------------------------------------------------

**F.R.A.N.K Assistant --- Assistant IA local modulaire, pensé pour durer.**
