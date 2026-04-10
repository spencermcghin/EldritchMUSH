from django.apps import AppConfig


class EldritchAppConfig(AppConfig):
    name = "eldritch_app"
    label = "eldritch_app"
    verbose_name = "EldritchMUSH App"

    def ready(self):
        # Import signal handlers so they connect when the app loads.
        # Wrapped in try/except so a missing optional dep (allauth)
        # doesn't prevent server startup.
        try:
            from eldritch_app import signals  # noqa: F401
        except Exception as exc:
            print(f"[eldritch_app] Could not load signal handlers: {exc}")
