"""Permission classes shared by the HTTP layer.

`SystemPermissions` is the generic registry kept for compatibility with the
existing `CheckPermission` helper in `core/security.py`.

`RequireAdmin` is the admin-only gate used by the operational administration
surface and by the hardened FEST endpoints. It encodes ONE rule, already used
by `modules.salesianos_fest.presentation.ownership.check_ownership_or_admin`
and by the pagos controllers:

    admin = is_staff OR is_superuser

No parallel role model, group table or RBAC system is introduced
(`contract/django-app-architecture-contract.md` §10 — "Permisos centralizados").

Contract: `contract/api-wrapper-presenter-contract.md` §8 — the public message
of a denial comes from the global error catalog in `core/exceptions.py`, never
from the permission class.
"""
from typing import Any

from django.http import HttpRequest
from ninja_extra.permissions import BasePermission


class SystemPermissions:
    """Generic permission registry."""

    @classmethod
    def all(cls) -> list:
        return []


class RequireAdmin(BasePermission):
    """Allows access only to Django admins (`is_staff` OR `is_superuser`).

    Applied on a route, the framework raises `PermissionDenied` (403) when the
    check fails and `core/exceptions.py` translates it into the stable public
    error code `ACTION_NOT_ALLOWED`.

    Anonymous callers never reach this class: the JWT auth declared on the
    route answers 401 `AUTHENTICATION_REQUIRED` first (auth runs before the
    permission check).
    """

    def has_permission(self, request: HttpRequest, controller: Any) -> bool:
        user = getattr(request, "user", None) or getattr(request, "auth", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(
            getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)
        )


__all__ = ["SystemPermissions", "RequireAdmin"]
