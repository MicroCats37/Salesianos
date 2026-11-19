"""`CoordinadorActivacionCompra` — la activación de derechos, exactamente una vez.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.1 I-2, §2.3, §4; RN-C06, RN-C08)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`
Contract: `contract/django-app-architecture-contract.md` §4.3

Este es el **coordinador** de la secuencia congelada de `FR-04` §2.3:

    PagoVerificado(orden_id, evidencia)      # lo hace `pagos`
    CompraMarcadaPagada(compra_id)           # lo hace `pagos`
    ActivarDominio(compra_id, origen)         # lo hace este coordinador
    NotificarComprador(compra_id)            # opcional, reintentable

Qué sabe y qué no sabe:

- **Sabe**: que hay que activar un origen, con qué clave y con qué snapshot
  congelado. **No sabe** qué es un cupo, un pase o una salida de stock: esas
  reglas son de los dominios (`RN-C01`, `funcional/01` §1).
- **Sabe**: que un pago confirmado y la entrega del derecho son hechos
  **separados** (RN-C08). Si la activación falla, el pago confirmado se
  conserva y queda una incidencia recuperable.

Las cuatro garantías:

| # | Garantía | Mecanismo |
|---|---|---|
| 1 | Un pago implica **como máximo una** activación efectiva por `(compra, origen)` | una fila de activación por par (restricción única en base de datos) + `estado=ACTIVADA` terminal + reserva condicional del intento |
| 2 | El reintento **converge** | la clave de activación es ESTABLE y el dominio deduplica por ella |
| 3 | El fallo del dominio **no revierte el pago** | el coordinador nunca toca `Compra.estado` ni `OrdenPago.estado` |
| 4 | El fallo es **visible y reintentable** | `incidencia` con datos seguros + `proxima_accion` en el resultado |

**Transacciones.** Este servicio es sync y no abre `transaction.atomic()`: cada
escritura es una sola sentencia (un `INSERT`, un `UPDATE` condicional) y por
eso ya es atómica. El `UPDATE` de reserva es el compare-and-swap que evita
que dos reintentos concurrentes despachen dos veces.
"""

import logging
import re

from django.utils import timezone
from injector import inject

from modules.commerce.domain.constants import (
    CLAVES_DETALLE_PERMITIDAS,
    EstadoActivacionCompra,
    EstadoCompra,
)
from modules.commerce.domain.models import ActivacionCompra, Compra
from modules.commerce.domain.schemas.compra_schemas import (
    ContextoActivacionCompra,
    ResultadoActivacionCompra,
)
from modules.commerce.domain.services.core.activacion_compra_core_service import (
    ActivacionCompraCoreService,
)
from modules.commerce.domain.services.core.registro_activadores_compra import (
    RegistroActivadoresCompra,
)

logger = logging.getLogger(__name__)

#: Un código de máquina SEGURO: mayúsculas, dígitos y guiones bajos.
CODIGO_SEGURO = re.compile(r"^[A-Z0-9_]{1,64}$")

#: Códigos del resultado de la activación. Son públicos y estables.
CODIGO_SIN_COMPRA = "SIN_COMPRA"
CODIGO_COMPRA_NO_PAGADA = "COMPRA_NO_PAGADA"
CODIGO_ACTIVACION_COMPLETADA = "ACTIVACION_COMPLETADA"
CODIGO_ACTIVACION_YA_COMPLETADA = "ACTIVACION_YA_COMPLETADA"
CODIGO_ACTIVACION_EN_CURSO = "ACTIVACION_EN_CURSO"
CODIGO_ACTIVADOR_NO_DISPONIBLE = "ACTIVADOR_NO_DISPONIBLE"
CODIGO_ACTIVACION_FALLIDA = "ACTIVACION_FALLIDA"
CODIGO_ACTIVACION_RECHAZADA = "ACTIVACION_RECHAZADA"
CODIGO_DOMINIO_NO_CATALOGADO = "DOMINIO_NO_CATALOGADO"

#: La acción segura que sigue.
ACCION_NINGUNA = "NINGUNA"
ACCION_REINTENTAR = "REINTENTAR_ACTIVACION"
ACCION_ESPERAR = "ESPERAR_ACTIVACION"


