"""Integration tests for quotation endpoint and price revalidation."""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.test import Client
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import AccessToken

from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.models import (
    Paquete,
    PaquetePrecio,
    PaqueteBeneficio,
    Promocion,
    Disciplina,
    Categoria,
    PaqueteDisciplina,
)
from modules.salesianos_fest.domain.constants import (
    TipoPaqueteChoices,
    ModoDisciplinasChoices,
    EtapaChoices,
    TipoBeneficioChoices,
    AlcanceBeneficioChoices,
    ModoCalculoBeneficioChoices,
    ModalidadChoices,
)


# ─── Auth Helper ────────────────────────────────────────────────────────────────

def _auth_post(client, path, user, data=None):
    """Make an authenticated POST request with JWT."""
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=data,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(db):
    return Client()


@pytest.fixture
def evento(db):
    return Evento.objects.create(
        nombre="FEST Test 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def paquete_simple(db, evento):
    """Package with one active REGULAR price."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Pack Básico",
        descripcion="Pack básico de prueba",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=2,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("45.00"),
        vigente_desde=date.today(),
        vigente_hasta=None,
        activo=True,
    )
    PaqueteBeneficio.objects.create(
        paquete=paquete,
        tipo=TipoBeneficioChoices.FIESTA,
        cantidad=1,
        alcance=AlcanceBeneficioChoices.INDIVIDUAL,
        modo_calculo=ModoCalculoBeneficioChoices.FIJO_INICIAL,
    )
    return paquete


@pytest.fixture
def paquete_preventa(db, evento):
    """Package with active PREVENTA price (lower than REGULAR)."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Pack Preventa",
        descripcion="Pack en preventa",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=5,
        activo=True,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("30.00"),
        vigente_desde=date.today(),
        vigente_hasta=date(2026, 12, 31),
        activo=True,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("45.00"),
        vigente_desde=date(2026, 11, 1),
        vigente_hasta=None,
        activo=True,
    )
    return paquete


@pytest.fixture
def persona(db):
    from modules.usuarios.domain.models.persona import Persona
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def usuario_con_persona(db, persona):
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        password="testpass123",
        email="test@example.com",
        persona_fk=persona,
    )


@pytest.fixture
def promocion_test(db):
    return Promocion.objects.create(anio=2010, nombre="Prueba", activa=True)


