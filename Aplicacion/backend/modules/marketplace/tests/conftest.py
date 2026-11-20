"""Registro de fixtures del módulo `marketplace`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Este `conftest.py` sólo importa y registra los módulos de fixtures; las
fixtures reales viven en `fixtures/`.
"""

import pytest

from modules.marketplace.tests.fixtures.inventario_fixtures import (  # noqa: F401
    inventario_orchestrator,
    pedido_pagado,
    producto_agotado,
    producto_con_stock,
)
from modules.marketplace.tests.fixtures.marketplace_fixtures import (  # noqa: F401
    archivo_grande,
    archivo_jpeg,
    archivo_mentiroso,
    archivo_png,
    categoria_producto,
    edicion_otra,
    edicion_publicada,
    edicion_sin_marketplace,
    evento,
    media_root,
    producto,
    token_admin,
    usuario_admin,
)
from modules.marketplace.tests.fixtures.pedido_fixtures import (  # noqa: F401
    edicion_ajena,
    edicion_publicada_sin_tienda,
    pedido_orchestrator,
    persona_compradora,
    producto_ajeno,
    producto_con_oferta,
    producto_inactivo,
    token_ajeno,
    token_comprador,
    usuario_ajeno,
    usuario_comprador,
    usuario_sin_persona,
)

# ── ORDEN DE PRUEBAS: el registro de activadores es del PROCESO ────────────
#
# `MarketplaceConfig.ready()` registra el activador del origen `MARKETPLACE`
# en el registro de activadores de `commerce`, que es un objeto ÚNICO DEL
# PROCESO (`D-FND-05-04`).
#
# `modules/commerce/tests/fixtures/activacion_fakes.py::registro_activadores`
# vacía ese registro antes y después de cada prueba que lo usa. Cuando las
# pruebas de `commerce` corren ANTES que las de `marketplace` en la misma
# sesión, el vaciado se lleva la registración de `ready()` y la prueba que la
# verifica falla aunque el módulo esté correcto: el resultado dependía del
# ORDEN de las pruebas, no del comportamiento del módulo.
#
# Este guard restaura la registración ORIGINAL — la que dejó `ready()` — y
# NUNCA una nueva: el snapshot se toma al IMPORTAR este conftest, durante la
# COLECCIÓN (Django ya está configurado y `ready()` ya corrió, pero ninguna
# prueba se ha ejecutado todavía, así que el registro está intacto). Si
# `ready()` NO hubiera registrado el activador, el snapshot sería `None`, no
# se restauraría nada y la prueba SEGUIRÍA FALLANDO: el aserto conserva todo
# su significado.
#
# Petición a A0 (A0-DOM02-09): decidir si `RegistroActivadoresCompra.limpiar()`
# debe RESTAURAR las registraciones de los dominios, para que el registro del
# proceso no dependa del orden de las pruebas. La RAÍZ de ese problema está en
# `modules/commerce/**` (raíz compartida, ajena a este paquete): este guard
# sólo acota el AISLAMIENTO de las pruebas de `marketplace`.
from modules.commerce.domain.constants import OrigenCompra
from modules.commerce.domain.services.core.registro_activadores_compra import (
    obtener_registro,
)

#: La registración que dejó `MarketplaceConfig.ready()` (o `None` si el módulo
#: no está instalado en la configuración activa).
_ACTIVADOR_DE_MARKETPLACE = obtener_registro().resolver(OrigenCompra.MARKETPLACE)


@pytest.fixture(autouse=True)
def activador_de_marketplace_registrado():
    """Restaurala registración del activador de `ready()` si otro módulo la vació.

    No altera el comportamiento del módulo: sólo garantiza que el registro del
    proceso llegue a cada prueba de `marketplace` como lo dejó el arranque de
    la aplicación.
    """
    if _ACTIVADOR_DE_MARKETPLACE is None:
        yield
        return

    registro = obtener_registro()
    if registro.resolver(OrigenCompra.MARKETPLACE) is None:
        registro.registrar(OrigenCompra.MARKETPLACE, _ACTIVADOR_DE_MARKETPLACE)
    yield
