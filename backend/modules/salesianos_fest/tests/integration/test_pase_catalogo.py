"""
Integration tests — independent party-pass catalogue (Apply 1).

What this file proves:

1. the catalogue of passes is INDEPENDENT from the sports catalogue — a pass
   never appears in `GET /api/catalogo/paquetes/` and the sports catalogue
   keeps its exact shape and rows;
2. the rollout flag, the ACTIVE event and the ACTIVE pass decide what is
   published — a disabled flag or the absence of an active pass expose NO
   purchasable entry;
3. only VIGENT prices are published as the effective price (the stage
   calendar is still exposed so the frontend can render it);
4. the models carry the guarantees the domain requires (unique evento+nombre,
   one ACTIVE price per stage).

NOT EXECUTED IN THIS PHASE: the tests are written here and run only once, in
Apply 9 (the consolidated validation of the whole change).
"""
from datetime import date
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction

from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.constants import EtapaChoices, TipoPaqueteChoices
from modules.salesianos_fest.domain.models import Pase, PasePrecio, Paquete

# ── Catálogo independiente: el flag gobierna la superficie ───────────────────


@pytest.mark.django_db
def test_catalogo_pases_vacio_con_flag_deshabilitado(api_client, pase_fiesta, settings):
    """
    GIVEN: el flag de despliegue está DESHABILITADO y existe un pase activo
    WHEN:  GET /api/pases/
    THEN:  200 con catálogo VACÍO — no se expone ninguna entrada comprable
    """
    settings.PASES_FIESTA_ENABLED = False

    response = api_client.get("/api/pases/")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.django_db
