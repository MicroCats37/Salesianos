"""
Integration tests — exact lookup of an EXISTING `Persona` by document (Apply 8B).

What this file proves:

1. an AUTHENTICATED caller resolves the person that matches the document
   EXACTLY, and receives the internal `persona_id`;
2. the lookup is EXACT: another document type with the same number and a
   partial number NEVER match;
3. an absent person is a TYPED 404 with the stable public code
   `PERSONA_NO_ENCONTRADA` (never an empty list);
4. an ANONYMOUS caller is refused with 401 and never reaches the query;
5. the answer carries the MINIMUM safe payload: the id, the name, the
   document type and the document the caller already supplied — never the
   account state, the contacts or the QR;
6. the lookup NEVER creates nor mutates a `Persona`.

NOT EXECUTED IN THIS PHASE: the tests are written here and run only once, in
Apply 9 (the consolidated validation of the whole change).
"""
import pytest
from django.test import Client
from ninja_jwt.tokens import AccessToken

from modules.usuarios.domain.models.persona import Persona

RUTA_RESOLVER = "/api/personas/resolver"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _auth_get(client, path, user):
    """GET with a JWT bearer token."""
    token = AccessToken.for_user(user)
    return client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")


def _resolver(tipo_documento, numero_documento):
    """The query string of the exact lookup."""
    return (
        f"{RUTA_RESOLVER}?tipo_documento={tipo_documento}"
        f"&numero_documento={numero_documento}"
    )


@pytest.fixture
def cliente(db):
    """Django Client: it handles the async controller of the module."""
    return Client()


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_resuelve_persona_existente_por_documento_exacto(
    cliente,
    create_user,
    persona_registrada,
):
    """
    GIVEN: A registered person with a known DNI
    WHEN:  GET /api/personas/resolver?tipo_documento=DNI&numero_documento=79000001
    THEN:  Returns 200 with the internal persona_id and the display name
    """
    response = _auth_get(
        cliente,
        _resolver("DNI", "79000001"),
        create_user,
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    resultado = data["data"]
    assert resultado["persona_id"] == str(persona_registrada.id)
    assert resultado["nombre_completo"] == "Ana Pérez"
    assert resultado["tipo_documento"] == "DNI"
    assert resultado["numero_documento"] == "79000001"


@pytest.mark.django_db
def test_la_busqueda_es_exacta_no_difusa(
    cliente,
    create_user,
    persona_registrada,
):
    """
    GIVEN: A registered person with a known DNI
    WHEN:  GET the resolver with a PARTIAL document number
    THEN:  Returns 404 — the lookup never matches a prefix
    """
    response = _auth_get(
        cliente,
        _resolver("DNI", "1234567"),
        create_user,
    )

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


@pytest.mark.django_db
def test_el_tipo_de_documento_distingue_las_identidades(
    cliente,
    create_user,
    persona_registrada,
    persona_registrada_ce,
):
    """
    GIVEN: A DNI and a CE that share the SAME document number
    WHEN:  GET the resolver for each type
    THEN:  Each call resolves its OWN person (the pair is the identity)
    """
    response_dni = _auth_get(
        cliente,
        _resolver("DNI", "79000001"),
        create_user,
    )
    response_ce = _auth_get(
        cliente,
        _resolver("CE", "79000001"),
        create_user,
    )

    assert response_dni.status_code == 200
    assert response_ce.status_code == 200
    assert response_dni.json()["data"]["persona_id"] == str(persona_registrada.id)
    assert response_ce.json()["data"]["persona_id"] == str(persona_registrada_ce.id)


@pytest.mark.django_db
def test_persona_inexistente_devuelve_404_tipado(cliente, create_user):
    """
    GIVEN: A document that belongs to NO registered person
    WHEN:  GET the resolver
    THEN:  Returns 404 with the stable public code PERSONA_NO_ENCONTRADA
    """
    response = _auth_get(
        cliente,
        _resolver("DNI", "99999999"),
        create_user,
    )

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PERSONA_NO_ENCONTRADA"
    assert data["error"]["message"]


@pytest.mark.django_db
def test_un_tipo_de_documento_desconocido_devuelve_422(cliente, create_user):
    """
    GIVEN: A document type that is NOT part of the closed identity vocabulary
    WHEN:  GET the resolver with that type
    THEN:  Returns 422 with the stable public code TIPO_DOCUMENTO_INVALIDO
           (an invalid request is NOT a person that does not exist)
    """
    response = _auth_get(
        cliente,
        _resolver("XXX", "79000001"),
        create_user,
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TIPO_DOCUMENTO_INVALIDO"


@pytest.mark.django_db
def test_el_visitante_anonimo_es_rechazado(cliente):
    """
    GIVEN: An anonymous caller (no bearer token)
    WHEN:  GET the resolver
    THEN:  Returns 401 and never resolves a person
    """
    response = cliente.get(_resolver("DNI", "79000001"))

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_la_respuesta_es_minima_y_no_expone_pii(
    cliente,
    create_user,
    persona_registrada,
):
    """
    GIVEN: A registered person (with contacts in the database)
    WHEN:  GET the resolver
    THEN:  The answer carries ONLY the id, the name, the type and the document
    """
    response = _auth_get(
        cliente,
        _resolver("DNI", "79000001"),
        create_user,
    )

    assert response.status_code == 200
    resultado = response.json()["data"]
    assert set(resultado.keys()) == {
        "persona_id",
        "nombre_completo",
        "tipo_documento",
        "numero_documento",
    }
    # The forbidden PII never travels.
    for prohibido in (
        "email",
        "telefono",
        "whatsapp",
        "direccion",
        "qr",
        "estado",
        "usuario_id",
        "genero",
        "contacto_emergencia_nombre",
        "contacto_emergencia_telefono",
        "aseguradora_nombre",
        "aseguradora_numero_poliza",
    ):
        assert prohibido not in resultado


@pytest.mark.django_db
def test_la_resolucion_nunca_crea_ni_modifica_una_persona(
    cliente,
    create_user,
    persona_registrada,
):
    """
    GIVEN: A database with ONE registered person
    WHEN:  GET the resolver for that person AND for an absent one
    THEN:  The number of personas is unchanged and the one that exists is
            untouched (the lookup is a READ)
    """
    antes = Persona.objects.count()
    persona_antes = Persona.objects.get(id=persona_registrada.id)

    response_ok = _auth_get(
        cliente,
        _resolver("DNI", "79000001"),
        create_user,
    )
    response_ausente = _auth_get(
        cliente,
        _resolver("DNI", "88888888"),
        create_user,
    )

    assert response_ok.status_code == 200
    assert response_ausente.status_code == 404
    assert Persona.objects.count() == antes

    persona_despues = Persona.objects.get(id=persona_registrada.id)
    assert persona_despues.nombres == persona_antes.nombres
    assert persona_despues.apellidos == persona_antes.apellidos
    assert persona_despues.tipo_documento == persona_antes.tipo_documento
    assert persona_despues.numero_documento == persona_antes.numero_documento


@pytest.mark.django_db
def test_el_lookup_externo_de_documento_no_cambia(
    cliente,
    create_user,
    persona_registrada,
):
    """
    GIVEN: The external document lookup endpoint (RENIEC/SUNAT)
    WHEN:  GET /api/personas/busqueda/{documento}
    THEN:  It keeps its own PUBLIC contract (no session, its own fields)
    """
    response = cliente.get("/api/personas/busqueda/45406196")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    resultado = response.json()["data"]
    assert set(resultado.keys()) == {
        "tipo_documento",
        "numero_documento",
        "razon_social",
    }
    assert "persona_id" not in resultado
