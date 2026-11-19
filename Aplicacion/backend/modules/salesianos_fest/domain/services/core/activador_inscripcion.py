"""`ActivadorInscripcion` — la activación de derechos del origen `INSCRIPCION`.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3, I-2) · `RN-I02` · `RN-I06` · `QA-I02`

Este es el ADAPTADOR que el módulo registra en el coordinador de `commerce`
(`IActivadorDominioCompra`). El coordinador conoce interfaces, no reglas de
dominio: entrega los hechos CONGELADOS de la compra y una clave estable, y
este adaptador decide qué significa activarlos para una inscripción.

**Qué hace, exactamente:**

1. Resuelve la inscripción a partir de la REFERENCIA de intención, que es
   de este módulo y por tanto la entiende (`domain/referencia.py`).
2. Calcula cuántos cupos habilita la compra a partir del SNAPSHOT de líneas
   que congeló `commerce`: el servidor ya resolvió el precio y la cantidad.
3. Registra la ACTIVACIÓN con esa clave. La restricción única de
   `ActivacionCapacidad.clave` es la autoridad de "exactamente una vez": un
   reintento de la MISMA compra NO vuelve a sumar cupos (`QA-I02`).
4. Suma los cupos a la capacidad PAGADA de la inscripción (`RN-I02`).
5. Concede los beneficios `FIJO_INICIAL` — SÓLO en la activación del ALTA:
   una ampliación NO los vuelve a conceder (`RN-I06`).

**Atomicidad.** Este servicio abre su propia transacción porque lo invoca un
COORDINADOR EXTERNO (`commerce`), no un flujo de este módulo: la regla de
`contract/django-app-architecture-contract.md` §4.4 (la transacción la abre
el flujo) aplica a los flujos propios; aquí la unidad atómica es "registrar
la activación, sumar los cupos y conceder los beneficios" o nada.

**Fallo.** Una excepción se propaga al coordinador, que la registra como
incidencia RECUPERABLE y conserva el pago confirmado (`RN-C08`).
"""

from django.db import IntegrityError, transaction
from injector import inject

from modules.commerce.domain.ports import IActivadorDominioCompra
from modules.commerce.domain.schemas.compra_schemas import (
    ContextoActivacionCompra,
    ResultadoActivacionDominio,
)
from modules.salesianos_fest.domain.constants import (
    CODIGO_CAPACIDAD_ACTIVADA,
    CODIGO_CAPACIDAD_YA_ACTIVADA,
    CODIGO_INSCRIPCION_NO_ENCONTRADA,
    CODIGO_REFERENCIA_NO_RECONOCIDA,
    CODIGO_SIN_CUPOS_ACTIVABLES,
    CONCEPTO_LINEA_CUPO,
    CONCEPTO_LINEA_PAQUETE,
)
from modules.salesianos_fest.domain.models import ActivacionCapacidad
from modules.salesianos_fest.domain.referencia import parsear_referencia
from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
    InscripcionSelector,
)
from modules.salesianos_fest.domain.selectors.pool_selector import PoolSelector
from modules.salesianos_fest.domain.services.core.beneficio_core_service import (
    BeneficioCoreService,
)
from modules.salesianos_fest.domain.services.core.capacidad_core_service import (
    CapacidadCoreService,
)

#: Tipos de línea de compra que este módulo sabe activar.
CONCEPTOS_ACTIVABLES = (CONCEPTO_LINEA_PAQUETE, CONCEPTO_LINEA_CUPO)


