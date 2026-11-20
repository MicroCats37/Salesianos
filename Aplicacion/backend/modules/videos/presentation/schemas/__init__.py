"""Esquemas HTTP del módulo `videos`.

Change: `public-video-streaming-crud`

La versión del contrato del módulo la DECLARA el dueño aquí y la refleja el
registro global que mantiene A0 (`core/contract_versions.py`). El registro
global es de A0: la entrada `videos` = `1.0.0` queda registrada junto al
módulo y el test de drift (`core/tests/integration/test_contract_versions.py`)
la vigila.
"""

from .videos_schemas import (
    ActualizarVideoIn,
    CrearVideoIn,
    VideoListOut,
    VideoOut,
)

#: Versión del contrato HTTP del módulo.
SCHEMA_VERSION = "1.0.0"

__all__ = [
    "SCHEMA_VERSION",
    "ActualizarVideoIn",
    "CrearVideoIn",
    "VideoListOut",
    "VideoOut",
]
