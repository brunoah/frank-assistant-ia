import json
from pathlib import Path
from datetime import datetime, timedelta
import re

class AgendaManager:
    def __init__(self):
        project_root = Path(__file__).resolve().parents[3]
        self.path = project_root / "data" / "agenda.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        if not self.path.exists():
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _parse_natural_date(self, date_str):
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")

        date_str = date_str.lower().strip()
        now = datetime.now()

        # demain
        if date_str == "demain":
            return (now + timedelta(days=1)).strftime("%Y-%m-%d")

        # aujourd'hui
        if date_str in ["aujourd'hui", "aujourdhui"]:
            return now.strftime("%Y-%m-%d")

        # dans X jours
        match_days = re.search(r"dans (\d+) jour", date_str)
        if match_days:
            days = int(match_days.group(1))
            return (now + timedelta(days=days)).strftime("%Y-%m-%d")

        # jour de la semaine
        weekdays = {
            "lundi": 0,
            "mardi": 1,
            "mercredi": 2,
            "jeudi": 3,
            "vendredi": 4,
            "samedi": 5,
            "dimanche": 6
        }

        for day_name, day_index in weekdays.items():
            if day_name in date_str:
                current_weekday = now.weekday()
                delta = (day_index - current_weekday) % 7

                if "prochain" in date_str or delta == 0:
                    delta += 7

                return (now + timedelta(days=delta)).strftime("%Y-%m-%d")

        # fallback : si déjà format YYYY-MM-DD
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except:
            return now.strftime("%Y-%m-%d")

    def _parse_natural_time(self, time_str):
        if not time_str:
            return "09:00"

        time_str = time_str.lower().strip()

        # 10h → 10:00
        match_hour = re.match(r"(\d{1,2})h$", time_str)
        if match_hour:
            return f"{int(match_hour.group(1)):02d}:00"

        # 10h30
        match_hour_min = re.match(r"(\d{1,2})h(\d{1,2})", time_str)
        if match_hour_min:
            return f"{int(match_hour_min.group(1)):02d}:{int(match_hour_min.group(2)):02d}"

        # 15:30
        match_standard = re.match(r"(\d{1,2}):(\d{1,2})", time_str)
        if match_standard:
            return f"{int(match_standard.group(1)):02d}:{int(match_standard.group(2)):02d}"

        return "09:00"
        

    def _load(self):
        try:
            if not self.path.exists() or self.path.stat().st_size == 0:
                return []

            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)

        except json.JSONDecodeError:
            return []

    def _save(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_event_from_text(self, title, raw_text):

        parsed_date = self._parse_natural_date_from_text(raw_text)
        parsed_time = self._parse_natural_time_from_text(raw_text)

        data = self._load()

        event = {
            "title": title or "Rendez-vous",
            "date": parsed_date,
            "time": parsed_time,
            "created_at": datetime.now().isoformat()
        }

        data.append(event)
        self._save(data)

        return f"Événement ajouté : {event['title']} le {parsed_date} à {parsed_time}"

    def _parse_natural_date_from_text(self, text):
        text = text.lower()
        now = datetime.now()

        if "demain" in text:
            return (now + timedelta(days=1)).strftime("%Y-%m-%d")

        weekdays = {
            "lundi": 0,
            "mardi": 1,
            "mercredi": 2,
            "jeudi": 3,
            "vendredi": 4,
            "samedi": 5,
            "dimanche": 6
        }

        for day_name, day_index in weekdays.items():
            if day_name in text:
                delta = (day_index - now.weekday()) % 7
                if delta == 0:
                    delta = 7
                return (now + timedelta(days=delta)).strftime("%Y-%m-%d")

        return now.strftime("%Y-%m-%d")
    
    def _parse_natural_time_from_text(self, text):
        text = text.lower()

        match = re.search(r"(\d{1,2})h(\d{0,2})", text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            return f"{hour:02d}:{minute:02d}"

        match2 = re.search(r"(\d{1,2}):(\d{2})", text)
        if match2:
            return f"{int(match2.group(1)):02d}:{int(match2.group(2)):02d}"

        return "09:00"


    def add_event(self, title, date, time):

        parsed_date = self._parse_natural_date(date)
        parsed_time = self._parse_natural_time(time)

        data = self._load()

        event = {
            "title": title or "Rendez-vous",
            "date": parsed_date,
            "time": parsed_time,
            "created_at": datetime.now().isoformat()
        }

        data.append(event)
        self._save(data)

        return f"Événement ajouté : {event['title']} le {parsed_date} à {parsed_time}"


    def list_events(self):
        data = self._load()

        if not data:
            return "Aucun événement enregistré."

        # Tri chronologique
        data.sort(key=lambda x: f"{x['date']} {x['time']}")

        from datetime import datetime
        import locale

        try:
            locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_TIME, "French_France")
            except:
                pass


        formatted_output = []
        current_date = None

        for event in data:
            event_datetime = datetime.strptime(
                f"{event['date']} {event['time']}",
                "%Y-%m-%d %H:%M"
            )

            jours = [
                "Lundi", "Mardi", "Mercredi",
                "Jeudi", "Vendredi", "Samedi", "Dimanche"
            ]

            mois = [
                "janvier", "février", "mars", "avril",
                "mai", "juin", "juillet", "août",
                "septembre", "octobre", "novembre", "décembre"
            ]

            jour_nom = jours[event_datetime.weekday()]
            mois_nom = mois[event_datetime.month - 1]

            readable_date = f"{jour_nom} {event_datetime.day} {mois_nom} {event_datetime.year}"

            # Nouveau bloc date
            if event['date'] != current_date:
                formatted_output.append(f"\n {readable_date}")
                current_date = event['date']

            formatted_output.append(f"   • {event['time']} — {event['title']}")

        return "\n".join(formatted_output).strip()


    def delete_event(self, title):
        data = self._load()
        new_data = [e for e in data if e["title"].lower() != title.lower()]

        if len(new_data) == len(data):
            return "Aucun événement trouvé avec ce titre."

        self._save(new_data)
        return f"Événement supprimé : {title}"