class ActivadorInscripcion(IActivadorDominioCompra):
    """El activador de derechos del dominio de inscripción."""

    @inject
    def __init__(
        self,
        capacidad_core: CapacidadCoreService | None = None,
        beneficio_core: BeneficioCoreService | None = None,
        pool_selector: PoolSelector | None = None,
        inscripcion_selector: InscripcionSelector | None = None,
    ):
        # Los colaboradores son collaborators sin estado: el activador puede
        # construirse a mano (lo registra el proceso al arrancar) o por DI.
        self.capacidad_core = capacidad_core or CapacidadCoreService()
        self.beneficio_core = beneficio_core or BeneficioCoreService()
        self.pool_selector = pool_selector or PoolSelector()
        self.inscripcion_selector = inscripcion_selector or InscripcionSelector()

    def activar(self, contexto: ContextoActivacionCompra) -> ResultadoActivacionDominio:
        """Habilita los cupos que la compra pagó.

        Es IDEMPOTENTE por `contexto.clave`: la misma clave nunca suma
        cupos dos veces.

        Args:
            contexto: los hechos congelados de la compra y la clave estable.

        Returns:
            El resultado del dominio. `exito=False` significa "no se aplicó":
            el derecho sigue sin concederse y la activación queda
            reintentable.
        """
        try:
            with transaction.atomic():
                return self._activar_sync(contexto)
        except IntegrityError:
            # Carrera: otra activación del MISMO derecho ganó y ya aplicó la
            # capacidad. La fila ganadora es la buena: se devuelve SU
            # resultado y NO se vuelve a sumar ningún cupo.
            existente = self.pool_selector.obtener_activacion_por_clave(
                contexto.clave
            )
            if existente is None:
                raise
            return self._resultado_ya_activada(existente.cupos)

    # ── Internos sync ───────────────────────────────────────────────────────

    def _activar_sync(
        self,
        contexto: ContextoActivacionCompra,
    ) -> ResultadoActivacionDominio:
        """La activación, dentro de la transacción."""
        intencion = parsear_referencia(contexto.referencia)
        if intencion is None:
            # La compra no es de este módulo: no se inventa a quién
            # pertenece.
            return ResultadoActivacionDominio(
                exito=False,
                codigo=CODIGO_REFERENCIA_NO_RECONOCIDA,
            )

        ya_activada = self.pool_selector.obtener_activacion_por_clave(contexto.clave)
        if ya_activada is not None:
            # Reintento de una activación ya aplicada: se devuelve el
            # resultado guardado y NO se vuelve a sumar ningún cupo.
            return self._resultado_ya_activada(ya_activada.cupos)

        inscripcion = self.inscripcion_selector.obtener_por_id(
            intencion.inscripcion_id
        )
        if inscripcion is None:
            return ResultadoActivacionDominio(
                exito=False,
                codigo=CODIGO_INSCRIPCION_NO_ENCONTRADA,
            )

        cupos = self._cupos_de_la_linea(contexto)
        if cupos <= 0:
            return ResultadoActivacionDominio(
                exito=False,
                codigo=CODIGO_SIN_CUPOS_ACTIVABLES,
            )

        # El registro de la activación es lo que hace idempotente al
        # activador: la clave es ÚNICA en la base de datos.
        activacion = ActivacionCapacidad.objects.create(
            inscripcion=inscripcion,
            clave=contexto.clave,
            compra_id=contexto.compra_id,
            tipo=intencion.tipo,
            cupos=cupos,
        )

        self.capacidad_core.habilitar_cupos_pagados(inscripcion.id, cupos)

        # Los beneficios `FIJO_INICIAL` se conceden SÓLO en el alta: una
        # ampliación no los duplica (`RN-I06`).
        if intencion.es_inicial:
            self.beneficio_core.conceder_fijo_inicial(inscripcion, activacion)

        return ResultadoActivacionDominio(
            exito=True,
            codigo=CODIGO_CAPACIDAD_ACTIVADA,
            detalle={
                "cantidad": cupos,
                "estado": "ACTIVADA",
            },
        )

    @staticmethod
    def _resultado_ya_activada(cupos: int) -> ResultadoActivacionDominio:
        """El resultado de una activación que ya se había aplicado."""
        return ResultadoActivacionDominio(
            exito=True,
            codigo=CODIGO_CAPACIDAD_YA_ACTIVADA,
            detalle={
                "cantidad": cupos,
                "estado": "YA_ACTIVADA",
            },
        )

    @staticmethod
    def _cupos_de_la_linea(contexto: ContextoActivacionCompra) -> int:
        """Los cupos que habilita el snapshot de líneas de la compra.

        El snapshot lo congeló `commerce` a partir de lo que resolvió el
        servidor: la cantidad comprada. El activador NO vuelve a consultar
        el catálogo ni a calcular precios (`RN-C02`).
        """
        total = 0
        for linea in contexto.lineas_snapshot or []:
            if not isinstance(linea, dict):
                continue
            if linea.get("concepto_tipo") not in CONCEPTOS_ACTIVABLES:
                continue
            try:
                cantidad = int(linea.get("cantidad") or 0)
            except (TypeError, ValueError):
                continue
            total += max(cantidad, 0)
        return total


__all__ = ["CONCEPTOS_ACTIVABLES", "ActivadorInscripcion"]
