import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "erp_financeiro.settings")

app = Celery("erp_financeiro")

# Lê configuração do Django settings com namespace CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descobre tasks automaticamente em todos os apps instalados
app.autodiscover_tasks()

# Beat schedule explícito com crontab para precisão horária
app.conf.beat_schedule = {
    # Previsão de caixa: todos os dias às 06:00
    "previsao_caixa_diaria": {
        "task": "inteligencia.tasks.previsao_caixa",
        "schedule": crontab(hour=6, minute=0),
    },
    # Alertas de vencimento: todos os dias às 07:00
    "alertas_vencimento_diarios": {
        "task": "core.tasks.alertas_vencimento",
        "schedule": crontab(hour=7, minute=0),
    },
    # Cobrança automática: todos os dias às 08:00
    "cobranca_automatica_diaria": {
        "task": "financeiro.tasks.cobranca_automatica",
        "schedule": crontab(hour=8, minute=0),
    },
    # Importação bancária: a cada 4 horas (00, 04, 08, 12, 16, 20)
    "importacao_bancaria_4h": {
        "task": "financeiro.tasks.importacao_bancaria",
        "schedule": crontab(minute=0, hour="0,4,8,12,16,20"),
    },
    # Fechamento diário: meia-noite
    "fechamento_diario_meia_noite": {
        "task": "financeiro.tasks.fechamento_diario",
        "schedule": crontab(hour=0, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
