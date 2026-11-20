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
from modules.salesianos_fest.tests.fixtures.pase_fixtures import (  # noqa: F401
    TOKEN_PASE_FIJO,
    beneficiario_pase,
    compra_pase_con_compra,
    compra_pase_pagada,
    compra_pase_pendiente,
    cortesia_pase,
    edicion_con_pases,
    pase,
    pase_retirado,
    pase_sin_precio,
    usuario_admin,
)


# ── ORDEN DE PRUEBAS: el registro de activadores es del PROCESO ────────────
#
# `SalesianosFestConfig.ready()` registra en `commerce` los activadores de los
# orígenes `INSCRIPCION` y `PASE`. Ese registro es un objeto ÚNICO DEL
# PROCESO (`D-FND-05-04`).
#
# `modules/commerce/tests/fixtures/activacion_fakes.py::registro_activadores`
# lo VACÍA antes y después de cada prueba que lo usa: cuando las pruebas de
# `commerce` corren antes que las de este módulo en la misma sesión, la
# registración de `ready()` se pierde y el resultado dependía del ORDEN de
# las pruebas.
#
# El snapshot se toma al IMPORTAR este conftest, durante la COLECCIÓN (Django
# ya está configurado y `ready()` ya corrió, pero ninguna prueba se ha
# ejecutado todavía, así que el registro está intacto).
from modules.commerce.domain.constants import OrigenCompra
from modules.commerce.domain.services.core.registro_activadores_compra import (
    obtener_registro,
)

#: La registración que dejó `SalesianosFestConfig.ready()`.
_ACTIVADORES_DE_SALESIANOS_FEST = {
    origen: obtener_registro().resolver(origen)
    for origen in (OrigenCompra.INSCRIPCION, OrigenCompra.PASE)
}


@pytest.fixture(autouse=True)
def activadores_de_salesianos_fest_registrados():
    """Restaura las registraciones de `ready()` si otro módulo las vació.

    El registro de activadores de `commerce` es un objeto ÚNICO DEL PROCESO
    (`D-FND-05-04`) y `apps.py::ready()` lo registra al arrancar. En
    PRODUCCIÓN esa registración es correcta y no se repite: nada llama a
    `limpiar()` fuera de las pruebas.

    En las PRUEBAS, el fixture `registro_activadores` de `commerce` vacía ese
    registro antes y después de cada test que lo usa, y con él se lleva la
    registración de este módulo para el resto de la sesión. Este fixture la
    RESTAURA: es una adaptación de AISLAMIENTO DE PRUEBAS, no un atajo de la
    regla de negocio (la idempotencia de la activación se comprueba con la
    clave, no con el registro).

    **RESTAURA LA REGISTRACIÓN ORIGINAL, NO UNA NUEVA.** El snapshot se toma
    al IMPORTAR este conftest, durante la COLECCIÓN (Django ya está
    configurado y `ready()` ya corrió, pero ninguna prueba se ha ejecutado
    todavía, así que el registro está intacto). Si `ready()` NO hubiera
    registrado el activador, el snapshot sería `None`, no se restauraría nada
    y la prueba que verifica la registración SEGUIRÍA FALLANDO.

    Esto NO es un detalle: la versión anterior de esta fixture REGISTRABA una
    instancia NUEVA en cada prueba, lo que hacía VACUA la verificación de
    `test_el_modulo_registra_su_activador_para_el_origen_inscripcion`: esa
    prueba pasaba aunque `ready()` no registrara NADA. Restaurar el snapshot
    conserva el significado del aserto.

    Petición a A0 (A0-DOM02-09): decidir si `limpiar()` debe RESTAURAR las
    registraciones de los dominios, para que el registro del proceso no
    dependa del orden de los tests. La raíz está en `modules/commerce/**`
    (raíz compartida): este guard sólo acota el AISLAMIENTO de las pruebas de
    este módulo.
    """
    registro = obtener_registro()
    for origen, activador in _ACTIVADORES_DE_SALESIANOS_FEST.items():
        if activador is None:
            continue
        if registro.resolver(origen) is None:
            registro.registrar(origen, activador)
    yield

