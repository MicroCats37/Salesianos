"""`emitir_ticket` — emite una credencial de control de acceso.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §1

La credencial (`Ticket`) REFERENCIA un derecho que ya existe en su módulo
dueño. Este comando es el camino de EMISIÓN del paquete `XCT-01`: resuelve
la referencia, deriva el tipo de derecho y la operación, y guarda el
código.

**POR QUÉ ES UN COMANDO Y NO UN EVENTO.** La emisión automática al otorgar
el derecho tocaría los flujos de `salesianos_fest` y `marketplace`, que son
raíces ajenas a este paquete (`00-contrato-global-de-apply.md`, "Forbidden
Edit Roots"). La decisión de automatizarla se pide a A0 como
`A0-XCT01-04`.

**EL CÓDIGO ES UN SECRETO.** Si no se declara `--codigo`, el comando genera
uno impredecible y lo muestra UNA vez por stdout: no se publica en ningún
listado ni se registra en la auditoría.
"""

import secrets

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.validaciones.domain.constants import (
    OPERACION_POR_TIPO_DERECHO,
    TipoDerechoChoices,
)
from modules.validaciones.domain.models import Ticket

#: Los bytes de entropía del código generado.
BYTES_CODIGO = 12

#: El prefijo legible del código generado.
PREFIJO_CODIGO = "FEST"


class Command(BaseCommand):
    """Emite una credencial para un derecho existente."""

    help = "Emite una credencial de control de acceso para un derecho existente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tipo",
            required=True,
            choices=[tipo.value for tipo in TipoDerechoChoices],
            help="El tipo de derecho al que apunta la credencial.",
        )
        parser.add_argument(
            "--referencia",
            required=True,
            help="El identificador del derecho: un beneficiario de pase o un pedido.",
        )
        parser.add_argument(
            "--codigo",
            default=None,
            help="El código de la credencial. Si no se declara, se genera uno.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tipo = options["tipo"]
        referencia = options["referencia"]
        codigo = options["codigo"] or self._generar_codigo()

        ticket = self._emitir(tipo, referencia, codigo)

        self.stdout.write(
            self.style.SUCCESS(
                f"Credencial emitida para {ticket.tipo_derecho} "
                f"({ticket.operacion})."
            )
        )
        # El código se muestra UNA vez: es un secreto.
        self.stdout.write(str(ticket.codigo))

    # ── Internos ──────────────────────────────────────────────────────────────

    @staticmethod
    def _generar_codigo() -> str:
        """Un código impredecible. No se deriva del derecho."""
        return f"{PREFIJO_CODIGO}-{secrets.token_urlsafe(BYTES_CODIGO)}"

    def _emitir(self, tipo: str, referencia: str, codigo: str) -> Ticket:
        """La credencial que referencia ese derecho."""
        if tipo == TipoDerechoChoices.PRODUCTO:
            return self._emitir_producto(referencia, codigo)
        return self._emitir_pase(referencia, codigo)

    @staticmethod
    def _emitir_pase(referencia: str, codigo: str) -> Ticket:
        """La credencial de un derecho de ENTRADA."""
        from modules.salesianos_fest.domain.constants import OrigenDerechoPase
        from modules.salesianos_fest.domain.models import PaseBeneficiario

        derecho = PaseBeneficiario.objects.filter(id=referencia).first()
        if derecho is None:
            raise CommandError("No existe el derecho de pase indicado.")

        tipo = (
            TipoDerechoChoices.ENTRADA_CORTESIA
            if derecho.origen == OrigenDerechoPase.CORTESIA
            else TipoDerechoChoices.PASE
        )
        return Ticket.objects.create(
            codigo=codigo,
            edicion_id=derecho.edicion_id,
            tipo_derecho=tipo,
            operacion=OPERACION_POR_TIPO_DERECHO[tipo],
            pase_beneficiario=derecho,
        )

    @staticmethod
    def _emitir_producto(referencia: str, codigo: str) -> Ticket:
        """La credencial de un pedido que se tiene que entregar."""
        from modules.marketplace.domain.models import Pedido

        pedido = Pedido.objects.filter(id=referencia).first()
        if pedido is None:
            raise CommandError("No existe el pedido indicado.")

        return Ticket.objects.create(
            codigo=codigo,
            edicion_id=pedido.edicion_id,
            tipo_derecho=TipoDerechoChoices.PRODUCTO,
            operacion=OPERACION_POR_TIPO_DERECHO[TipoDerechoChoices.PRODUCTO],
            pedido=pedido,
        )


__all__ = ["BYTES_CODIGO", "PREFIJO_CODIGO", "Command"]
