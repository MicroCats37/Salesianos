"""Domain results for salesianos_fest module."""
from .inscripcion_results import (
    InscripcionResult,
    InscripcionDetailResult,
    EquipoResult,
    InscripcionPersonaResult,
    ParticipacionResult,
)
from .compra_results import (
    CompraCreatedResult,
    CompraIzipayPreparedResult,
    CompraConfirmedResult,
)
from .catalogo_results import (
    DisciplinaResult,
    PromocionResult,
    CategoriaResult,
    PaquetePrecioResult,
    PaqueteBeneficioResult,
    PaqueteDisciplinaResult,
    PaqueteResult,
    PaqueteListResult,
)
from .asignacion_results import (
    AsignacionCupoCreatedResult,
    AsignacionCupoLiberadaResult,
)
from .acreditacion_results import (
    AcreditacionResult,
    OverrideFiestaResult,
    AccesoRegistradoResult,
)

__all__ = [
    "InscripcionResult",
    "InscripcionDetailResult",
    "EquipoResult",
    "InscripcionPersonaResult",
    "ParticipacionResult",
    "CompraCreatedResult",
    "CompraIzipayPreparedResult",
    "CompraConfirmedResult",
    "DisciplinaResult",
    "PromocionResult",
    "CategoriaResult",
    "PaquetePrecioResult",
    "PaqueteBeneficioResult",
    "PaqueteDisciplinaResult",
    "PaqueteResult",
    "PaqueteListResult",
    "AsignacionCupoCreatedResult",
    "AsignacionCupoLiberadaResult",
    "AcreditacionResult",
    "OverrideFiestaResult",
    "AccesoRegistradoResult",
]
