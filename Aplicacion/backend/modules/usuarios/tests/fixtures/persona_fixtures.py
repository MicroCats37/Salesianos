"""
Fixtures reales del módulo `usuarios`.

`contract/TEST_ARCHITECTURE_CONTRACT.md` §3: las fixtures viven en
`fixtures/` y el `conftest.py` sólo las importa.

La fuente externa de documentos se sustituye por un DOBLE que se inyecta por
el grafo de fixtures (el puerto `IConsultaDocumentoClient` se re-vincula en
el inyector). Prohibido `unittest.mock.patch`
(`contract/TEST_ARCHITECTURE_CONTRACT.md` §6).
"""

import pytest
from injector import Binder, Module
from ninja_extra.dependency_resolver import register_injector_modules

from modules.usuarios.di import UsuariosModule
from modules.usuarios.domain.constants import (
    EstadoConsultaDocumentoChoices,
    GrupoFuncionalChoices,
)
from modules.usuarios.domain.models import Persona, Usuario
from modules.usuarios.domain.ports import IConsultaDocumentoClient
from modules.usuarios.domain.results import ConsultaDocumentoResultado
from modules.usuarios.domain.services.core.grupo_service import GrupoFuncionalService


class ConsultaDocumentoClientFalso(IConsultaDocumentoClient):
    """Doble de la fuente externa de documentos.

    Registra las consultas recibidas y devuelve el estado configurado. Es el
    mecanismo de aislamiento: no hay mocks, hay un doble por el puerto.
    """

    def __init__(self, resultado: ConsultaDocumentoResultado | None = None):
        self.resultado = resultado
        self.llamadas: list[str] = []

    async def consultar(self, numero_documento: str) -> ConsultaDocumentoResultado:
        self.llamadas.append(numero_documento)
        if self.resultado is not None:
            return self.resultado
        return ConsultaDocumentoResultado(
            estado=EstadoConsultaDocumentoChoices.NO_ENCONTRADO,
            numero_documento=numero_documento,
        )


def construir_resultado_externo(
    estado: EstadoConsultaDocumentoChoices = EstadoConsultaDocumentoChoices.ENCONTRADO,
    tipo_documento: str = "DNI",
    numero_documento: str = "12345678",
    nombre_completo: str = "PEREZ, ANA",
) -> ConsultaDocumentoResultado:
    """Construye el resultado tipado de la fuente externa."""
    return ConsultaDocumentoResultado(
        estado=estado,
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
        nombre_completo=nombre_completo,
    )


async def contar_personas() -> int:
    """Cuenta las personas desde un contexto async.

    Django prohíbe el ORM síncrono dentro de un contexto async: la cuenta
    va por `sync_to_async`.
    """
    from asgiref.sync import sync_to_async

    return await sync_to_async(Persona.objects.count)()


async def contar_usuarios() -> int:
    """Cuenta las cuentas desde un contexto async."""
    from asgiref.sync import sync_to_async

    return await sync_to_async(Usuario.objects.count)()


async def contar_personas_por_documento(numero_documento: str) -> int:
    """Cuenta las personas con ese documento desde un contexto async."""
    from asgiref.sync import sync_to_async

    return await sync_to_async(
        Persona.objects.filter(numero_documento=numero_documento).count
    )()


def _revincular_puerto(interfaz, instancia) -> None:
    """Re-vincula un puerto del inyector a una instancia concreta."""

    class _Modulo(Module):
        def configure(self, binder: Binder) -> None:
            binder.bind(interfaz, to=instancia)

    register_injector_modules(_Modulo())


# ── Fuente externa ──────────────────────────────────────────────────────────


@pytest.fixture
def consulta_documento_client():
    """Doble de la fuente externa, inyectado por el puerto."""
    cliente = ConsultaDocumentoClientFalso()
    _revincular_puerto(IConsultaDocumentoClient, cliente)
    yield cliente
    register_injector_modules(UsuariosModule())


# ── Identidad y cuentas ────────────────────────────────────────────────────


@pytest.fixture
def persona_creada(db):
    """Una `Persona` sin cuenta (`FR-03` §1.1)."""
    return Persona.objects.create(
        tipo_documento="DNI",
        numero_documento="12345678",
        nombres="ANA",
        apellidos="PEREZ",
        genero="F",
    )


