# Garante que o app Celery seja carregado quando o Django inicializar,
# para que os decoradores @shared_task funcionem corretamente.
from .celery import app as celery_app

__all__ = ("celery_app",)
