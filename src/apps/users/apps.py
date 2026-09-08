from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    def ready(self):
        # Registers the login-throttle receivers. Imported here rather than at
        # module level so the app registry is fully populated first.
        from . import signals  # noqa: F401
