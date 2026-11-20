"""El adaptador de `VerificarDerecho` del módulo de PASES.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §5

Este adaptador es el PRODUCTOR de la interfaz `VerificarDerecho` para los
derechos de ENTRADA (`PaseBeneficiario`): el pase comprado y la entrada de
cortesía.

**LA REGLA ES DE AQUÍ.** `validaciones` NO reimplanta estas reglas: este
archivo vive en el módulo DUEÑO y por eso es el único que puede decir si un
derecho de entrada se puede canjear y por qué (`FR-05` §1).

Las reglas que aplica, todas CONGELADAS:

- un derecho `REVOCADO` no se puede canjear (`RN-P08`);
- una compra `PENDIENTE` NO habilita ningún derecho (`RN-P02`);
- no se consume más unidades de las concedidas (`RN-P07`);
- la revocación es permanente: la unidad no vuelve al lote (`FR-05` §2.3).

El contador `cantidad_consumida` lo escribe ESTE módulo: el derecho es del
dueño y su contador también (`D-DOM03-07`).
"""

from django.db import transaction

from modules.salesianos_fest.domain.constants import (
    EstadoCompraPase,
    EstadoDerechoPase,
)
from modules.salesianos_fest.domain.models import PaseBeneficiario
from modules.validaciones.domain.constants import TipoDerechoChoices
from modules.validaciones.domain.exceptions import (
    CantidadExcedidaError,
    DerechoRevocadoError,
    TicketNoEncontradoError,
    TicketYaConsumidoError,
)
from modules.validaciones.domain.ports.verificador_derecho import (
    IVerificadorDerecho,
    TitularDerecho,
    VerificacionDerecho,
)

#: Los motivos públicos y SEGUROS por los que un derecho no se canjea.
MOTIVO_DERECHO_REVOCADO = "El derecho de entrada está revocado."
MOTIVO_COMPRA_NO_PAGADA = "La compra del pase todavía no está pagada."
MOTIVO_YA_CONSUMIDO = "El derecho de entrada ya se canjeó por completo."


class PaseVerificadorDerecho(IVerificadorDerecho):
    """El dueño de los derechos de ENTRADA."""

    tipo_derecho = TipoDerechoChoices.PASE

    # ── LECTURA ───────────────────────────────────────────────────────────────

    def resolver(self, referencia_id: str) -> VerificacionDerecho:
        """Publica el estado del derecho SIN tocarlo (`RN-P06`)."""
        return self._verificacion(self._derecho(referencia_id))

    # ── MUTACIÓN ──────────────────────────────────────────────────────────────

    def consumir(
        self,
        referencia_id: str,
        cantidad: int | None = None,
        actor_usuario_id: str | None = None,
    ) -> VerificacionDerecho:
        """Revalida BAJO BLOQUEO y consume el derecho.

        `cantidad=None` significa "todo lo disponible". `cantidad` mayor que
        lo disponible es un EXCESO (`FR-05` §2.2): no se consume parcialmente
        sin que el operador lo pida explícitamente.
        """
        with transaction.atomic():
            derecho = self._derecho(referencia_id, bloquear=True)
            self._revalidar(derecho, cantidad)
            derecho.cantidad_consumida += self._cantidad_a_consumir(
                derecho, cantidad
            )
            derecho.save(update_fields=["cantidad_consumida", "updated_at"])
        return self._verificacion(derecho)

    # ── Internos ──────────────────────────────────────────────────────────────

    @staticmethod
    def _derecho(referencia_id: str, bloquear: bool = False) -> PaseBeneficiario:
        """El derecho del módulo dueño, con su titular y su pase."""
        consulta = PaseBeneficiario.objects.select_related(
            "persona",
            "pase",
            "compra_pase",
        )
        if bloquear:
            consulta = consulta.select_for_update()
        derecho = consulta.filter(id=referencia_id).first()
        if derecho is None:
            raise TicketNoEncontradoError()
        return derecho

    @staticmethod
    def _cantidad_a_consumir(
        derecho: PaseBeneficiario, cantidad: int | None
    ) -> int:
        """Cuántas unidades se consumen, o el EXCESO como error."""
        disponible = derecho.cantidad - derecho.cantidad_consumida
        if disponible <= 0:
            raise TicketYaConsumidoError()
        if cantidad is None:
            return disponible
        if cantidad > disponible:
            raise CantidadExcedidaError()
        return cantidad

    @staticmethod
    def _revalidar(derecho: PaseBeneficiario, cantidad: int | None) -> None:
        """La regla del dueño, en el instante de la confirmación."""
        if derecho.estado != EstadoDerechoPase.ACTIVO:
            raise DerechoRevocadoError()
        if (
            derecho.compra_pase_id
            and derecho.compra_pase.estado != EstadoCompraPase.PAGADA
        ):
            # Una compra PENDIENTE no habilita ningún derecho (`RN-P02`).
            raise DerechoRevocadoError()
        PaseVerificadorDerecho._cantidad_a_consumir(derecho, cantidad)

    @staticmethod
    def _verificacion(derecho: PaseBeneficiario) -> VerificacionDerecho:
        """La publicación del dueño sobre su derecho."""
        disponible = max(0, derecho.cantidad - derecho.cantidad_consumida)
        puede_canjear, motivo_codigo, motivo_mensaje = PaseVerificadorDerecho._motivo(
            derecho, disponible
        )
        return VerificacionDerecho(
            tipo_derecho=TipoDerechoChoices.PASE,
            codigo=derecho.pase.slug,
            titular=TitularDerecho(
                persona_id=str(derecho.persona_id),
                nombre=_nombre_completo(derecho.persona),
            ),
            edicion_id=str(derecho.edicion_id),
            estado=derecho.estado,
            cantidad_total=derecho.cantidad,
            cantidad_consumida=derecho.cantidad_consumida,
            cantidad_disponible=disponible,
            puede_canjear=puede_canjear,
            motivo_codigo=motivo_codigo,
            motivo_mensaje=motivo_mensaje,
        )

    @staticmethod
    def _motivo(derecho: PaseBeneficiario, disponible: int):
        """Si el derecho se puede canjear, y por qué no."""
        if derecho.estado != EstadoDerechoPase.ACTIVO:
            return (
                False,
                "DERECHO_REVOCADO",
                MOTIVO_DERECHO_REVOCADO,
            )
        if (
            derecho.compra_pase_id
            and derecho.compra_pase.estado != EstadoCompraPase.PAGADA
        ):
            return (
                False,
                "COMPRA_NO_PAGADA",
                MOTIVO_COMPRA_NO_PAGADA,
            )
        if disponible <= 0:
            return (
                False,
                "TICKET_YA_CONSUMIDO",
                MOTIVO_YA_CONSUMIDO,
            )
        return (True, None, None)


def _nombre_completo(persona) -> str:
    """El nombre de la persona, como lo publica su módulo."""
    partes = [persona.nombres or "", persona.apellidos or ""]
    return " ".join(parte for parte in partes if parte).strip()


__all__ = [
    "MOTIVO_COMPRA_NO_PAGADA",
    "MOTIVO_DERECHO_REVOCADO",
    "MOTIVO_YA_CONSUMIDO",
    "PaseVerificadorDerecho",
]
