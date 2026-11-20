"""Fixtures del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

El módulo de agregación NO tiene datos propios: sus tests usan las fixtures
del módulo DUEÑO (`salesianos_fest`), que es donde vive la edición, la
inscripción, el equipo y la persona. Importarlas aquí es deliberado: el
resumen tiene que contar los hechos del dueño, no los suyos.
"""

import pytest

from modules.salesianos_fest.tests.fixtures.fest_fixtures import (  # noqa: F401
    categoria,
    disciplina,
    edicion_publicada,
    equipo,
    evento,
    injector,
    inscripcion,
    persona,
    persona_ajena,
    persona_participante,
    paquete,
    precio,
    promocion,
    usuario_responsable,
)


@pytest.fixture
def inscripcion_sin_pagos(db, edicion_publicada, paquete, persona_ajena, promocion):
    """Inscripción SIN capacidad pagada, con OTRO responsable.

    **Shadowa** la fixture del dueño (`fest_fixtures.inscripcion_sin_pagos`):
    aquí esta inscripción CONVIVE con `inscripcion` en el mismo test, y la
    restricción `fest_inscripcion_unica_por_responsable_y_paquete`
    (edición, responsable, paquete) no admite dos inscripciones del mismo
    responsable con el mismo paquete. La fixture del dueño NO se toca: la
    comparten 30 casos de `test_cupo_activacion.py`, donde nunca convive con
    `inscripcion`.
    """
    from modules.salesianos_fest.domain.models import Inscripcion

    return Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona_ajena,
        paquete=paquete,
        promocion=promocion,
        referencia="INS-ADM-0002",
        cupos_solicitados=10,
        cupos_pagados=0,
        cupos_asignados=0,
    )


@pytest.fixture
def selector():
    """El selector del resumen, sin dependencias externas."""
    from modules.administracion.domain.selectors.admin_resumen_selector import (
        AdminResumenSelector,
    )

    return AdminResumenSelector()


@pytest.fixture
def servicio_auditoria():
    """El servicio que escribe el acta."""
    from modules.administracion.domain.services.core.admin_auditoria_service import (
        AdminAuditoriaService,
    )

    return AdminAuditoriaService()
