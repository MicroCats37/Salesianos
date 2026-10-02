"""
Shared fixtures index for inscripciones integration tests.

Re-exports all fixtures from fixtures/ subpackage for pytest discovery.

Factories (make_payload_*) are NOT re-exported — import directly:
    from modules.inscripciones.tests.fixtures.factories import make_inscripcion_payload
"""
from modules.inscripciones.tests.fixtures.usuarios_fixtures import (
    api_client,
    create_user,
    auth_client,
    usuario_admin,
)
from modules.inscripciones.tests.fixtures.inscripciones_fixtures import (
    disciplina_futbol,
    disciplina_basket,
    categoria_senior,
    categoria_junior,
    paquete_basic,
    paquete_disciplina_futbol,
    evento_activo,
    promocion_test,
    persona_simple,
    usuario_con_persona,
    auth_client_con_persona,
    base_inscripcion_setup,
)