@pytest.fixture
def persona_registrada_sin_cuenta(db):
    """Una `Persona` registrada SIN cuenta (documento distinto)."""
    return Persona.objects.create(
        tipo_documento="DNI",
        numero_documento="44555666",
        nombres="CARLOS",
        apellidos="SINCUENTA",
        genero="M",
    )


@pytest.fixture
def cuenta_sin_persona(db):
    """Una cuenta técnica sin `Persona` (`FR-03` §1.2)."""
    return Usuario.objects.create_user(
        username="cuenta.tecnica",
        password="Prueba-12345",
        email=None,
    )


@pytest.fixture
def cuenta_con_persona(db, persona_creada):
    """Una cuenta vinculada a una `Persona`."""
    return Usuario.objects.create_user(
        username="ana.cuenta",
        password="Prueba-12345",
        email="ana.cuenta@example.com",
        persona_fk=persona_creada,
    )


@pytest.fixture
def usuario_normal(db, cuenta_con_persona):
    """Cuenta con el grupo funcional `Normal`."""
    GrupoFuncionalService().asignar_grupo(
        cuenta_con_persona,
        GrupoFuncionalChoices.NORMAL.value,
    )
    return cuenta_con_persona


@pytest.fixture
def usuario_administrador(db):
    """Cuenta con el grupo funcional `Administrador`."""
    persona = Persona.objects.create(
        tipo_documento="DNI",
        numero_documento="87654321",
        nombres="LUIS",
        apellidos="ADMIN",
    )
    usuario = Usuario.objects.create_user(
        username="ana.admin",
        password="Prueba-12345",
        email="ana.admin@example.com",
        persona_fk=persona,
    )
    GrupoFuncionalService().asignar_grupo(
        usuario,
        GrupoFuncionalChoices.ADMINISTRADOR.value,
    )
    return usuario


# ── Superficie HTTP ────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def api_usuarios():
    """API de prueba con el controller de identidad registrado.

    Es una API LOCAL del test: el registro real en `config/api.py` es de A0.

    El ÁMBITO es de SESIÓN a propósito: `ninja_extra` mantiene el
    `APIController` de una clase de controller en un estado GLOBAL. Si cada
    test crea su propia API, el registro vuelve a apuntar las rutas a la API
    anterior y el cliente deja resolverlas
    (`Cannot resolve "/personas/resolver"`). Con UNA sola API por sesión el
    estado global es consistente.

    El `urls_namespace` es único por proceso, igual que en `config/api.py`.
    """
    import uuid

    from core.exceptions import register_exception_handlers
    from ninja_extra import NinjaExtraAPI
    from ninja_jwt.authentication import JWTAuth

    from modules.usuarios.presentation.controllers import PersonaController

    api = NinjaExtraAPI(
        urls_namespace=f"usuarios-test-{uuid.uuid4().hex[:8]}",
        auth=JWTAuth(),
    )
    register_exception_handlers(api)
    api.register_controllers(PersonaController)
    return api


@pytest.fixture
def api_client(api_usuarios):
    """Cliente asíncrono del módulo (`ninja_extra.testing.TestAsyncClient`).

    `ninja_extra.testing.TestAsyncClient.request` NO fusiona `self.headers`
    con los encabezados por petición (a diferencia de
    `ninja.testing.TestClient`): los fusiona esta subclase para que la
    cabecera `Authorization` llegue a la vista.
    """
    from ninja_extra.testing import TestAsyncClient

    class ClienteUsuarios(TestAsyncClient):
        """Cliente que sí propaga los encabezados por petición."""

        def request(self, method, path, data=None, json=None, **request_params):
            headers = {
                **self.headers,
                **request_params.pop("headers", {}),
            }
            if headers:
                request_params["headers"] = headers
            return super().request(
                method,
                path,
                data=data,
                json=json,
                **request_params,
            )

    return ClienteUsuarios(api_usuarios)


@pytest.fixture
def auth_client(api_client, usuario_normal):
    """Cliente asíncrono con sesión JWT de una cuenta `Normal`."""
    from ninja_jwt.tokens import AccessToken

    token = AccessToken.for_user(usuario_normal)
    api_client.headers.update({"Authorization": f"Bearer {token}"})
    api_client.user = usuario_normal
    return api_client


__all__ = [
    "ConsultaDocumentoClientFalso",
    "api_client",
    "api_usuarios",
    "auth_client",
    "construir_resultado_externo",
    "consulta_documento_client",
    "cuenta_con_persona",
    "cuenta_sin_persona",
    "persona_creada",
    "usuario_administrador",
    "usuario_normal",
]
