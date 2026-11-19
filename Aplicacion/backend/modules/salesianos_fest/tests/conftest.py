"""Registro de fixtures del módulo `salesianos_fest`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Este `conftest.py` sólo importa y registra los módulos de fixtures; las
fixtures reales viven en `fixtures/`.
"""

import pytest

from modules.salesianos_fest.tests.fixtures.fest_fixtures import (  # noqa: F401
    beneficio,
    beneficio_por_cupo,
    disciplina,
    disciplina_inactiva,
    disciplina_otra_edicion,
    edicion_borrador,
    edicion_otra,
    edicion_publicada,
    edicion_sin_modulo,
    equipo,
    evento,
    injector,
    inscripcion,
    inscripcion_sin_pagos,
    paquete,
    paquete_retirado,
    paquete_sin_precio,
    persona,
    persona_ajena,
    persona_otro_participante,
    persona_participante,
    precio,
    usuario_ajeno,
    usuario_responsable,
)


@pytest.fixture(autouse=True)
def activator_de_inscripcion_registrado():
    """Asegura que el activador del origen INSCRIPCION esté registrado.

    El registro de activadores de `commerce` es un objeto ÚNICO DEL PROCESO
    (`D-FND-05-04`) y `apps.py::ready()` lo registra al arrancar. En
    PRODUCCIÓN esa registration es correcta y no se repite: nada llama a
    `limpiar()` fuera de las pruebas.

    En las PRUEBAS, el fixture `registro_activadores` de `commerce` vacía ese
    registro antes y después de cada test que lo usa, y con él se lleva el
    activador de este módulo para el resto de la sesión. Este fixture lo
    vuelve a registrar: es una adaptación de AISLAMIENTO DE PRUEBAS, no un
    atajo de la regla de negocio (la idempotencia de la activación se
    comprueba con la clave, no con el registro).

    Petición a A0 (A0-DOM02-09): decidir si `limpiar()` debe RESTAURAR las
    registraciones de los dominios, para que el registro del proceso no
    dependa del orden de los tests.
    """
    from modules.commerce.domain.constants import OrigenCompra
    from modules.commerce.domain.services.core.registro_activadores_compra import (
        obtener_registro,
    )
    from modules.salesianos_fest.domain.services.core.activador_inscripcion import (
        ActivadorInscripcion,
    )

    obtener_registro().registrar(
        OrigenCompra.INSCRIPCION,
        ActivadorInscripcion(),
    )
    yield

