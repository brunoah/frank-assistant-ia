import threading
import time
from datetime import datetime, timedelta


class AgendaReminderService:
    def __init__(self, agenda_manager, speak_callback):
        self.agenda_manager = agenda_manager
        self.speak_callback = speak_callback
        self.running = False
        self.already_notified = set()

    def start(self):
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._run_loop, daemon=True)
            thread.start()

    def stop(self):
        self.running = False

    def _run_loop(self):
        while self.running:
            try:
                self._check_events()
            except Exception as e:
                print(f"[Reminder Error] {e}")

            time.sleep(30)  # vérifie toutes les 30 secondes

    def _check_events(self):
        events = self.agenda_manager._load()
        now = datetime.now()

        for event in events:
            event_id = f"{event['date']} {event['time']} {event['title']}"

            if event_id in self.already_notified:
                continue

            event_datetime = datetime.strptime(
                f"{event['date']} {event['time']}",
                "%Y-%m-%d %H:%M"
            )

            delta = event_datetime - now

            # 5 minutes avant
            if timedelta(minutes=0) <= delta <= timedelta(minutes=5):
                message = f"Ton rendez-vous {event['title']} commence dans moins de 5 minutes."
                self.speak_callback(message)
                self.already_notified.add(event_id)
                print("👂 En écoute...")
