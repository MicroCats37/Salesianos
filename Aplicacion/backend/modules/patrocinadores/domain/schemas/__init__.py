"""DTOs internos del módulo `patrocinadores`.

Contract: `contract/django-app-architecture-contract.md` §4.6 (DTOs internos)
"""

from modules.patrocinadores.domain.schemas.patrocinadores_schemas import (
    ArchivoPatrocinadorUploadData,
    ImagenPatrocinadorData,
    LogoPatrocinadorData,
    PatrocinadorCreateData,
    PatrocinadorOrdenImagenData,
    PatrocinadorUpdateData,
)

__all__ = [
    "ArchivoPatrocinadorUploadData",
    "ImagenPatrocinadorData",
    "LogoPatrocinadorData",
    "PatrocinadorCreateData",
    "PatrocinadorOrdenImagenData",
    "PatrocinadorUpdateData",
]
