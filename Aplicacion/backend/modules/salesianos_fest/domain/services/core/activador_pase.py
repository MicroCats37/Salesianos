"""`ActivadorPase` — la activación de derechos del origen `PASE`.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3, I-2) · `RN-P02` · `QA-P01`

Este es el ADAPTADOR que el módulo registra en el coordinador de `commerce`
(`IActivadorDominioCompra`). El coordinador conoce interfaces, no reglas de
dominio: entrega los hechos CONGELADOS de la compra y una clave estable, y
este adaptador decide qué significa activarlos para un lote de pases.

**Qué hace, exactamente:**

1. Resuelve el lote a partir de la compra de `commerce` (`contexto.compra_id`)
   y COMPRUEBA que la referencia de intención es de este módulo: una
   referencia que no encaja NO se adivina.
2. Calcula cuántos pases habilita la compra a partir del SNAPSHOT de líneas
   que congeló `commerce`: el servidor ya resolvió el precio y la cantidad.
3. Registra la ACTIVACIÓN con esa clave. La restricción única de
   `ActivacionPase.clave` es la autoridad de "exactamente una vez": un
   reintento de la MISMA compra NO vuelve a habilitar los pases (`QA-P01`).
4. Marca el lote como `PAGADA`. HASTA ENTONCES no se puede asignar ningún
   beneficiario (`RN-P02`).

**Atomicidad.** Este servicio abre su propia transacción porque lo invoca un
COORDINADOR EXTERNO (`commerce`), no un flujo de este módulo: la regla de
`contract/django-app-architecture-contract.md` §4.4 (la transacción la abre
el flujo) aplica a los flujos propios; aquí la unidad atómica es "registrar
la activación y marcar el lote pagado" o nada.

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
    CODIGO_COMPRA_PASE_NO_ENCONTRADA,
    CODIGO_PASES_ACTIVADOS,
    CODIGO_PASES_YA_ACTIVADOS,
    CODIGO_REFERENCIA_PASE_NO_RECONOCIDA,
    CODIGO_SIN_PASES_ACTIVABLES,
    CONCEPTO_LINEA_PASE,
)
from modules.salesianos_fest.domain.models import ActivacionPase
from modules.salesianos_fest.domain.referencia_pase import parsear_referencia_pase
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.services.core.pase_core_service import (
    PaseCoreService,
)

#: Tipos de línea de compra que este módulo sabe activar.
CONCEPTOS_ACTIVABLES = (CONCEPTO_LINEA_PASE,)


class ActivadorPase(IActivadorDominioCompra):
    """El activador de derechos del dominio de pases."""

    @inject
    def __init__(
        self,
        pase_core: PaseCoreService | None = None,
        pase_selector: PaseSelector | None = None,
    ):
        # Los colaboradores son collaborators sin estado: el activador puede
        # construirse a mano (lo registra el proceso al arrancar) o por DI.
        self.pase_core = pase_core or PaseCoreService()
        self.pase_selector = pase_selector or PaseSelector()

    def activar(self, contexto: ContextoActivacionCompra) -> ResultadoActivacionDominio:
        """Habilita los pases que la compra pagó.

        Es IDEMPOTENTE por `contexto.clave`: la misma clave nunca habilita
        los pases dos veces.

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
            # Carrera: otra activación del MISMO derecho ganó y ya aplicó
            # la activación. La fila ganadora es la buena: se devuelve SU
            # resultado y NO se vuelve a habilitar ningún pase.
            existente = self.pase_selector.obtener_activacion_por_clave(
                contexto.clave
            )
            if existente is None:
                raise
            return self._resultado_ya_activada(existente.cantidad)

    # ── Internos sync ───────────────────────────────────────────────────────

    def _activar_sync(
        self,
        contexto: ContextoActivacionCompra,
    ) -> ResultadoActivacionDominio:
        """La activación, dentro de la transacción."""
        intencion = parsear_referencia_pase(contexto.referencia)
        if intencion is None:
            # La compra no es de este módulo: no se inventa a quién
            # pertenece.
            return ResultadoActivacionDominio(
                exito=False,
                codigo=CODIGO_REFERENCIA_PASE_NO_RECONOCIDA,
            )

        ya_activada = self.pase_selector.obtener_activacion_por_clave(contexto.clave)
        if ya_activada is not None:
            # Reintento de una activación ya aplicada: se devuelve el
            # resultado guardado y NO se vuelve a habilitar ningún pase.
            return self._resultado_ya_activada(ya_activada.cantidad)

        compra_pase = self.pase_selector.obtener_compra_pase_por_compra(
            contexto.compra_id
        )
        if compra_pase is None:
            return ResultadoActivacionDominio(
                exito=False,
                codigo=CODIGO_COMPRA_PASE_NO_ENCONTRADA,
            )

        if not intencion.coincide_con(
            edicion_id=compra_pase.edicion_id,
            pase_id=compra_pase.pase_id,
            comprador_id=compra_pase.comprador_id,
            cantidad=compra_pase.cantidad,
        ):
            # La compra de `commerce` y la referencia NO describen la misma
            # intención: no se aplica nada.
            return ResultadoActivacionDominio(
                exito=False,
                codigo=CODIGO_REFERENCIA_PASE_NO_RECONOCIDA,
            )

        pases = self._pases_de_la_linea(contexto)
        if pases <= 0:
            return ResultadoActivacionDominio(
                exito=False,
                codigo=CODIGO_SIN_PASES_ACTIVABLES,
            )

        # El registro de la activación es lo que hace idempotente al
        # activador: la clave es ÚNICA en la base de datos.
        ActivacionPase.objects.create(
            compra_pase=compra_pase,
            clave=contexto.clave,
            compra_id=contexto.compra_id,
            cantidad=pases,
        )

        # El lote pasa a `PAGADA`: a partir de aquí se puede asignar.
        self.pase_core.marcar_pagada(compra_pase.id)

        return ResultadoActivacionDominio(
            exito=True,
            codigo=CODIGO_PASES_ACTIVADOS,
            detalle={
                "cantidad": pases,
                "estado": "ACTIVADA",
            },
        )

    @staticmethod
    def _resultado_ya_activada(cantidad: int) -> ResultadoActivacionDominio:
        """El resultado de una activación que ya se había aplicado."""
        return ResultadoActivacionDominio(
            exito=True,
            codigo=CODIGO_PASES_YA_ACTIVADOS,
            detalle={
                "cantidad": cantidad,
                "estado": "YA_ACTIVADA",
            },
        )

    @staticmethod
    def _pases_de_la_linea(contexto: ContextoActivacionCompra) -> int:
        """Los pases que habilita el snapshot de líneas de la compra.

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


__all__ = ["CONCEPTOS_ACTIVABLES", "ActivadorPase"]
