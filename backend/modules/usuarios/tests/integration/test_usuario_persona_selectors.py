"""
Integration tests — UsuarioSelector and PersonaSelector (read-only query
surface of the usuarios module).

These selectors give the operational administration surface a way to list
accounts and people without importing anything from `presentation/`.
"""
import uuid

import pytest

from modules.usuarios.domain.models import Persona, Usuario
from modules.usuarios.domain.selectors import PersonaSelector, UsuarioSelector


def _documento_unico() -> str:
    """Return a unique 8-digit document number.

    `Persona` has a UNIQUE constraint on (tipo_documento, numero_documento) and
    some tests of this module run in transaction mode (their rows survive the
    rollback), so the document number must not be hardcoded.
    """
    return f"{uuid.uuid4().int % 100000000:08d}"


@pytest.fixture
def persona(db):
    """Persona of the test."""
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento=_documento_unico(),
        genero="M",
    )


@pytest.fixture
def usuario(db, persona):
    """Account linked to the persona."""
    return Usuario.objects.create_user(
        username="jperez",
        email="jperez@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def usuario_admin(db):
    """Administrator account (`is_staff`)."""
    admin_persona = Persona.objects.create(
        nombres="Ana",
        apellidos="Rojas",
        tipo_documento="DNI",
        numero_documento=_documento_unico(),
        genero="F",
    )
    admin = Usuario.objects.create_user(
        username="arojas",
        email="arojas@example.com",
        password="testpass123",
        persona_fk=admin_persona,
        is_staff=True,
    )
    return admin


@pytest.fixture
def usuario_selector():
    """The account selector."""
    return UsuarioSelector()


@pytest.fixture
def persona_selector():
    """The person selector."""
    return PersonaSelector()


# ── UsuarioSelector ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_usuario_obtener_por_id(usuario_selector, usuario):
    """GIVEN: an existing account WHEN: fetched by id THEN: it is returned."""
    assert usuario_selector.obtener_por_id(str(usuario.id)) == usuario


@pytest.mark.django_db
def test_usuario_obtener_por_id_desconocido(usuario_selector, db):
    """GIVEN: an unknown id WHEN: fetched THEN: None."""
    assert usuario_selector.obtener_por_id("00000000-0000-0000-0000-000000000000") is None


@pytest.mark.django_db
def test_usuario_obtener_por_username(usuario_selector, usuario):
    """GIVEN: an existing account WHEN: fetched by username THEN: it is returned."""
    assert usuario_selector.obtener_por_username("jperez") == usuario


@pytest.mark.django_db
def test_usuario_listar_devuelve_las_cuentas(usuario_selector, usuario, usuario_admin):
    """GIVEN: two accounts WHEN: listed THEN: both are returned."""
    resultado = list(usuario_selector.listar())

    assert usuario in resultado
    assert usuario_admin in resultado


@pytest.mark.django_db
def test_usuario_listar_filtra_por_activo(usuario_selector, usuario, usuario_admin):
    """GIVEN: a deactivated account WHEN: listed as active THEN: it is excluded."""
    usuario.is_active = False
    usuario.save(update_fields=["is_active"])

    activos = list(usuario_selector.listar(activo=True))
    inactivos = list(usuario_selector.listar(activo=False))

    assert usuario_admin in activos
    assert usuario not in activos
    assert usuario in inactivos


@pytest.mark.django_db
def test_usuario_listar_filtra_por_es_admin(
    usuario_selector, usuario, usuario_admin
):
    """
    GIVEN: one administrator and one regular account
    WHEN:  filtered by the admin rule (`is_staff OR is_superuser`)
    THEN:  each filter returns the right population.
    """
    admins = list(usuario_selector.listar(es_admin=True))
    no_admins = list(usuario_selector.listar(es_admin=False))

    assert usuario_admin in admins
    assert usuario not in admins
    assert usuario in no_admins
    assert usuario_admin not in no_admins


@pytest.mark.django_db
def test_usuario_listar_es_admin_incluye_superusuario(
    usuario_selector, usuario, usuario_admin
):
    """
    GIVEN: a superuser
    WHEN:  filtered by the admin rule
    THEN:  the superuser IS an admin (the rule is `is_staff OR is_superuser`).
    """
    superusuario = Usuario.objects.create_superuser(
        username="root",
        email="root@example.com",
        password="testpass123",
        persona_fk=Persona.objects.create(
            nombres="Root",
            apellidos="Sistema",
            tipo_documento="DNI",
            numero_documento=_documento_unico(),
            genero="M",
        ),
    )

    admins = list(usuario_selector.listar(es_admin=True))

    assert superusuario in admins
    assert usuario_admin in admins
    assert usuario not in admins


@pytest.mark.django_db
def test_usuario_listar_busca_por_username(usuario_selector, usuario, usuario_admin):
    """GIVEN: two accounts WHEN: searched by username THEN: only one matches."""
    resultado = list(usuario_selector.listar(q="jperez"))

    assert usuario in resultado
    assert usuario_admin not in resultado


@pytest.mark.django_db
def test_usuario_listar_busca_por_nombre_de_la_persona(
    usuario_selector, usuario, usuario_admin
):
    """GIVEN: two accounts WHEN: searched by the name of the linked person."""
    resultado = list(usuario_selector.listar(q="Rojas"))

    assert usuario_admin in resultado
    assert usuario not in resultado


@pytest.mark.django_db
def test_usuario_listar_busca_por_documento(
    usuario_selector, usuario, usuario_admin
):
    """GIVEN: two accounts WHEN: searched by the document of the linked person."""
    documento = usuario_admin.persona_fk.numero_documento

    assert list(usuario_selector.listar(q=documento)) == [usuario_admin]


@pytest.mark.django_db
def test_usuario_listar_busca_por_email(usuario_selector, usuario, usuario_admin):
    """GIVEN: two accounts WHEN: searched by email THEN: only one matches."""
    resultado = list(usuario_selector.listar(q="jperez@example.com"))

    assert usuario in resultado
    assert usuario_admin not in resultado


@pytest.mark.django_db
def test_usuario_listar_ignora_un_termino_sin_coincidencia(
    usuario_selector, usuario, usuario_admin
):
    """GIVEN: a term that matches nothing WHEN: searched THEN: an empty result."""
    assert usuario_selector.listar(q="zzzz-no-existe").count() == 0


# ── PersonaSelector ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_persona_obtener_por_id(persona_selector, persona):
    """GIVEN: an existing person WHEN: fetched by id THEN: it is returned."""
    assert persona_selector.obtener_por_id(str(persona.id)) == persona


@pytest.mark.django_db
def test_persona_obtener_por_id_desconocido(persona_selector, db):
    """GIVEN: an unknown id WHEN: fetched THEN: None."""
    assert persona_selector.obtener_por_id("00000000-0000-0000-0000-000000000000") is None


@pytest.mark.django_db
def test_persona_obtener_por_documento(persona_selector, persona):
    """GIVEN: an existing person WHEN: fetched by civil identity THEN: it is returned."""
    assert (
        persona_selector.obtener_por_documento("DNI", persona.numero_documento)
        == persona
    )


@pytest.mark.django_db
def test_persona_obtener_por_documento_inexistente(persona_selector, db):
    """GIVEN: an unknown document WHEN: fetched THEN: None."""
    assert persona_selector.obtener_por_documento("DNI", "00000000") is None


@pytest.mark.django_db
def test_persona_listar_busca_por_nombres(persona_selector, persona):
    """GIVEN: a person WHEN: searched by first name THEN: it is returned."""
    assert persona in list(persona_selector.listar(q="Juan"))


@pytest.mark.django_db
def test_persona_listar_busca_por_apellidos(persona_selector, persona):
    """GIVEN: a person WHEN: searched by last name THEN: it is returned."""
    assert persona in list(persona_selector.listar(q="Pérez"))


@pytest.mark.django_db
def test_persona_listar_busca_por_documento(persona_selector, persona):
    """GIVEN: a person WHEN: searched by document THEN: it is returned."""
    assert persona in list(persona_selector.listar(q=persona.numero_documento))


@pytest.mark.django_db
def test_persona_listar_sin_termino_devuelve_todas(persona_selector, persona):
    """GIVEN: no search term WHEN: listed THEN: every person is returned."""
    assert persona in list(persona_selector.listar())
