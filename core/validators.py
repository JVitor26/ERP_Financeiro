"""
Validators de senha personalizados para o ERP Financeiro.

Implementam a interface Django password validator:
  - validate(password, user=None)
  - get_help_text()
"""
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SenhaComplexidadeValidator:
    """
    Exige que a senha contenha:
    - pelo menos uma letra maiúscula
    - pelo menos uma letra minúscula
    - pelo menos um dígito numérico
    - pelo menos um caractere especial (@$!%*?&#+\-_=^~)
    """

    ESPECIAIS = r"[@$!%*?&#+\-_=^~]"

    def validate(self, password, user=None):
        errors = []
        if not re.search(r"[A-Z]", password):
            errors.append(
                ValidationError(
                    _("A senha deve conter pelo menos uma letra maiuscula."),
                    code="password_no_upper",
                )
            )
        if not re.search(r"[a-z]", password):
            errors.append(
                ValidationError(
                    _("A senha deve conter pelo menos uma letra minuscula."),
                    code="password_no_lower",
                )
            )
        if not re.search(r"\d", password):
            errors.append(
                ValidationError(
                    _("A senha deve conter pelo menos um numero."),
                    code="password_no_digit",
                )
            )
        if not re.search(self.ESPECIAIS, password):
            errors.append(
                ValidationError(
                    _("A senha deve conter pelo menos um caractere especial (@$!%*?&#+_-=^~)."),
                    code="password_no_special",
                )
            )
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Sua senha deve conter pelo menos uma letra maiuscula, "
            "uma minuscula, um numero e um caractere especial (@$!%*?&#+_-=^~)."
        )


class SenhaHistoricoValidator:
    """
    Impede a reutilização das últimas N senhas (padrão: 5).
    Consulta o model HistoricoSenha para verificar o histórico.
    """

    def __init__(self, num_senhas=5):
        self.num_senhas = num_senhas

    def validate(self, password, user=None):
        if user is None or not user.pk:
            return

        # Import local para evitar circular import (models importa validators via settings)
        from django.contrib.auth.hashers import check_password

        from core.models import HistoricoSenha

        historico = (
            HistoricoSenha.objects.filter(usuario=user)
            .order_by("-criado_em")[: self.num_senhas]
        )
        for entrada in historico:
            if check_password(password, entrada.hash_senha):
                raise ValidationError(
                    _(
                        "Voce nao pode reutilizar uma das suas ultimas %(num)d senhas."
                    )
                    % {"num": self.num_senhas},
                    code="password_already_used",
                )

    def get_help_text(self):
        return _(
            "Sua senha nao pode ser igual a nenhuma das suas ultimas %(num)d senhas."
        ) % {"num": self.num_senhas}
