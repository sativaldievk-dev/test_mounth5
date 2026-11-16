"""Blog application configuration."""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Configuration for blog models and API endpoints."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"
