from django.apps import AppConfig


class WebAppConfig(AppConfig):
    name = "web"
    verbose_name = "EldritchMUSH Web"

    def ready(self):
        # Import signal handlers so they connect when the app loads.
        # Wrapped in try/except so a missing optional dep (allauth) doesn't
        # prevent server startup.
        try:
            from web import signals  # noqa: F401
        except Exception as exc:
            print(f"[web.apps] Could not load signal handlers: {exc}")
