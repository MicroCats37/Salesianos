"""
Identidad civil y cuentas.

GIVEN: la identidad civil (`Persona`) y la cuenta (`Usuario`) son entidades
INDEPENDIENTES.
WHEN: se registran personas y cuentas.
THEN: la `Persona` existe sin cuenta, la cuenta existe sin `Persona`, el
documento es único por tipo y el resolver NO nace cuentas.

Cubre `FR-03` §1.1, §1.2 · `RN-U01`, `RN-U02` · `DEC-02`.
"""

import pytest
from django.db import IntegrityError

from modules.usuarios.domain.constants import GrupoFuncionalChoices
from modules.usuarios.domain.models import Persona, Usuario
from modules.usuarios.domain.services.core.grupo_service import GrupoFuncionalService
from modules.usuarios.tests.fixtures.factories import make_persona_payload


@pytest.mark.django_db(transaction=True)
def test_persona_puede_existir_sin_cuenta(persona_creada):
    """GIVEN una persona sin cuenta · WHEN se consulta · THEN no hay cuenta."""
    from modules.usuarios.domain.selectors import UsuarioSelector

    assert Persona.objects.count() == 1
    assert Usuario.objects.count() == 0
    assert UsuarioSelector().obtener_por_persona(str(persona_creada.id)) is None


@pytest.mark.django_db(transaction=True)
def test_cuenta_puede_existir_sin_persona(cuenta_sin_persona):
    """GIVEN una cuenta técnica · WHEN se consulta · THEN no tiene persona."""
    assert cuenta_sin_persona.persona_fk is None
    assert Usuario.objects.count() == 1
    assert Persona.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_persona_es_unica_por_tipo_y_numero(persona_creada):
    """GIVEN una persona registrada · WHEN se repite el documento · THEN la
    base de datos lo rechaza."""
    payload = make_persona_payload(nombres="OTRO")

    with pytest.raises(IntegrityError):
        Persona.objects.create(**payload)


@pytest.mark.django_db(transaction=True)
def test_mismo_documento_en_distinto_tipo_es_otra_persona(persona_creada):
    """GIVEN un DNI · WHEN se registra el mismo número como CE · THEN son
    personas distintas (`FR-03` §1.1 — la clave es el par completo)."""
    persona_ce = Persona.objects.create(
        tipo_documento="CE",
        numero_documento=persona_creada.numero_documento,
        nombres="ANA",
        apellidos="PEREZ",
    )

    assert persona_ce.id != persona_creada.id
    assert Persona.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_documento_se_normaliza_para_la_comparacion(persona_creada):
    """GIVEN un documento con espacios y guiones · WHEN se busca · THEN
    encuentra la misma persona (`FR-03` §1.1 — comparación sin separadores)."""
    from modules.usuarios.domain.selectors import PersonaSelector

    selector = PersonaSelector()
    encontrada = selector.obtener_por_documento("DNI", "12 345-678")

    assert encontrada is not None
    assert encontrada.id == persona_creada.id


@pytest.mark.django_db(transaction=True)
async def test_resolver_no_nace_una_cuenta(
    db,
    consulta_documento_client,
):
    """GIVEN una consulta de documento · WHEN se resuelve · THEN no se crea
    ninguna cuenta (`FR-03` §1.2 — el nacimiento de cuenta es explícito)."""
    from ninja_extra.dependency_resolver import get_injector

    from modules.usuarios.domain.constants import EstadoConsultaDocumentoChoices
    from modules.usuarios.domain.services.orchestrators.persona_orchestrator import (
        PersonaOrchestrator,
    )
    from modules.usuarios.tests.fixtures.persona_fixtures import (
        construir_resultado_externo,
        contar_personas,
        contar_usuarios,
    )

    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.ENCONTRADO,
        numero_documento="87654321",
    )

    orchestrator = get_injector().get(PersonaOrchestrator)
    resultado = await orchestrator.resolver("DNI", "87654321")

    assert resultado.origen.value == "EXTERNO"
    assert await contar_usuarios() == 0
    assert await contar_personas() == 0


@pytest.mark.django_db(transaction=True)
def test_grupo_normal_no_es_administrador(cuenta_con_persona):
    """GIVEN una cuenta con el grupo `Normal` · WHEN se consulta · THEN no
    administra (`FR-03` §1.2)."""
    servicio = GrupoFuncionalService()
    servicio.asignar_grupo(cuenta_con_persona, GrupoFuncionalChoices.NORMAL.value)

    assert servicio.es_normal(cuenta_con_persona) is True
    assert servicio.es_administrador(cuenta_con_persona) is False
    assert servicio.nivel_rol(cuenta_con_persona) == "normal"


@pytest.mark.django_db(transaction=True)
def test_grupo_administrador_administra(usuario_administrador):
    """GIVEN una cuenta con el grupo `Administrador` · WHEN se consulta ·
    THEN administra (`FR-03` §1.2)."""
    servicio = GrupoFuncionalService()

    assert servicio.es_administrador(usuario_administrador) is True
    assert servicio.es_normal(usuario_administrador) is False
    assert servicio.nivel_rol(usuario_administrador) == "administrador"


@pytest.mark.django_db(transaction=True)
def test_superusuario_es_nivel_tecnico_no_rol_de_negocio(cuenta_sin_persona):
    """GIVEN una cuenta con `is_superuser` · WHEN se consulta · THEN el nivel
    técnico resuelve todo (`DEC-02`)."""
    cuenta_sin_persona.is_superuser = True
    cuenta_sin_persona.save(update_fields=["is_superuser"])

    servicio = GrupoFuncionalService()

    assert servicio.es_administrador(cuenta_sin_persona) is True
    assert servicio.nivel_rol(cuenta_sin_persona) == "administrador"
    # El superusuario NO tiene un rol de negocio asignado.
    assert GrupoFuncionalChoices.ADMINISTRADOR.value not in servicio.grupos_de(
        cuenta_sin_persona
    )


@pytest.mark.django_db(transaction=True)
def test_solo_existen_dos_grupos_funcionales(usuario_normal, usuario_administrador):
    """GIVEN las cuentas con rol · WHEN se listan los grupos · THEN sólo
    existen `Normal` y `Administrador` (`FR-03` §1.2 — prohibido un tercer
    grupo por defecto)."""
    from django.contrib.auth.models import Group

    grupos = set(Group.objects.values_list("name", flat=True))

    assert grupos == {"Normal", "Administrador"}