# ── CotizacionEndpoint Tests ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cotizar_paquete_existente(api_client, paquete_simple):
    """
    GIVEN: un paquete activo con precio REGULAR de S/45.00
    WHEN: POST /api/cotizaciones/ con cantidad=12
    THEN: retorna 200 con precio_unitario=45.00, total=540.00
    """
    response = api_client.post(
        "/api/cotizaciones/",
        {"paquete_id": str(paquete_simple.id), "cantidad": 12},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    cotizacion = data["data"]
    assert cotizacion["paquete_id"] == str(paquete_simple.id)
    assert cotizacion["cantidad_cotizada"] == 12
    assert cotizacion["precio_unitario"] == 45.00
    assert cotizacion["total"] == 540.00
    assert cotizacion["estado"] == "ACTIVA"
    assert cotizacion["minimo_cantidad"] == 10


@pytest.mark.django_db
def test_cotizar_cantidad_igual_al_minimo(api_client, paquete_simple):
    """
    GIVEN: paquete con minimo_compra_inicial=10
    WHEN: POST /api/cotizaciones/ con cantidad=10 (exacta al mínimo)
    THEN: retorna 200 con total=450.00
    """
    response = api_client.post(
        "/api/cotizaciones/",
        {"paquete_id": str(paquete_simple.id), "cantidad": 10},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 450.00


@pytest.mark.django_db
def test_cotizar_cantidad_inferior_al_minimo(api_client, paquete_simple):
    """
    GIVEN: paquete con minimo_compra_inicial=10
    WHEN: POST /api/cotizaciones/ con cantidad=5
    THEN: retorna 409 con code=CANTIDAD_INSUFICIENTE
    """
    response = api_client.post(
        "/api/cotizaciones/",
        {"paquete_id": str(paquete_simple.id), "cantidad": 5},
        content_type="application/json",
    )
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "CANTIDAD_INSUFICIENTE"


@pytest.mark.django_db
def test_cotizar_paquete_inexistente(api_client):
    """
    GIVEN: un paquete_id que no existe
    WHEN: POST /api/cotizaciones/
    THEN: retorna 404 con code=PAQUETE_NOT_FOUND
    """
    response = api_client.post(
        "/api/cotizaciones/",
        {"paquete_id": "00000000-0000-0000-0000-000000000000", "cantidad": 10},
        content_type="application/json",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PAQUETE_NOT_FOUND"


@pytest.mark.django_db
def test_cotizar_devuelve_precios_de_referencia(api_client, paquete_preventa):
    """
    GIVEN: paquete con PREVENTA=S/30.00 (vigente hoy) y REGULAR=S/45.00 (futuro)
    WHEN: POST /api/cotizaciones/
    THEN: devuelve precio_unitario = precio de la etapa vigente por fecha
          (PREVENTA hoy, ya que su ventana incluye la fecha actual),
          y precio_preventa / precio_regular como referencia para la UI.

    NOTE: obtener_precio_vigente() filtra por rango de fechas
    (vigente_desde <= hoy AND (vigente_hasta IS NULL OR vigente_hasta >= hoy)).
    Cuando hay un único precio que cumple el rango, ese gana — NO el de
    mayor vigente_desde. La cotización incluye ambos precios para que la UI
    muestre el comparativo preventa vs regular independientemente.
    """
    response = api_client.post(
        "/api/cotizaciones/",
        {"paquete_id": str(paquete_preventa.id), "cantidad": 8},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    cotizacion = data["data"]
    # Both prices are returned for UI reference
    assert cotizacion["precio_preventa"] == 30.00
    assert cotizacion["precio_regular"] == 45.00
    # precio_unitario comes from the date-vigente price (PREVENTA, vigente hoy)
    assert cotizacion["precio_unitario"] == 30.00


@pytest.mark.django_db
def test_cotizar_validez_24_horas(api_client, paquete_simple):
    """
    GIVEN: un paquete activo
    WHEN: POST /api/cotizaciones/
    THEN: validez_hasta es aproximadamente 24h en el futuro
    """
    from datetime import datetime

    response = api_client.post(
        "/api/cotizaciones/",
        {"paquete_id": str(paquete_simple.id), "cantidad": 10},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    validez = data["data"]["validez_hasta"]
    # Parse as naive datetime (API returns UTC ISO string)
    validez_dt_naive = datetime.fromisoformat(validez.replace("Z", ""))
    # Compare with a naive "now" measured immediately after the API call
    # cotizacion_flujo uses datetime.now() (local time) so match that
    now_naive = datetime.now()
    delta = validez_dt_naive - now_naive
    # 24h = 86400s; allow generous tolerance for test timing
    assert 85000 <= delta.total_seconds() <= 88000


# ── Vigente Filter Tests (date-aware vigente price resolution) ─────────────────


@pytest.fixture
def paquete_sin_vigente(db, evento):
    """
    Paquete con PREVENTA ya vencida y REGULAR que aún no comienza.
    Hoy está en el gap entre ambas etapas → no hay precio vigente.
    """
    from modules.salesianos_fest.domain.models import Paquete
    from modules.salesianos_fest.domain.constants import (
        TipoPaqueteChoices,
        ModoDisciplinasChoices,
        EtapaChoices,
    )

    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Pack Sin Vigente",
        descripcion="Pack con gap de fechas",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=5,
        activo=True,
    )
    # PREVENTA: ya venció (hasta ayer)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("30.00"),
        vigente_desde=date.today() - timedelta(days=30),
        vigente_hasta=date.today() - timedelta(days=1),
        activo=True,
    )
    # REGULAR: aún no comienza (desde mañana)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("45.00"),
        vigente_desde=date.today() + timedelta(days=1),
        vigente_hasta=None,
        activo=True,
    )
    return paquete


@pytest.mark.django_db
def test_obtener_precio_vigente_respeta_fechas_no_fallback(
    api_client, paquete_sin_vigente
):
    """
    GIVEN: paquete con PREVENTA ya vencida y REGULAR futura
    WHEN: POST /api/cotizaciones/
    THEN: retorna 409 con code=PRECIO_NO_ENCONTRADO (NO cae al REGULAR futuro)

    El sistema NO debe devolver un precio que no está vigente hoy, aunque sea
    el "más reciente activo". Configurar el catálogo sin precio vigente es
    un error de configuración que debe gritar, no enmascararse.
    """
    response = api_client.post(
        "/api/cotizaciones/",
        {"paquete_id": str(paquete_sin_vigente.id), "cantidad": 5},
        content_type="application/json",
    )
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PRECIO_NO_ENCONTRADO"


# ── PrecioCambio Conflict Tests ────────────────────────────────────────────────


@pytest.mark.django_db
def test_inscripcion_precio_cotizado_incorrecto_rechazado(
    api_client, evento, paquete_simple, usuario_con_persona, promocion_test
):
    """
    GIVEN: paquete con precio vigente S/45.00
    WHEN: POST /api/inscripciones/completa/ con precio_unitario_cotizado=40.00
          (precio desactualizado, diferente al vigente)
    THEN: retorna 409 con code=PRECIO_CAMBIO
    """
    # Create required disciplina + categoria for the inscription flow
    disciplina = Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete_simple, disciplina=disciplina)
    Categoria.objects.create(
        evento=evento,
        nombre="Senior",
        promocion_desde=1990,
        promocion_hasta=2015,
        esta_activa=True,
    )

    response = _auth_post(
        api_client,
        "/api/inscripciones/completa/",
        usuario_con_persona,
        {
            "evento_id": str(evento.id),
            "paquete_id": str(paquete_simple.id),
            "promocion_id": str(promocion_test.id),
            "cantidad": 10,
            "equipos": [
                {
                    "disciplina_id": str(disciplina.id),
                    "nombre": "Equipo Test",
                    "estado": "EQUIPO_ACTIVO",
                }
            ],
            "estado": "BORRADOR",
            "observacion": "",
            "precio_unitario_cotizado": 40.00,  # WRONG — vigente is 45.00
        },
    )

    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PRECIO_CAMBIO"
    # The error message contains the price delta
    assert "40.00" in data["error"]["message"]
    assert "45.00" in data["error"]["message"]


@pytest.mark.django_db
def test_inscripcion_sin_precio_cotizado_no_rechaza(
    api_client, evento, paquete_simple, usuario_con_persona, promocion_test
):
    """
    GIVEN: paquete con precio vigente S/45.00
    WHEN: POST /api/inscripciones/completa/ SIN precio_unitario_cotizado
    THEN: no se ejecuta la revalidación de precio (acepta cualquier precio server-side)
         — la inscripción se crea si pasa todas las demás validaciones
    """
    disciplina = Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete_simple, disciplina=disciplina)
    Categoria.objects.create(
        evento=evento,
        nombre="Senior",
        promocion_desde=1990,
        promocion_hasta=2015,
        esta_activa=True,
    )

    response = _auth_post(
        api_client,
        "/api/inscripciones/completa/",
        usuario_con_persona,
        {
            "evento_id": str(evento.id),
            "paquete_id": str(paquete_simple.id),
            "promocion_id": str(promocion_test.id),
            "cantidad": 10,
            "equipos": [
                {
                    "disciplina_id": str(disciplina.id),
                    "nombre": "Equipo Test",
                    "estado": "EQUIPO_ACTIVO",
                }
            ],
            "estado": "BORRADOR",
            "observacion": "",
            # SIN precio_unitario_cotizado — no se ejecuta revalidación
        },
    )
    # Should NOT be 409 (PRECIO_CAMBIO)
    # May be 201 if all other validations pass, or 400/404 for other reasons
    if response.status_code == 409:
        data = response.json()
        assert data["error"]["code"] != "PRECIO_CAMBIO"
