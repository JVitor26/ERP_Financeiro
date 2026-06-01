"""
Management command: restore_db

Uso:
  python manage.py restore_db <arquivo>

Comportamento:
  - .sql.gz  (PostgreSQL): descomprime e executa psql
  - .db      (SQLite):     sobrescreve o db.sqlite3 atual
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
    help = "Restaura backup do banco de dados (PostgreSQL .sql.gz ou SQLite .db)."

    def add_arguments(self, parser):
        parser.add_argument(
            "arquivo",
            type=str,
            help="Caminho para o arquivo de backup (.sql.gz para PostgreSQL, .db para SQLite).",
        )

    def handle(self, *args, **options):
        arquivo_str = options["arquivo"]
        arquivo = Path(arquivo_str)

        if not arquivo.exists():
            raise CommandError(f"Arquivo nao encontrado: {arquivo}")

        db_config = settings.DATABASES["default"]
        engine = db_config["ENGINE"]
        sufixo = arquivo.suffix.lower()

        if sufixo == ".gz" and arquivo.stem.endswith(".sql"):
            if "postgresql" not in engine:
                raise CommandError("Arquivo .sql.gz requer banco PostgreSQL configurado.")
            self._restore_postgres(db_config, arquivo)
        elif sufixo == ".db":
            if "sqlite3" not in engine:
                raise CommandError("Arquivo .db requer banco SQLite configurado.")
            self._restore_sqlite(db_config, arquivo)
        else:
            raise CommandError(
                f"Extensao nao reconhecida: '{arquivo.suffix}'. "
                "Use .sql.gz (PostgreSQL) ou .db (SQLite)."
            )

    def _restore_postgres(self, db_config, arquivo):
        """Descomprime o .sql.gz e executa via psql."""
        self.stdout.write(f"Restaurando PostgreSQL a partir de {arquivo} ...")

        env = {
            "PGPASSWORD": db_config.get("PASSWORD", ""),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        }
        cmd = [
            "psql",
            "--host", db_config.get("HOST", "localhost"),
            "--port", str(db_config.get("PORT", "5432")),
            "--username", db_config.get("USER", "postgres"),
            "--dbname", db_config.get("NAME", ""),
            "--no-password",
        ]

        try:
            with gzip.open(arquivo, "rb") as f_gz:
                sql_bytes = f_gz.read()
        except (gzip.BadGzipFile, OSError) as exc:
            raise CommandError(f"Falha ao descomprimir {arquivo}: {exc}") from exc

        try:
            resultado = subprocess.run(
                cmd,
                input=sql_bytes,
                capture_output=True,
                env=env,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="replace")
            raise CommandError(f"psql falhou: {stderr}") from exc
        except FileNotFoundError:
            raise CommandError("psql nao encontrado. Instale o cliente PostgreSQL.")

        msg = f"Restore PostgreSQL concluido a partir de {arquivo}"
        self.stdout.write(self.style.SUCCESS(msg))
        logger.info(msg)

    def _restore_sqlite(self, db_config, arquivo):
        """Copia o arquivo .db sobre o banco SQLite atual (faz backup antes)."""
        db_path = Path(db_config["NAME"])
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup de segurança do banco atual antes de sobrescrever
        if db_path.exists():
            ts = timezone.now().strftime("%Y%m%d_%H%M%S")
            seguranca = backup_dir / f"pre_restore_{ts}.db"
            shutil.copy2(db_path, seguranca)
            self.stdout.write(f"Backup de seguranca criado: {seguranca}")

        shutil.copy2(arquivo, db_path)
        msg = f"Restore SQLite concluido: {arquivo} -> {db_path}"
        self.stdout.write(self.style.SUCCESS(msg))
        logger.info(msg)
