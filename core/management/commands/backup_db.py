"""
Management command: backup_db

Uso:
  python manage.py backup_db

Comportamento:
  - PostgreSQL: executa pg_dump e salva em backups/backup_YYYYMMDD_HHMMSS.sql.gz
  - SQLite:     copia db.sqlite3 para backups/backup_YYYYMMDD_HHMMSS.db
"""
import gzip
import logging
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Cria backup do banco de dados (PostgreSQL ou SQLite)."

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        db_config = settings.DATABASES["default"]
        engine = db_config["ENGINE"]

        if "postgresql" in engine:
            self._backup_postgres(db_config, backup_dir, timestamp)
        elif "sqlite3" in engine:
            self._backup_sqlite(db_config, backup_dir, timestamp)
        else:
            raise CommandError(f"Engine nao suportada para backup: {engine}")

    def _backup_postgres(self, db_config, backup_dir, timestamp):
        destino = backup_dir / f"backup_{timestamp}.sql.gz"
        env = {
            "PGPASSWORD": db_config.get("PASSWORD", ""),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        }
        cmd = [
            "pg_dump",
            "--host", db_config.get("HOST", "localhost"),
            "--port", str(db_config.get("PORT", "5432")),
            "--username", db_config.get("USER", "postgres"),
            "--no-password",
            "--format", "plain",
            db_config.get("NAME", ""),
        ]

        self.stdout.write(f"Executando pg_dump para {db_config.get('NAME')} ...")
        try:
            resultado = subprocess.run(
                cmd,
                capture_output=True,
                env=env,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="replace")
            raise CommandError(f"pg_dump falhou: {stderr}") from exc
        except FileNotFoundError:
            raise CommandError("pg_dump nao encontrado. Instale o cliente PostgreSQL.")

        with gzip.open(destino, "wb") as f_gz:
            f_gz.write(resultado.stdout)

        tamanho = destino.stat().st_size
        msg = f"Backup PostgreSQL criado: {destino} ({tamanho:,} bytes)"
        self.stdout.write(self.style.SUCCESS(msg))
        logger.info(msg)

    def _backup_sqlite(self, db_config, backup_dir, timestamp):
        db_path = Path(db_config["NAME"])
        if not db_path.exists():
            raise CommandError(f"Banco SQLite nao encontrado: {db_path}")

        destino = backup_dir / f"backup_{timestamp}.db"
        shutil.copy2(db_path, destino)

        tamanho = destino.stat().st_size
        msg = f"Backup SQLite criado: {destino} ({tamanho:,} bytes)"
        self.stdout.write(self.style.SUCCESS(msg))
        logger.info(msg)
