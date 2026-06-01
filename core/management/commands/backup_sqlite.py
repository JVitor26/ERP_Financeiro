from pathlib import Path
from shutil import copy2

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Cria backup simples do banco SQLite de desenvolvimento."

    def handle(self, *args, **options):
        db_name = settings.DATABASES["default"]["NAME"]
        db_path = Path(db_name)
        if not db_path.exists():
            raise CommandError(f"Banco SQLite nao encontrado: {db_path}")
        backup_dir = settings.BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)
        destino = backup_dir / f"db-{timezone.now():%Y%m%d-%H%M%S}.sqlite3"
        copy2(db_path, destino)
        self.stdout.write(self.style.SUCCESS(f"Backup criado: {destino}"))
