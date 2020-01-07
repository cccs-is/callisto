from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'gallery'

    def ready(self):
        import gallery.signals
