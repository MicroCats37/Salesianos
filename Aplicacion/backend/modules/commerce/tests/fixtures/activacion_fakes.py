"""Dobles de prueba del puerto de activación de derechos.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3
Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.1 I-2)

Estos dobles son **reutilizables por los dominios de origen** (DOM-02
`inscripciones`, DOM-03 `pases`, DOM-06 `marketplace`): implementan el
puerto `IActivadorDominioCompra` sin reescribir su contrato y sin duplicar
las reglas de ningún dominio (ni de cupos, ni de pases, ni de stock).

Lo que modela el doble es el CONTRATO del puerto, no el dominio:

- la activación es **idempotente por clave**: dos llamadas con la misma clave
  aplican el derecho **una sola vez**;
- el dominio puede **fallar** o **rechazar** a voluntad;
- el resultado sólo lleva un código de máquina y un detalle con claves
  permitidas.

Importable desde cualquier test del proyecto:

    from modules.commerce.tests.fixtures.activacion_fakes import (
        ActivadorDominioFake,
        registro_activadores,
    )
"""

import pytest

from modules.commerce.domain.schemas.compra_schemas import ResultadoActivacionDominio
from modules.commerce.domain.services.core.registro_activadores_compra import (
    obtener_registro,
)


class ActivadorDominioFake:
    """Doble de un activador de dominio.

    Aplica el derecho **una sola vez por clave**, que es exactamente lo que
    el puerto exige del dominio. No implementa ninguna regla de cupos, pases
    ni stock: no las conoce y no debe conocerlas.
    """

    def __init__(
        self,
        origen: str = "INSCRIPCION",
        *,
        fallar: bool = False,
        rechazar: bool = False,
        codigo: str = "DERECHO_HABILITADO",
        codigo_rechazo: str = "DOMINIO_RECHAZO",
        detalle: dict | None = None,
        mensaje_fallo: str = "El dominio no pudo aplicar el derecho.",
    ) -> None:
        self.origen = origen
        self.fallar = fallar
        self.rechazar = rechazar
        self.codigo = codigo
        self.codigo_rechazo = codigo_rechazo
        self.detalle = detalle if detalle is not None else {"cantidad": 1}
        self.mensaje_fallo = mensaje_fallo
        #: Callback opcional: se invoca en cada llamada, ANTES de aplicar.
        self.al_activar = None
        #: Todos los contextos recibidos.
        self.llamadas: list = []
        #: Las claves cuyo derecho se aplicó EFECTIVAMENTE (una sola vez).
        self.claves_efectivas: list[str] = []

    @property
    def llamadas_efectivas(self) -> int:
        """Cuántas veces se aplicó el derecho de verdad."""
        return len(self.claves_efectivas)

    def activar(self, contexto) -> ResultadoActivacionDominio:
        """Aplica (o no) el derecho, una sola vez por clave."""
        self.llamadas.append(contexto)

        if self.al_activar is not None:
            self.al_activar(contexto)

        if self.fallar:
            raise RuntimeError(self.mensaje_fallo)

        if self.rechazar:
            return ResultadoActivacionDominio(
                exito=False,
                codigo=self.codigo_rechazo,
            )

        if contexto.clave not in self.claves_efectivas:
            self.claves_efectivas.append(contexto.clave)

        return ResultadoActivacionDominio(
            exito=True,
            codigo=self.codigo,
            detalle=dict(self.detalle),
        )


@pytest.fixture
def registro_activadores():
    """El registro de activadores del proceso, limpio antes y después.

    El registro es único en el proceso (los dominios registran su activador
    sin tocar `commerce`), así que la prueba lo vacía al empezar y al
    terminar: ninguna prueba ve el activador de otra.
    """
    registro = obtener_registro()
    registro.limpiar()
    yield registro
    registro.limpiar()


@pytest.fixture
def activador(registro_activadores):
    """Un activador de dominio registrado para `INSCRIPCION`."""
    doble = ActivadorDominioFake(origen="INSCRIPCION")
    registro_activadores.registrar("INSCRIPCION", doble)
    return doble


__all__ = [
    "ActivadorDominioFake",
    "activador",
    "registro_activadores",
]
