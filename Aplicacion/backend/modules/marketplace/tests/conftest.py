"""Registro de fixtures del módulo `marketplace`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Este `conftest.py` sólo importa y registra los módulos de fixtures; las
fixtures reales viven en `fixtures/`.
"""

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
