import os
import requests

class WebTools:
    def weather(self, city: str = "Paris") -> str:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return "Clé OPENWEATHER_API_KEY manquante."

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "fr",
        }

        try:
            r = requests.get(url, params=params, timeout=15)
        except Exception as e:
            return f"Erreur réseau météo: {e}"

        if r.status_code != 200:
            # message simple pour la voix
            return f"Impossible de récupérer la météo pour {city}."

        data = r.json()

        name = data.get("name") or city
        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        desc = data["weather"][0]["description"]

        wind = data.get("wind", {}).get("speed", None)
        if wind is not None:
            wind_kmh = round(float(wind) * 3.6)
            return f"À {name}, il fait {temp} degrés, {desc}. Ressenti {feels} degrés. Vent {wind_kmh} kilomètres heure."
        else:
            return f"À {name}, il fait {temp} degrés, {desc}. Ressenti {feels} degrés."

    def web_search(self, query: str, num_results: int = 5) -> str:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return "Clé SERPER_API_KEY manquante."

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "num": int(num_results),
        }

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=20)
        except Exception as e:
            return f"Erreur réseau Serper: {e}"

        if r.status_code != 200:
            return f"Erreur Serper HTTP {r.status_code}: {r.text}"

        data = r.json()
        organic = data.get("organic", []) or []

        if not organic:
            return f"Aucun résultat trouvé pour : {query}"

        # 🔹 Construire un contexte propre
        context_blocks = []
        for item in organic[:num_results]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            block = f"Titre: {title}\nSource: {link}\nExtrait: {snippet}"
            context_blocks.append(block)

        web_context = "\n\n".join(context_blocks)

        # 🔹 IMPORTANT :
        # On renvoie un texte structuré que le modèle pourra résumer ensuite
        return f"""
    RESULTATS WEB POUR: {query}

    {web_context}

    Merci de synthétiser ces informations en une réponse claire, structurée et utile.
    """