def test_catalogo_pases_publico_y_sin_autenticacion(api_client, pase_fiesta, settings):
    """
    GIVEN: el flag está habilitado y hay un pase activo
    WHEN:  GET /api/pases/ SIN cabecera de autenticación
    THEN:  200 — el catálogo es público
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.get("/api/pases/")

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.django_db
def test_catalogo_pases_publica_pase_activo_con_flag_habilitado(
    api_client, pase_fiesta, settings
):
    """
    GIVEN: el flag está habilitado, el evento es el activo y el pase está activo
    WHEN:  GET /api/pases/
    THEN:  200 con el pase publicado y su precio vigente
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.get("/api/pases/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1

    pase_out = data[0]
    assert pase_out["id"] == str(pase_fiesta.id)
    assert pase_out["evento_id"] == str(pase_fiesta.evento_id)
    assert pase_out["nombre"] == "Pase de Fiesta"
    assert pase_out["descripcion"] == "Acceso a la fiesta de cierre."
    assert pase_out["activo"] is True
    assert pase_out["cantidad_maxima"] == 0
    # PREVENTA vigente; REGULAR todavía no vigente.
    assert pase_out["precio_preventa"] == 25.0
    assert pase_out["precio_regular"] is None
    assert pase_out["precio_vigente"] == 25.0
    assert len(pase_out["precios"]) == 2


@pytest.mark.django_db
def test_catalogo_pases_omite_pases_inactivos(
    api_client, pase_fiesta, pase_inactivo, settings
):
    """
    GIVEN: un pase activo y otro inactivo del mismo evento
    WHEN:  GET /api/pases/
    THEN:  sólo se publica el pase ACTIVO
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.get("/api/pases/")

    data = response.json()["data"]
    nombres = {item["nombre"] for item in data}
    assert nombres == {"Pase de Fiesta"}
    assert "Pase Retirado" not in nombres


@pytest.mark.django_db
def test_catalogo_pases_omite_edicion_no_activa(
    api_client, pase_fiesta, pase_de_edicion_inactiva, settings
):
    """
    GIVEN: un pase activo de una edición que NO está activa
    WHEN:  GET /api/pases/
    THEN:  el pase de la edición inactiva NO se publica
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.get("/api/pases/")

    data = response.json()["data"]
    nombres = {item["nombre"] for item in data}
    assert nombres == {"Pase de Fiesta"}
    assert "Pase de la Edición Anterior" not in nombres


@pytest.mark.django_db
def test_catalogo_pases_vacio_sin_evento_activo(
    api_client, settings, evento_no_activo
):
    """
    GIVEN: el flag está habilitado pero NO hay ninguna edición activa
    WHEN:  GET /api/pases/
    THEN:  200 con catálogo VACÍO (no es un error)
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.get("/api/pases/")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


# ── Precios vigentes ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_catalogo_pases_solo_expone_precios_vigentes(
    api_client, pase_precios_fuera_de_ventana, settings
):
    """
    GIVEN: un pase activo cuyas dos etapas están fuera de su ventana
    WHEN:  GET /api/pases/
    THEN:  no hay precio vigente (precio_vigente=None) pero el calendario
           de etapas sigue publicado
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.get("/api/pases/")

    data = response.json()["data"]
    assert len(data) == 1
    pase_out = data[0]
    assert pase_out["precio_preventa"] is None
    assert pase_out["precio_regular"] is None
    assert pase_out["precio_vigente"] is None

    # El calendario de etapas se conserva: el frontend puede mostrarlo.
    assert len(pase_out["precios"]) == 2
    assert {p["etapa"] for p in pase_out["precios"]} == {"PREVENTA", "REGULAR"}


@pytest.mark.django_db
def test_catalogo_pases_pase_sin_precio_no_es_comprable(api_client, pase_sin_precio, settings):
    """
    GIVEN: un pase activo sin ninguna fila de precio
    WHEN:  GET /api/pases/
    THEN:  se publica con precio_vigente=None (no es comprable)
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.get("/api/pases/")

    data = response.json()["data"]
    assert len(data) == 1
    pase_out = data[0]
    assert pase_out["nombre"] == "Pase Sin Precio"
    assert pase_out["precio_vigente"] is None
    assert pase_out["precios"] == []


# ── Contrato HTTP ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_catalogo_pases_contrato_http(api_client, pase_fiesta, settings):
    """
    GIVEN: el flag está habilitado y hay un pase activo
    WHEN:  GET /api/pases/
    THEN:  la respuesta respeta el contrato de PaseListOut / PasePrecioOut
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.get("/api/pases/")

    pase_out = response.json()["data"][0]
    assert set(pase_out.keys()) == {
        "id",
        "evento_id",
        "nombre",
        "descripcion",
        "activo",
        "precio_preventa",
        "precio_regular",
        "precio_vigente",
        "cantidad_maxima",
        "precios",
    }
    assert isinstance(pase_out["precio_preventa"], float)
    assert isinstance(pase_out["cantidad_maxima"], int)

    precio_out = pase_out["precios"][0]
    assert set(precio_out.keys()) == {
        "etapa",
        "precio_unitario",
        "vigente_desde",
        "vigente_hasta",
    }
    assert isinstance(precio_out["precio_unitario"], float)
    assert precio_out["etapa"] in {"PREVENTA", "REGULAR"}


# ── No contamination del catálogo deportivo ──────────────────────────────────


@pytest.mark.django_db
def test_catalogo_pases_no_altera_catalogo_de_paquetes(
    api_client, pase_fiesta, paquete_reencuentro, paquete_futbol, settings
):
    """
    GIVEN: un pase activo y dos paquetes deportivos del mismo evento
    WHEN:  GET /api/catalogo/paquetes/
    THEN:  el catálogo deportivo NO cambia: mismos paquetes, mismos tipos y
           ninguna fila de tipo "PASE"
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.get("/api/catalogo/paquetes/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    nombres = {item["nombre"] for item in data}
    assert nombres == {"Reencuentro + Fiesta", "Fútbol 7 Masculino"}
    assert "Pase de Fiesta" not in nombres
    assert {item["tipo"] for item in data} <= {"PACK", "DISCIPLINA"}
    assert Paquete.objects.count() == 2
    assert Pase.objects.count() == 1


@pytest.mark.django_db
def test_paquete_no_admite_tipo_pase(api_client, settings):
    """
    GIVEN: el catálogo de paquetes deportivos
    WHEN:  se inspecciona el dominio del tipo de paquete
    THEN:  no existe un tipo "PASE" — el pase es un catálogo independiente
    """
    assert "PASE" not in [valor for valor, _ in TipoPaqueteChoices.choices]
    assert "PASE" not in dict(Paquete._meta.get_field("tipo").choices)
    assert Paquete.objects.filter(tipo="PASE").count() == 0


# ── Garantías del modelo ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_pase_unicidad_evento_nombre(db, evento):
    """
    GIVEN: un pase ya creado en el evento
    WHEN:  se crea otro pase con el MISMO nombre en el MISMO evento
    THEN:  la base de datos lo rechaza (unique evento+nombre)
    """
    Pase.objects.create(evento=evento, nombre="Pase Único", activo=True)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Pase.objects.create(evento=evento, nombre="Pase Único", activo=True)


@pytest.mark.django_db
def test_pase_precio_unicidad_activa_por_etapa(db, pase_fiesta):
    """
    GIVEN: un pase con un precio ACTIVO en preventa
    WHEN:  se crea otro precio ACTIVO de la misma etapa
    THEN:  la base de datos lo rechaza; un precio INACTIVO sí se permite
    """
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PasePrecio.objects.create(
                pase=pase_fiesta,
                etapa=EtapaChoices.PREVENTA,
                precio_unitario=Decimal("99.00"),
                vigente_desde=date.today(),
                activo=True,
            )

    inactivo = PasePrecio.objects.create(
        pase=pase_fiesta,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("99.00"),
        vigente_desde=date.today(),
        activo=False,
    )
    assert inactivo.pk is not None


# ── Seed del catálogo FEST ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_seed_catalogo_fest_crea_pase_inactivo_e_idempotente():
    """
    GIVEN: el seed del catálogo FEST
    WHEN:  se ejecuta dos veces
    THEN:  crea UN pase con precios PREVENTA/REGULAR, todo INACTIVO, sin
           duplicados
    """
    call_command("seed_catalogo_fest", stdout=StringIO())
    call_command("seed_catalogo_fest", stdout=StringIO())

    fest_evento = Evento.objects.get(nombre="Salesianos FEST 2026")

    passes = Pase.objects.filter(evento=fest_evento, nombre="Pase de Fiesta")
    assert passes.count() == 1
    pase = passes.get()
    assert pase.activo is False
    assert pase.cantidad_maxima == 0

    precios = PasePrecio.objects.filter(pase=pase)
    assert precios.count() == 2
    assert {p.etapa for p in precios} == {"PREVENTA", "REGULAR"}
    assert all(p.activo is False for p in precios)


@pytest.mark.django_db
def test_pase_sembrado_no_se_publica_sin_activacion(api_client, settings):
    """
    GIVEN: el seed ejecutado (pase INACTIVO) y el flag habilitado
    WHEN:  GET /api/pases/
    THEN:  el catálogo sigue vacío — el pase sembrado no se publica solo
    """
    settings.PASES_FIESTA_ENABLED = True
    call_command("seed_catalogo_fest", stdout=StringIO())

    response = api_client.get("/api/pases/")

    assert response.status_code == 200
    assert response.json()["data"] == []
