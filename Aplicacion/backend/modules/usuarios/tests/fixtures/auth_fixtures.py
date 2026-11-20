"""
Fixtures reales de autenticación y sesión del módulo `usuarios`.

`contract/TEST_ARCHITECTURE_CONTRACT.md` §3: las fixtures viven en
`fixtures/` y el `conftest.py` sólo las importa. Prohibido
`unittest.mock.patch` (§6): el aislamiento, cuando hace falta, es un doble
por el grafo de fixtures.

Estas fixtures usan la API LOCAL del módulo (la `api_usuarios` de
`persona_fixtures.py`), que registra los controllers de `usuarios` con una
única instancia por SESIÓN: `ninja_extra` mantiene el `APIController` de una
clase de controller en estado GLOBAL, así que una API por test re-apuntaría
las rutas a la API anterior (F-18 / F-40).
"""

import pytest
from ninja_jwt.tokens import AccessToken

from modules.usuarios.domain.models import Usuario


@pytest.fixture
def cuenta_inactiva(db, cuenta_con_persona):
    """Cuenta DESACTIVADA con su persona vinculada.

    Es un estado DISTINTO de "credenciales inválidas": la contraseña es
    correcta, pero la cuenta no puede operar.
    """
    cuenta_con_persona.is_active = False
    cuenta_con_persona.save()
    return cuenta_con_persona


@pytest.fixture
def superusuario_tecnico(db):
    """Cuenta técnica de soporte: superusuario y SIN `Persona` vinculada.

    El superusuario es el nivel TÉCNICO (`DEC-02`), no un rol de negocio, y
    no tiene por qué tener persona (`FR-03` §1.2).
    """
    return Usuario.objects.create_superuser(
        username="soporte.tecnico",
        password="Prueba-12345",
    )


@pytest.fixture
def cliente_con_sesion(api_client):
    """Factory de cliente autenticado con el token de una cuenta concreta.

    `ninja_extra.testing.TestAsyncClient.request` NO fusiona `self.headers`
    con los encabezados por petición: los fusiona la subclase de la fixture
    `api_client`, así que la cabecera `Authorization` llega a la vista.
    """

    def _factory(usuario) -> object:
        token = AccessToken.for_user(usuario)
        api_client.headers.update({"Authorization": f"Bearer {token}"})
        api_client.user = usuario
        return api_client

    return _factory


__all__ = [
    "cliente_con_sesion",
    "cuenta_inactiva",
    "superusuario_tecnico",
]
