"""Permission classes shared by the HTTP layer.

`SystemPermissions` is the generic registry kept for compatibility with the
existing `CheckPermission` helper in `core/security.py`.

`RequireAdmin` is the admin-only gate used by the operational administration
surface and by the hardened FEST endpoints. It delegates to
`core.capacidades.es_admin`, the single place where the rule lives:

    admin = is_staff OR is_superuser

`RequireCapability` is the granular gate: it asks the SAME map for one
capability, so the area can express "this action needs the break-glass tier"
without a second source of truth.

No parallel role model, group table or RBAC system is introduced
(`contract/django-app-architecture-contract.md` §10 — "Permisos centralizados").
The Django flags (`is_staff`, `is_superuser`) remain the only source of truth
and no migration is required.

Contract: `contract/api-wrapper-presenter-contract.md` §8 — the public message
of a denial comes from the global error catalog in `core/exceptions.py`, never
from the permission class.
"""
from typing import Any

from django.http import HttpRequest
from ninja_extra.permissions import BasePermission

from core.capacidades import (
    CAP_ACREDITACIONES_ESCRIBIR,
    CAP_ADMIN_VER,
    CAP_COMPETENCIAS_ESCRIBIR,
    CAP_EQUIPOS_ESCRIBIR,
    CAP_INSCRIPCIONES_ESCRIBIR,
    CAP_PAGOS_APROBAR,
    CAP_PAGOS_VER,
    CAP_USUARIOS_GESTIONAR,
    CAP_USUARIOS_PROMOVER_SUPERUSUARIO,
    CAP_USUARIOS_VER,
    es_admin,
    tiene_capacidad,
)


class SystemPermissions:
    """Generic permission registry."""

    @classmethod
    def all(cls) -> list:
        return []


def _actor(request: HttpRequest):
    """Return the authenticated actor of the request, or None."""
    user = getattr(request, "user", None) or getattr(request, "auth", None)
    if not user or not getattr(user, "is_authenticated", False):
        return None
    return user


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
        actor = _actor(request)
        if actor is None:
            return False
        return es_admin(actor)


class RequireCapability(BasePermission):
    """Allows access only to the actors that hold one capability.

    The capability is resolved by `core.capacidades`, the single map of the
    project. A superuser ALWAYS resolves the complete set, so this gate is
    never narrower than the automatic Django bypass.

    The capability is declared in two stable ways:

    - as a CONCRETE subclass (`permissions=[RequirePagosAprobar]`), which is
      what the routes use: Ninja-Extra instantiates the class and the
      capability travels in the class attribute;
    - as an INSTANCE with an explicit code
      (`permissions=[RequireCapability(CAP_PAGOS_APROBAR)]`), for the cases
      where the code is computed.

    A route-level `permissions` list REPLACES the one of the controller, so a
    sensitive route must declare EVERY gate it needs.
    """

    #: Capability code required by the gate.
    codigo: str = ""

    def __init__(self, codigo: str | None = None):
        if codigo is not None:
            self.codigo = codigo

    def has_permission(self, request: HttpRequest, controller: Any) -> bool:
        actor = _actor(request)
        if actor is None:
            return False
        if not self.codigo:
            return False
        return tiene_capacidad(actor, self.codigo)


# ── Gates concretos ───────────────────────────────────────────────────────────
#
# Clases estables: el nombre de la clase ES la capability, de modo que la
# ruta declare la exigencia sin repetir la cadena de texto.


class RequireAdminVer(RequireCapability):
    """Read the whole administration area."""

    codigo = CAP_ADMIN_VER


class RequireInscripcionesEscribir(RequireCapability):
    """Mutate the registrations and their roster."""

    codigo = CAP_INSCRIPCIONES_ESCRIBIR


class RequireEquiposEscribir(RequireCapability):
    """Manage the team templates."""

    codigo = CAP_EQUIPOS_ESCRIBIR


class RequireCompetenciasEscribir(RequireCapability):
    """Manage the competitions, the bracket and the encounters."""

    codigo = CAP_COMPETENCIAS_ESCRIBIR


class RequireAcreditacionesEscribir(RequireCapability):
    """Manage the accreditations and the access control."""

    codigo = CAP_ACREDITACIONES_ESCRIBIR


class RequirePagosVer(RequireCapability):
    """Read the payments."""

    codigo = CAP_PAGOS_VER


class RequirePagosAprobar(RequireCapability):
    """Approve or annul a payment received outside the provider.

    Sensitive action: only the break-glass tier holds it.
    """

    codigo = CAP_PAGOS_APROBAR


class RequireUsuariosVer(RequireCapability):
    """Read the accounts table."""

    codigo = CAP_USUARIOS_VER


class RequireUsuariosGestionar(RequireCapability):
    """Activate, deactivate, promote or demote an account."""

    codigo = CAP_USUARIOS_GESTIONAR


class RequirePromoverSuperusuario(RequireCapability):
    """Grant or revoke the break-glass tier."""

    codigo = CAP_USUARIOS_PROMOVER_SUPERUSUARIO


__all__ = [
    "SystemPermissions",
    "RequireAdmin",
    "RequireCapability",
    "RequireAdminVer",
    "RequireInscripcionesEscribir",
    "RequireEquiposEscribir",
    "RequireCompetenciasEscribir",
    "RequireAcreditacionesEscribir",
    "RequirePagosVer",
    "RequirePagosAprobar",
    "RequireUsuariosVer",
    "RequireUsuariosGestionar",
    "RequirePromoverSuperusuario",
]
