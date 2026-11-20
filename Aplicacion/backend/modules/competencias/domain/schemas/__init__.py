"""DTOs INTERNOS del módulo `competencias` (no son esquemas HTTP).

Contract: `contract/django-app-architecture-contract.md` §4.6

Los DTOs de `domain/schemas/` viajan entre el DOMINIO y la capa de
presentación. Los de `domain/results/` son la SALIDA de los servicios: el
presenter los proyecta a los esquemas HTTP.

Este archivo NO contiene esquemas HTTP: los de la capa HTTP viven en
`presentation/schemas/`.
"""

from modules.competencias.domain.schemas.competencias_schemas import (
    AvanceData,
    CompetenciaCreateData,
    CorreccionData,
    EncuentroActualizarData,
    EncuentroCreateData,
    EquipoCompetenciaCreateData,
    EquipoCompetenciaEditData,
    EquipoElegibleData,
    ResultadoEncuentroData,
    RondaCreateData,
)

__all__ = [
    "AvanceData",
    "CompetenciaCreateData",
    "CorreccionData",
    "EncuentroActualizarData",
    "EncuentroCreateData",
    "EquipoCompetenciaCreateData",
    "EquipoCompetenciaEditData",
    "EquipoElegibleData",
    "ResultadoEncuentroData",
    "RondaCreateData",
]
