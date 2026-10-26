"""
AdminAcreditacionSelector — read queries of the accreditations and of the
access log (A10, A11, A12).

`AcreditacionEvento.codigo_qr` is a LIVE BEARER CREDENTIAL — the token the QR
scanner submits to `POST /api/acceso/registrar`. It is NEVER read by this
selector and NEVER travels in an administrative payload: the surface reports
the operational state of the credential, never the credential itself
(`contract/api-wrapper-presenter-contract.md` §9).

Read-only by construction: no method in this selector writes.
"""
from datetime import date

from django.db.models import Count, Max, Q

from modules.administracion.domain.exceptions import AdminResourceNotFoundError
from modules.administracion.domain.results.admin_acreditacion_results import (
    AdminAccesoListItemResult,
    AdminAcreditacionDetalleResult,
    AdminAcreditacionListItemResult,
)
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)
from modules.salesianos_fest.domain.constants import ResultadoAccesoChoices
from modules.salesianos_fest.domain.models import AcreditacionEvento, ControlAcceso


def _nombre_completo(nombres: str, apellidos: str) -> str:
    """Return the display name of a person."""
    return f"{nombres} {apellidos}".strip()


class AdminAcreditacionSelector:
    """Read-only queries for the accreditations of an event."""

    # ── Accreditations (A10) ───────────────────────────────────────────────

    def listar(
        self,
        evento_id: str,
        *,
        estado: str | None = None,
        autorizacion_fiesta: str | None = None,
        acceso_fiesta: bool | None = None,
        q: str | None = None,
        params: AdminPaginacionParams,
    ) -> tuple[list[AdminAcreditacionListItemResult], int]:
        """Return the page of accreditations and the total of matching rows.

        Args:
            evento_id: the ACTIVE event (resolved server-side).
            estado: filter by the accreditation state.
            autorizacion_fiesta: filter by the authorization origin.
            acceso_fiesta: filter by the fiesta access flag.
            q: free text over the person (name, document).
            params: the normalized pagination parameters.

        Returns:
            `(items, total)`.
        """
        qs = (
            AcreditacionEvento.objects
            .filter(evento_id=evento_id)
            .select_related("persona")
        )

        if estado:
            qs = qs.filter(estado=estado)

        if autorizacion_fiesta:
            qs = qs.filter(autorizacion_fiesta=autorizacion_fiesta)

        if acceso_fiesta is not None:
            qs = qs.filter(acceso_fiesta=acceso_fiesta)

        if q:
            qs = qs.filter(
                Q(persona__nombres__icontains=q)
                | Q(persona__apellidos__icontains=q)
                | Q(persona__numero_documento__icontains=q)
            )

        qs = qs.order_by(params.ordering)

        total = qs.count()
        filas = list(qs[params.offset: params.offset + params.page_size])

        accesos = self._accesos_por_acreditacion([fila.id for fila in filas])

        items: list[AdminAcreditacionListItemResult] = []
        for fila in filas:
            permitidos, ultimo = accesos.get(str(fila.id), (0, None))
            items.append(
                AdminAcreditacionListItemResult(
                    id=str(fila.id),
                    persona_id=str(fila.persona_id),
                    persona_nombre=_nombre_completo(
                        fila.persona.nombres, fila.persona.apellidos
                    ),
                    persona_documento=fila.persona.numero_documento,
                    estado=fila.estado,
                    acceso_fiesta=fila.acceso_fiesta,
                    acceso_box=fila.acceso_box,
                    autorizacion_fiesta=fila.autorizacion_fiesta,
                    habilitado=fila.habilitado,
                    observacion=fila.observacion,
                    accesos_permitidos=permitidos,
                    ultimo_acceso=ultimo,
                )
            )

        return items, total

    # ── Accreditation detail (A11) ────────────────────────────────────────

    def obtener_detalle(
        self,
        evento_id: str,
        acreditacion_id: str,
    ) -> AdminAcreditacionDetalleResult:
        """Return the drilldown of one accreditation.

        Raises:
            AdminResourceNotFoundError: when the accreditation does not exist
                or does not belong to the active event.
        """
        fila = (
            AcreditacionEvento.objects
            .filter(id=acreditacion_id, evento_id=evento_id)
            .select_related("persona")
            .first()
        )

        if fila is None:
            raise AdminResourceNotFoundError("Acreditación")

        permitidos, ultimo = self._accesos_por_acreditacion([fila.id]).get(
            str(fila.id),
            (0, None),
        )

        return AdminAcreditacionDetalleResult(
            id=str(fila.id),
            persona_id=str(fila.persona_id),
            persona_nombre=_nombre_completo(
                fila.persona.nombres, fila.persona.apellidos
            ),
            persona_documento=fila.persona.numero_documento,
            estado=fila.estado,
            acceso_fiesta=fila.acceso_fiesta,
            acceso_box=fila.acceso_box,
            autorizacion_fiesta=fila.autorizacion_fiesta,
            habilitado=fila.habilitado,
            observacion=fila.observacion,
            accesos_permitidos=permitidos,
            ultimo_acceso=ultimo,
            accesos=self._accesos_de_acreditacion(str(fila.id)),
        )

    # ── Access log (A12) ──────────────────────────────────────────────────

    def listar_accesos(
        self,
        evento_id: str,
        *,
        resultado: str | None = None,
        punto_acceso: str | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        q: str | None = None,
        params: AdminPaginacionParams,
    ) -> tuple[list[AdminAccesoListItemResult], int]:
        """Return the page of access records and the total of matching rows.

        Args:
            evento_id: the ACTIVE event (resolved server-side).
            resultado: filter by PERMITIDO / DENEGADO.
            punto_acceso: filter by the scanner location.
            desde: only records at or after this date.
            hasta: only records at or before this date.
            q: free text over the person (name, document).
            params: the normalized pagination parameters.

        Returns:
            `(items, total)`.
        """
        qs = (
            ControlAcceso.objects
            .filter(acreditacion__evento_id=evento_id)
            .select_related("acreditacion__persona", "operador__persona_fk")
        )

        if resultado:
            qs = qs.filter(resultado=resultado)

        if punto_acceso:
            qs = qs.filter(punto_acceso=punto_acceso)

        if desde is not None:
            qs = qs.filter(fecha_hora__date__gte=desde)

        if hasta is not None:
            qs = qs.filter(fecha_hora__date__lte=hasta)

        if q:
            qs = qs.filter(
                Q(acreditacion__persona__nombres__icontains=q)
                | Q(acreditacion__persona__apellidos__icontains=q)
                | Q(acreditacion__persona__numero_documento__icontains=q)
            )

        qs = qs.order_by(params.ordering)

        total = qs.count()
        filas = list(qs[params.offset: params.offset + params.page_size])

        return [self._map_acceso(fila) for fila in filas], total

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _accesos_por_acreditacion(acreditacion_ids: list) -> dict[str, tuple[int, object]]:
        """Return `(permitidos, ultimo_acceso)` of every accreditation."""
        if not acreditacion_ids:
            return {}

        filas = (
            ControlAcceso.objects
            .filter(acreditacion_id__in=acreditacion_ids)
            .values("acreditacion_id")
            .annotate(
                permitidos=Count(
                    "id",
                    filter=Q(resultado=ResultadoAccesoChoices.PERMITIDO),
                ),
                ultimo=Max("fecha_hora"),
            )
        )

        return {
            str(fila["acreditacion_id"]): (fila["permitidos"], fila["ultimo"])
            for fila in filas
        }

    def _accesos_de_acreditacion(self, acreditacion_id: str) -> list[AdminAccesoListItemResult]:
        """Return the access records of one accreditation."""
        filas = (
            ControlAcceso.objects
            .filter(acreditacion_id=acreditacion_id)
            .select_related("acreditacion__persona", "operador__persona_fk")
            .order_by("-fecha_hora")
        )
        return [self._map_acceso(fila) for fila in filas]

    @staticmethod
    def _map_acceso(fila: ControlAcceso) -> AdminAccesoListItemResult:
        """Map an access record into its result DTO."""
        persona = fila.acreditacion.persona
        operador = fila.operador

        return AdminAccesoListItemResult(
            id=str(fila.id),
            acreditacion_id=str(fila.acreditacion_id),
            persona_nombre=_nombre_completo(persona.nombres, persona.apellidos),
            persona_documento=persona.numero_documento,
            resultado=fila.resultado,
            punto_acceso=fila.punto_acceso,
            operador_nombre=(
                _nombre_completo(
                    operador.persona_fk.nombres,
                    operador.persona_fk.apellidos,
                )
                if operador and operador.persona_fk
                else None
            ),
            fecha_hora=fila.fecha_hora,
        )


__all__ = ["AdminAcreditacionSelector"]
