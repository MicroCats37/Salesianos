"""
Ownership authorization for the salesianos_fest HTTP layer.

Shared by every controller that reads or mutates the resources of an
inscripcion, so the rule is stated once and cannot drift between endpoints.

Rule (same for pool, roster, participaciones, equipos and cupos):
- The responsable of the inscripcion may act on it.
- A Django admin (`is_staff` / `is_superuser`) may act on any inscripcion.
- Everybody else gets 403 Forbidden.

The check is HTTP-level: it reads the authenticated request and raises
`ForbiddenError`. It never mutates state and never leaks internal ids in the
public message — the exception handler owns the public wording.

Resources that do not carry an `inscripcion_id` of their own (equipo,
participacion, asignacion) are resolved to their parent inscripcion first, so
the same rule applies to them without duplicating the query logic per
endpoint.
"""
from asgiref.sync import sync_to_async

from core.capacidades import es_admin
from core.exceptions import ForbiddenError


def _is_admin(user) -> bool:
    """Return True when the actor is a Django admin (is_staff or is_superuser).

    The rule is NOT re-implemented here: it is delegated to
    `core.capacidades`, the single map of the project.
    """
    return es_admin(user)


async def check_ownership_or_admin(request, inscripcion_id: str) -> None:
    """Verify the authenticated user can mutate this inscripcion.

    Allowed actors:
    - The responsable of the inscripcion (persona matches the authenticated user)
    - Any Django admin user (is_staff or is_superuser)

    Raises:
        ForbiddenError (403): if the user is neither responsible nor admin.
    """
    user = request.user

    # Admins can do anything.
    if _is_admin(user):
        return

    persona_id = getattr(user, "persona_fk_id", None)
    if not persona_id:
        raise ForbiddenError()

    def _check() -> None:
        from modules.salesianos_fest.domain.models import Inscripcion

        try:
            inscripcion = Inscripcion.objects.only("responsable_id").get(id=inscripcion_id)
        except Inscripcion.DoesNotExist:
            # The endpoint owns the "not found" answer — do not mask it here.
            return
        if str(inscripcion.responsable_id) != str(persona_id):
            raise ForbiddenError()

    await sync_to_async(_check, thread_sensitive=True)()


async def _resolve_inscripcion_id_for_equipo(equipo_id: str) -> str | None:
    """Return the inscripcion that owns the equipo, or None when it does not exist."""

    def _query() -> str | None:
        from modules.salesianos_fest.domain.models import Equipo

        equipo = Equipo.objects.only("inscripcion_id").filter(id=equipo_id).first()
        return str(equipo.inscripcion_id) if equipo else None

    return await sync_to_async(_query, thread_sensitive=True)()


async def _resolve_inscripcion_id_for_participacion(participacion_id: str) -> str | None:
    """Return the inscripcion that owns the participacion, or None when missing."""

    def _query() -> str | None:
        from modules.salesianos_fest.domain.models import Participacion

        participacion = (
            Participacion.objects.select_related("inscripcion_persona")
            .only("inscripcion_persona__inscripcion_id")
            .filter(id=participacion_id)
            .first()
        )
        if not participacion:
            return None
        return str(participacion.inscripcion_persona.inscripcion_id)

    return await sync_to_async(_query, thread_sensitive=True)()


async def _resolve_inscripcion_id_for_asignacion(asignacion_id: str) -> str | None:
    """Return the inscripcion that owns the asignacion, or None when missing."""

    def _query() -> str | None:
        from modules.salesianos_fest.domain.models import AsignacionCupo

        asignacion = (
            AsignacionCupo.objects.only("inscripcion_id")
            .filter(id=asignacion_id)
            .first()
        )
        return str(asignacion.inscripcion_id) if asignacion else None

    return await sync_to_async(_query, thread_sensitive=True)()


async def check_ownership_or_admin_for_equipo(request, equipo_id: str) -> None:
    """Verify the authenticated user can read/act on this equipo.

    The equipo inherits the ownership of its inscripcion.

    Raises:
        ForbiddenError (403): if the user is neither responsible nor admin.
    """
    inscripcion_id = await _resolve_inscripcion_id_for_equipo(equipo_id)
    if inscripcion_id is None:
        # The endpoint owns the "not found" answer — do not mask it here.
        return
    await check_ownership_or_admin(request, inscripcion_id)


async def check_ownership_or_admin_for_participacion(
    request, participacion_id: str
) -> None:
    """Verify the authenticated user can read/act on this participacion.

    The participacion inherits the ownership of the inscripcion of its
    `inscripcion_persona`.

    Raises:
        ForbiddenError (403): if the user is neither responsible nor admin.
    """
    inscripcion_id = await _resolve_inscripcion_id_for_participacion(participacion_id)
    if inscripcion_id is None:
        # The endpoint owns the "not found" answer — do not mask it here.
        return
    await check_ownership_or_admin(request, inscripcion_id)


async def check_ownership_or_admin_for_asignacion(request, asignacion_id: str) -> None:
    """Verify the authenticated user can read/act on this asignacion de cupo.

    The asignacion inherits the ownership of its inscripcion.

    Raises:
        ForbiddenError (403): if the user is neither responsible nor admin.
    """
    inscripcion_id = await _resolve_inscripcion_id_for_asignacion(asignacion_id)
    if inscripcion_id is None:
        # The endpoint owns the "not found" answer — do not mask it here.
        return
    await check_ownership_or_admin(request, inscripcion_id)


async def check_acreditacion_access_or_admin(request, persona_id: str) -> None:
    """Verify the authenticated user can read the accreditation of a persona.

    An acreditacion belongs to a PERSONA (one row per event/person), not to an
    inscription, so the owner of the record is the accredited person itself.

    Allowed actors:
    - The accredited person (the authenticated user's persona matches).
    - Any Django admin user (is_staff or is_superuser).

    The live QR credential is NEVER returned by this endpoint; it is delivered
    only by the explicit, admin-only QR generation action.

    Raises:
        ForbiddenError (403): if the user is neither the accredited person nor
            an admin.
    """
    user = request.user

    if _is_admin(user):
        return

    persona_fk_id = getattr(user, "persona_fk_id", None)
    if not persona_fk_id or str(persona_fk_id) != str(persona_id):
        raise ForbiddenError()
