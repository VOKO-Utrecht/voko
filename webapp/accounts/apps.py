from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"
    default = True

    def ready(self):
        import accounts.signals  # noqa: F401
