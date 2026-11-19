"""`ActivacionCompraCoreService` — persistencia de la activación de derechos.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.1 I-2)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`
Contract: `contract/django-app-architecture-contract.md` §4.3

Servicio **sync** que opera sobre el ORM. No abre `transaction.atomic()`: el
coordinador (el caller) provee las transacciones compuestas.

**No hay capa de repositorio**: el ORM de Django es la abstracción de
persistencia (contract §9).
"""

from datetime import timedelta

from django.db.models import F, Q
from django.utils import timezone

from modules.commerce.domain.constants import (
    LEGA_ACTIVACION_SEGUNDOS,
    EstadoActivacionCompra,
)
from modules.commerce.domain.models import ActivacionCompra, Compra


class ActivacionCompraCoreService:
    """Operaciones de persistencia de la activación de una compra."""

    def obtener_compra_por_orden(self, orden_pago_id: str) -> Compra | None:
        """La compra que financia la orden, si existe.

        Args:
            orden_pago_id: UUID de la `OrdenPago`.

        Returns:
            La `Compra` o `None`.
        """
        if not orden_pago_id:
            return None
        return Compra.objects.filter(orden_pago_id=orden_pago_id).first()

    def obtener_activacion(self, compra_id, origen: str) -> ActivacionCompra | None:
        """La activación de `(compra, origen)`, si ya existe."""
        return ActivacionCompra.objects.filter(
            compra_id=compra_id,
            origen=origen,
        ).first()

    def crear_activacion(
        self,
        compra: Compra,
        origen: str,
        clave: str,
    ) -> ActivacionCompra:
        """Crea el registro de activación.

        Puede lanzar `IntegrityError` si otra vuelta ganó la carrera: la
        guarda real es la restricción única de la base de datos, no esta
        comprobación (aprendizaje #6 de FND-04).
        """
        return ActivacionCompra.objects.create(
            compra=compra,
            origen=origen,
            clave=clave,
            estado=EstadoActivacionCompra.PENDIENTE,
        )

    def reclamar(self, activacion_id) -> bool:
        """Reserva el intento de activación. Devuelve `True` si lo obtiene.

        Es un **UPDATE condicional**: una sola sentencia que hace de
        compare-and-swap. Sólo puede ganar quien deja la fila en un estado
        reclamable, de modo que dos reintentos concurrentes no despachan dos
        veces (FR-04 I-2).

        La fila es reclamable cuando:
        - no hay ningún intento reservado (`en_curso=False`), o
        - el intento reservado venció su lease: el proceso que lo reservó
          murió y la activación quedaría bloqueada para siempre.
        """
        ahora = timezone.now()
        limite = ahora - timedelta(seconds=LEGA_ACTIVACION_SEGUNDOS)

        actualizado = (
            ActivacionCompra.objects.filter(id=activacion_id)
            .filter(
                estado__in=[
                    EstadoActivacionCompra.PENDIENTE,
                    EstadoActivacionCompra.FALLIDA,
                ]
            )
            .filter(
                Q(en_curso=False)
                | Q(en_curso=True, ultimo_intento_en__isnull=True)
                | Q(en_curso=True, ultimo_intento_en__lte=limite)
            )
            .update(
                en_curso=True,
                intentos=F("intentos") + 1,
                ultimo_intento_en=ahora,
                updated_at=ahora,
            )
        )
        return actualizado == 1

    def liberar(self, activacion_id) -> None:
        """Libera el intento reservado sin cerrar la activación.

        Se usa cuando el dominio de origen todavía no puede activar (su
        activador no está registrado): la activación sigue `PENDIENTE` y
        reintentable, y el cobro confirmado se conserva (RN-C08).
        """
        ActivacionCompra.objects.filter(id=activacion_id).update(
            en_curso=False,
            updated_at=timezone.now(),
        )

    def marcar_activada(self, activacion_id, detalle: dict) -> None:
        """Cierra la activación como `ACTIVADA`. Es terminal."""
        ActivacionCompra.objects.filter(id=activacion_id).update(
            estado=EstadoActivacionCompra.ACTIVADA,
            en_curso=False,
            activada_en=timezone.now(),
            incidencia={},
            detalle=detalle or {},
            updated_at=timezone.now(),
        )

    def marcar_fallida(self, activacion_id, incidencia: dict) -> None:
        """Cierra el intento como `FALLIDA`, con la incidencia segura.

        La activación queda **reintentable** y el pago confirmado se conserva
        (RN-C08, FR-04 §4).
        """
        ActivacionCompra.objects.filter(id=activacion_id).update(
            estado=EstadoActivacionCompra.FALLIDA,
            en_curso=False,
            incidencia=incidencia or {},
            updated_at=timezone.now(),
        )


__all__ = ["ActivacionCompraCoreService"]
