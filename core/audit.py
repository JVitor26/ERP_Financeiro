from datetime import date, datetime
from decimal import Decimal


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "")[:255]


def request_context(request):
    if request is None:
        return {}
    return {
        "ip": get_client_ip(request),
        "dispositivo": get_user_agent(request),
        "origem": "api",
        "metadados": {
            "method": request.method,
            "path": request.get_full_path(),
        },
    }


def json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "name"):
        return str(value)
    return value


def snapshot_model(instance):
    return {
        field.name: "***" if field.name in {"password", "mfa_secret"} else json_safe(field.value_from_object(instance))
        for field in instance._meta.concrete_fields
    }


def diff_snapshots(before, after):
    diff = {}
    for key in sorted(set(before) | set(after)):
        old = before.get(key)
        new = after.get(key)
        if old != new:
            diff[key] = {"anterior": old, "novo": new}
    return diff
