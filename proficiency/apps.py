from django.apps import AppConfig


class ProficiencyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'proficiency'
    
    def ready(self):
        """Import signals khi app được load"""
        import proficiency.signals  # noqa