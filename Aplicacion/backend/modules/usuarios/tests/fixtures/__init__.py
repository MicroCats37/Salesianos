"""Fixtures del módulo `usuarios`."""

from modules.usuarios.tests.fixtures.auth_fixtures import (  # noqa: F401
    cliente_con_sesion,
    cuenta_inactiva,
    superusuario_tecnico,
)
from modules.usuarios.tests.fixtures.persona_fixtures import (  # noqa: F401
    api_client,
    api_usuarios,
    auth_client,
    consulta_documento_client,
    cuenta_con_persona,
    cuenta_sin_persona,
    persona_creada,
    persona_registrada_sin_cuenta,
    usuario_administrador,
    usuario_normal,
)
