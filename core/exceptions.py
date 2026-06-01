from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

    response = exception_handler(exc, context)
    if response is None:
        return None

    response.data = {
        "status_code": response.status_code,
        "detail": response.data,
    }
    return response
