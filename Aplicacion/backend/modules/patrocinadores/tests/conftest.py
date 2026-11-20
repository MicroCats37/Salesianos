"""Registro de fixtures del módulo `patrocinadores`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Este `conftest.py` sólo importa y registra los módulos de fixtures; las
fixtures reales viven en `fixtures/`.
"""

from modules.patrocinadores.tests.fixtures.patrocinadores_fixtures import (  # noqa: F401
    archivo_grande,
    archivo_jpeg,
    archivo_mentiroso,
    archivo_png,
    edicion_otra,
    edicion_publicada,
    edicion_sin_patrocinadores,
    evento,
    media_root,
    patrocinador,
    token_admin,
    usuario_admin,
)
