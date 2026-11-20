"""Esquemas HTTP del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

La versión del contrato del módulo la DECLARA el dueño aquí y la refleja el
registro global que mantiene A0 (`core/contract_versions.py`). El registro
global es de A0: la entrada `administracion` = `1.0.0` quedó registrada en la
reconciliación A0 de XCT-02 (2026-11-20 · lote D2) y el test de drift
(`core/tests/integration/test_contract_versions.py`) la vigila.
"""

from .admin_auditoria_schemas import AuditoriaItemOut, AuditoriaListadoOut
from .admin_operacion_schemas import (
    AccionOperativaOut,
    AdminEquipoDetalleOut,
    AdminEquipoListItemOut,
    AdminInscripcionDetalleOut,
    AdminInscripcionListItemOut,
    AdminPagoDetalleOut,
    AdminPagoListItemOut,
    AdminPersonaDetalleOut,
    AdminPersonaListItemOut,
    CandidatoAEquipoOut,
    CausaOut,
    CompraDeCuposOut,
    CompraOut,
    CompradorOut,
    CuposOperativosOut,
    EntregaDerechosOut,
    EquipoDeInscripcionOut,
    EstadoOperativoOut,
    EventoHistorialAdminOut,
    EventoHistorialOut,
    InscripcionDetalleEquipoOut,
    IntentoPagoOut,
    OperacionManualOut,
    ParticipacionAdminOut,
    ParticipacionPoolOut,
    ParticipanteAdminOut,
    ParticipanteDeEquipoOut,
    PersonaOut,
    PlantillaEquipoOut,
    PoolOut,
    ReferenciaOut,
    RetirarParticipanteIn,
)
from .admin_resumen_schemas import (
    ResumenAccionOut,
    ResumenIncidenciaOut,
    ResumenMetricaOut,
    ResumenOperativoOut,
)

#: Versión del contrato HTTP del módulo.
SCHEMA_VERSION = "1.0.0"

__all__ = [
    "SCHEMA_VERSION",
    "AccionOperativaOut",
    "AdminEquipoDetalleOut",
    "AdminEquipoListItemOut",
    "AdminInscripcionDetalleOut",
    "AdminInscripcionListItemOut",
    "AdminPagoDetalleOut",
    "AdminPagoListItemOut",
    "AdminPersonaDetalleOut",
    "AdminPersonaListItemOut",
    "AuditoriaItemOut",
    "AuditoriaListadoOut",
    "CandidatoAEquipoOut",
    "CausaOut",
    "CompraDeCuposOut",
    "CompraOut",
    "CompradorOut",
    "CuposOperativosOut",
    "EntregaDerechosOut",
    "EquipoDeInscripcionOut",
    "EstadoOperativoOut",
    "EventoHistorialAdminOut",
    "EventoHistorialOut",
    "InscripcionDetalleEquipoOut",
    "IntentoPagoOut",
    "OperacionManualOut",
    "ParticipacionAdminOut",
    "ParticipacionPoolOut",
    "ParticipanteAdminOut",
    "ParticipanteDeEquipoOut",
    "PersonaOut",
    "PlantillaEquipoOut",
    "PoolOut",
    "ReferenciaOut",
    "ResumenAccionOut",
    "ResumenIncidenciaOut",
    "ResumenMetricaOut",
    "ResumenOperativoOut",
    "RetirarParticipanteIn",
]
