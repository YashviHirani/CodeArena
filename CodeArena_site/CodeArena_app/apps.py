from django.apps import AppConfig


class CodearenaAppConfig(AppConfig):
    name = 'CodeArena_app'
    
    def ready(self):
        import CodeArena_app.signals