class CoordinadorActivacionCompra:
    """Coordinador de la activación de derechos de una compra pagada."""

    @inject
    def __init__(
        self,
        core: ActivacionCompraCoreService,
        registro: RegistroActivadoresCompra,
    ) -> None:
        self.core = core
        self.registro = registro

    # ── Entradas ────────────────────────────────────────────────────────────

    def activar_por_orden(self, orden_pago_id: str) -> ResultadoActivacionCompra:
        """Activa los derechos de la compra que financia la orden.

        Es la entrada que usa `pagos` (a través del puerto
        `IActivacionCompraService`) al confirmar un pago.

        Args:
            orden_pago_id: UUID de la `OrdenPago` confirmada.

        Returns:
            El resultado de la activación. Nunca lanza por un fallo esperado:
            un fallo del dominio es una incidencia recuperable, no un error.
        """
        compra = self.core.obtener_compra_por_orden(orden_pago_id)
        if compra is None:
            return ResultadoActivacionCompra(
                existe=False,
                codigo=CODIGO_SIN_COMPRA,
                proxima_accion=ACCION_NINGUNA,
            )
        return self.activar_por_compra(compra.id)

    def activar_por_compra(self, compra_id) -> ResultadoActivacionCompra:
        """Activa los derechos de una compra ya pagada.

        Es idempotente: una segunda llamada sobre una activación `ACTIVADA`
        NO vuelve a invocar al dominio.

        Args:
            compra_id: UUID de la `Compra`.

        Returns:
            El resultado de la activación.
        """
        compra = self._leer_compra(compra_id)
        if compra is None:
            return ResultadoActivacionCompra(
                existe=False,
                codigo=CODIGO_SIN_COMPRA,
                proxima_accion=ACCION_NINGUNA,
            )

        if compra.estado != EstadoCompra.PAGADA:
            # El pago confirmado y la entrega del derecho son hechos
            # separados: sin pago confirmado no hay nada que activar, y no
            # es una incidencia (RN-C08).
            return ResultadoActivacionCompra(
                existe=True,
                codigo=CODIGO_COMPRA_NO_PAGADA,
                proxima_accion=ACCION_NINGUNA,
            )

        activacion = self._obtener_o_crear(compra)
        if activacion.estado == EstadoActivacionCompra.ACTIVADA:
            # TERMINAL: el derecho ya está habilitado. No se vuelve a invocar
            # al dominio (FR-04 I-2).
            return ResultadoActivacionCompra(
                existe=True,
                activada=True,
                ya_activada=True,
                intentos=activacion.intentos,
                codigo=CODIGO_ACTIVACION_YA_COMPLETADA,
                proxima_accion=ACCION_NINGUNA,
            )

        if not self.core.reclamar(activacion.id):
            # Otro intento tiene la activación reservada: no se despacha dos
            # veces. El llamador puede reintentar más tarde.
            return ResultadoActivacionCompra(
                existe=True,
                en_curso=True,
                recuperable=True,
                intentos=activacion.intentos + 1,
                codigo=CODIGO_ACTIVACION_EN_CURSO,
                proxima_accion=ACCION_ESPERAR,
            )

        activador = self.registro.resolver(compra.origen)
        if activador is None:
            # El dominio de origen todavía no puede activar. La activación
            # queda PENDIENTE y reintentable; el pago se conserva (RN-C08).
            self.core.liberar(activacion.id)
            return ResultadoActivacionCompra(
                existe=True,
                recuperable=True,
                intentos=activacion.intentos + 1,
                codigo=CODIGO_ACTIVADOR_NO_DISPONIBLE,
                proxima_accion=ACCION_REINTENTAR,
            )

        contexto = self._contexto(compra, activacion.clave)

        try:
            resultado = activador.activar(contexto)
        except Exception:
            # El dominio falló. El texto de la excepción NUNCA se persiste ni
            # se devuelve: sólo un código seguro (RN-C08, FR-04 §4).
            logger.exception(
                "El dominio de origen %s no pudo activar los derechos de la "
                "compra %s. El pago confirmado se conserva.",
                compra.origen,
                compra.id,
            )
            self.core.marcar_fallida(
                activacion.id,
                self._incidencia(
                    compra,
                    activacion.intentos + 1,
                    CODIGO_ACTIVACION_FALLIDA,
                ),
            )
            return ResultadoActivacionCompra(
                existe=True,
                recuperable=True,
                intentos=activacion.intentos + 1,
                codigo=CODIGO_ACTIVACION_FALLIDA,
                proxima_accion=ACCION_REINTENTAR,
            )

        if not resultado.exito:
            self.core.marcar_fallida(
                activacion.id,
                self._incidencia(
                    compra,
                    activacion.intentos + 1,
                    self._codigo_seguro(resultado.codigo),
                ),
            )
            return ResultadoActivacionCompra(
                existe=True,
                recuperable=True,
                intentos=activacion.intentos + 1,
                codigo=CODIGO_ACTIVACION_RECHAZADA,
                proxima_accion=ACCION_REINTENTAR,
            )

        self.core.marcar_activada(
            activacion.id,
            self._detalle_seguro(resultado.detalle),
        )
        return ResultadoActivacionCompra(
            existe=True,
            activada=True,
            intentos=activacion.intentos + 1,
            codigo=CODIGO_ACTIVACION_COMPLETADA,
            proxima_accion=ACCION_NINGUNA,
        )

    # ── Internos ────────────────────────────────────────────────────────────

    def _leer_compra(self, compra_id) -> Compra | None:
        """La compra tal como está ahora en la base de datos."""
        try:
            return Compra.objects.filter(id=compra_id).first()
        except (ValueError, TypeError):
            return None

    def _obtener_o_crear(self, compra: Compra) -> ActivacionCompra:
        """La activación de `(compra, origen)`, creándola si no existe.

        La carrera la resuelve la restricción única de la base de datos: si
        otra vuelta la creó primero, `get_or_create` devuelve la suya.
        """
        clave = self._clave(compra)
        activacion, _creada = ActivacionCompra.objects.get_or_create(
            compra=compra,
            origen=compra.origen,
            defaults={"clave": clave},
        )
        return activacion

    def _clave(self, compra: Compra) -> str:
        """La clave de idempotencia de la activación.

        Es **estable**: se deriva de `(compra_id, origen)` y no cambia entre
        reintentos. Es lo que permite que el dominio no aplique el derecho
        dos veces y lo que hace que el reintento converja (FR-04 I-2).
        """
        return f"activacion:{compra.origen}:{compra.id}"

    def _contexto(self, compra: Compra, clave: str) -> ContextoActivacionCompra:
        """Los hechos congelados que se entregan al dominio.

        El coordinador NO resuelve reglas de dominio: entrega el snapshot y
        la clave, y el dominio decide.
        """
        return ContextoActivacionCompra(
            compra_id=compra.id,
            origen=compra.origen,
            clave=clave,
            persona_id=compra.persona_id,
            referencia=compra.referencia,
            total=compra.total,
            moneda=compra.moneda,
            lineas_snapshot=list(compra.lineas_snapshot or []),
        )

    def _incidencia(self, compra: Compra, intento: int, codigo: str) -> dict:
        """La incidencia persistida: SÓLO datos seguros.

        Nunca el texto de una excepción, ni un payload de proveedor, ni un
        identificador interno, ni un secreto (FR-04 §4, RN-C08).
        """
        return {
            "codigo": codigo,
            "origen": compra.origen,
            "intento": intento,
            "fecha": timezone.now().isoformat(),
        }

    def _codigo_seguro(self, codigo: str) -> str:
        """Un código de máquina seguro, o el genérico si no lo es."""
        if codigo and CODIGO_SEGURO.match(codigo):
            return codigo
        return CODIGO_DOMINIO_NO_CATALOGADO

    def _detalle_seguro(self, detalle: dict) -> dict:
        """El detalle del dominio, reducido a la lista cerrada de claves.

        Cualquier clave que no esté permitida, o cualquier valor que no sea
        un escalar corto, se descarta: así el detalle persistido no puede
        filtrar identificadores ni texto libre.
        """
        limpio: dict = {}
        for clave, valor in (detalle or {}).items():
            if clave not in CLAVES_DETALLE_PERMITIDAS:
                continue
            if isinstance(valor, bool) or isinstance(valor, (int, float)):
                limpio[clave] = valor
            elif isinstance(valor, str) and CODIGO_SEGURO.match(valor):
                limpio[clave] = valor
        return limpio


__all__ = [
    "ACCION_ESPERAR",
    "ACCION_NINGUNA",
    "ACCION_REINTENTAR",
    "CODIGO_ACTIVACION_COMPLETADA",
    "CODIGO_ACTIVACION_EN_CURSO",
    "CODIGO_ACTIVACION_FALLIDA",
    "CODIGO_ACTIVACION_RECHAZADA",
    "CODIGO_ACTIVACION_YA_COMPLETADA",
    "CODIGO_ACTIVADOR_NO_DISPONIBLE",
    "CODIGO_COMPRA_NO_PAGADA",
    "CODIGO_SIN_COMPRA",
    "CoordinadorActivacionCompra",
]
