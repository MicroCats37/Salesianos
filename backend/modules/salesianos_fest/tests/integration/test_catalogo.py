"""Integration tests for catalog endpoints."""
import pytest


@pytest.mark.django_db
def test_listar_disciplinas(api_client, disciplina_futbol_m, disciplina_futbol_f, disciplina_voley):
    """
    GIVEN: tres disciplinas activas en la base
    WHEN: GET /api/catalogo/disciplinas/
    THEN: retorna 200 con lista de disciplinas activas
    """
    response = api_client.get("/api/catalogo/disciplinas/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 3
    siglas = {item["sigla"] for item in data["data"]}
    assert "F7M" in siglas
    assert "F7F" in siglas
    assert "VOL" in siglas


@pytest.mark.django_db
def test_listar_disciplinas_vacias(api_client):
    """
    GIVEN: no hay disciplinas en la base
    WHEN: GET /api/catalogo/disciplinas/
    THEN: retorna 200 con lista vacía
    """
    response = api_client.get("/api/catalogo/disciplinas/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.django_db
def test_listar_promociones(api_client, promocion_junior, promocion_senior):
    """
    GIVEN: dos promociones activas
    WHEN: GET /api/catalogo/promociones/
    THEN: retorna 200 con lista de promociones
    """
    response = api_client.get("/api/catalogo/promociones/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 2


@pytest.mark.django_db
def test_listar_categorias(api_client, evento, categoria_senior):
    """
    GIVEN: una categoría activa
    WHEN: GET /api/catalogo/categorias/
    THEN: retorna 200 con la categoría
    """
    response = api_client.get("/api/catalogo/categorias/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 1
    assert data["data"][0]["nombre"] == "Senior"


@pytest.mark.django_db
def test_listar_paquetes(api_client, paquete_reencuentro, paquete_futbol):
    """
    GIVEN: dos paquetes activos con precios
    WHEN: GET /api/catalogo/paquetes/
    THEN: retorna 200 con lista de paquetes y precios de preventa
    """
    response = api_client.get("/api/catalogo/paquetes/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 2
    nombres = {item["nombre"] for item in data["data"]}
    assert "Reencuentro + Fiesta" in nombres
    assert "Fútbol 7 Masculino" in nombres
    reencuentro = next(
        item for item in data["data"] if item["nombre"] == "Reencuentro + Fiesta"
    )
    assert reencuentro["descripcion"] == "Pack con fiesta"


@pytest.mark.django_db
def test_listar_paquetes_retorna_disciplinas_completas(
    api_client, paquete_futbol, disciplina_futbol_m,
):
    """
    GIVEN: un paquete con una disciplina vinculada
    WHEN: GET /api/catalogo/paquetes/
    THEN: cada paquete incluye `disciplinas[]` con disciplina_id,
          disciplina_nombre, disciplina_sigla, min_jugadores y max_jugadores
          (contrato canónico de PaquetePresenter — sección 2)
    """
    response = api_client.get("/api/catalogo/paquetes/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    paquete_out = data["data"][0]

    # Verifica la presencia del campo top-level
    assert "disciplinas" in paquete_out, (
        "Falta el campo `disciplinas` en PaqueteListOut"
    )
    assert isinstance(paquete_out["disciplinas"], list)
    assert len(paquete_out["disciplinas"]) == 1

    disciplina_out = paquete_out["disciplinas"][0]
    # Verifica los campos del shape canónico PaqueteDisciplina
    assert disciplina_out["disciplina_id"] == str(disciplina_futbol_m.id)
    assert disciplina_out["disciplina_nombre"] == "Fútbol 7 Masculino"
    assert disciplina_out["disciplina_sigla"] == "F7M"
    # min_jugadores y max_jugadores son int no-null para Disciplina activa
    assert disciplina_out["min_jugadores"] == 7
    assert disciplina_out["max_jugadores"] == 10


@pytest.mark.django_db
def test_listar_paquetes_cantidad_minima_compra_canonica(
    api_client, paquete_futbol,
):
    """
    GIVEN: un paquete PACK activo
    WHEN: GET /api/catalogo/paquetes/
    THEN: el campo `cantidad_minima_compra` es el canónico (int >= 1),
          NO `cantidad_maxima_participantes` legacy
    """
    response = api_client.get("/api/catalogo/paquetes/")
    data = response.json()
    paquete_out = data["data"][0]
    assert paquete_out["cantidad_minima_compra"] == 7
    assert isinstance(paquete_out["cantidad_minima_compra"], int)
    assert paquete_out["cantidad_minima_compra"] >= 1


@pytest.mark.django_db
def test_listar_paquetes_modo_disciplinas_canonico(
    api_client, paquete_futbol, paquete_reencuentro,
):
    """
    GIVEN: paquetes en modo FIJO y ELEGIBLE
    WHEN: GET /api/catalogo/paquetes/
    THEN: el campo `modo_disciplinas` retorna exactamente "FIJO" o "ELEGIBLE"
    """
    response = api_client.get("/api/catalogo/paquetes/")
    data = response.json()
    modos = {item["modo_disciplinas"] for item in data["data"]}
    assert modos <= {"FIJO", "ELEGIBLE"}
    # El paquete_futbol es FIJO, paquete_reencuentro es ELEGIBLE
    futbol = next(p for p in data["data"] if p["nombre"] == "Fútbol 7 Masculino")
    reencuentro = next(p for p in data["data"] if p["nombre"] == "Reencuentro + Fiesta")
    assert futbol["modo_disciplinas"] == "FIJO"
    assert reencuentro["modo_disciplinas"] == "ELEGIBLE"


@pytest.mark.django_db
def test_listar_paquetes_sin_disciplinas_retorna_array_vacio(api_client, paquete_duo):
    """
    GIVEN: un paquete SIN disciplinas vinculadas (estado pendiente)
    WHEN: GET /api/catalogo/paquetes/
    THEN: el campo `disciplinas` retorna array vacío (no null, no undefined)
    """
    response = api_client.get("/api/catalogo/paquetes/")
    assert response.status_code == 200
    data = response.json()
    paquete_out = data["data"][0]
    assert paquete_out["nombre"] == "Dúo + Fiesta Box"
    assert paquete_out["disciplinas"] == []


@pytest.mark.django_db
def test_detalle_paquete(api_client, paquete_reencuentro):
    """
    GIVEN: un paquete con beneficios y precios
    WHEN: GET /api/catalogo/paquetes/{id}/
    THEN: retorna 200 con detalle completo incluyendo precios y beneficios
    """
    response = api_client.get(f"/api/catalogo/paquetes/{paquete_reencuentro.id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["nombre"] == "Reencuentro + Fiesta"
    assert data["data"]["tipo"] == "PACK"
    assert isinstance(data["data"]["precios"], list)
    assert len(data["data"]["precios"]) == 2
    assert isinstance(data["data"]["beneficios"], list)
    assert len(data["data"]["beneficios"]) == 1
    assert data["data"]["beneficios"][0]["tipo"] == "FIESTA"


@pytest.mark.django_db
def test_detalle_paquete_no_encontrado(api_client):
    """
    GIVEN: un ID de paquete que no existe
    WHEN: GET /api/catalogo/paquetes/{id}/
    THEN: retorna 404
    """
    import uuid

    fake_id = uuid.uuid4()
    response = api_client.get(f"/api/catalogo/paquetes/{fake_id}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_detalle_paquete_duo_sin_disciplinas(api_client, paquete_duo):
    """
    GIVEN: un paquete Dúo sin disciplinas vinculadas (estado pendiente)
    WHEN: GET /api/catalogo/paquetes/{id}/
    THEN: retorna 200 con disciplinas vacías (catálogo de solo lectura)
    """
    response = api_client.get(f"/api/catalogo/paquetes/{paquete_duo.id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["nombre"] == "Dúo + Fiesta Box"
    assert data["data"]["disciplinas"] == []


@pytest.mark.django_db
def test_seed_catalogo_fest_creates_official_ranges():
    """
    GIVEN: the seed_catalogo_fest management command
    WHEN: the command is executed
    THEN:
        - Creates 56 Promociones (1970-2025) with correct category names
        - Creates 4 official Categoria rows for FEST 2026 with correct ranges
        - Deletes obsolete categories (Sub-*)
        - Does NOT delete other events' categorias
    """
    from modules.salesianos_fest.domain.models import (
        Categoria,
        Paquete,
        PaqueteDisciplina,
        Promocion,
    )
    from io import StringIO
    from django.core.management import call_command
    from modules.eventos.domain.models import Evento

    # Run the seed command
    out = StringIO()
    call_command("seed_catalogo_fest", stdout=out)

    # Get the FEST 2026 evento that the seed command creates
    fest_evento = Evento.objects.get(nombre="Salesianos FEST 2026")

    # Verify 56 Promociones created (1970-2025)
    assert Promocion.objects.count() == 56, f"Expected 56, got {Promocion.objects.count()}"

    # Verify Promocion names by category range
    junior_promos = Promocion.objects.filter(nombre="Junior", activa=True)
    senior_promos = Promocion.objects.filter(nombre="Senior", activa=True)
    master_promos = Promocion.objects.filter(nombre="Master", activa=True)
    super_master_promos = Promocion.objects.filter(nombre="Super Master", activa=True)

    assert junior_promos.count() == 14, f"Junior (2012-2025): expected 14, got {junior_promos.count()}"
    assert senior_promos.count() == 14, f"Senior (1998-2011): expected 14, got {senior_promos.count()}"
    assert master_promos.count() == 13, f"Master (1985-1997): expected 13, got {master_promos.count()}"
    assert super_master_promos.count() == 15, f"Super Master (1970-1984): expected 15, got {super_master_promos.count()}"

    # Verify specific year mappings
    assert Promocion.objects.filter(anio=2012, nombre="Junior").exists()
    assert Promocion.objects.filter(anio=2025, nombre="Junior").exists()
    assert Promocion.objects.filter(anio=1998, nombre="Senior").exists()
    assert Promocion.objects.filter(anio=2011, nombre="Senior").exists()
    assert Promocion.objects.filter(anio=1985, nombre="Master").exists()
    assert Promocion.objects.filter(anio=1997, nombre="Master").exists()
    assert Promocion.objects.filter(anio=1970, nombre="Super Master").exists()
    assert Promocion.objects.filter(anio=1984, nombre="Super Master").exists()

    # Verify 4 official Categoria rows for FEST 2026
    fest_categorias = Categoria.objects.filter(evento=fest_evento, esta_activa=True)
    assert fest_categorias.count() == 4, f"Expected 4 active categorias, got {fest_categorias.count()}"

    # Verify official ranges
    junior_cat = fest_categorias.get(nombre="Junior")
    senior_cat = fest_categorias.get(nombre="Senior")
    master_cat = fest_categorias.get(nombre="Master")
    super_master_cat = fest_categorias.get(nombre="Super Master")

    assert junior_cat.promocion_desde == 2012 and junior_cat.promocion_hasta == 2025
    assert senior_cat.promocion_desde == 1998 and senior_cat.promocion_hasta == 2011
    assert master_cat.promocion_desde == 1985 and master_cat.promocion_hasta == 1997
    assert super_master_cat.promocion_desde == 1970 and super_master_cat.promocion_hasta == 1984

    # Verify each commercial offer exposes only its official disciplines.
    disciplinas_por_paquete = {
        "Reencuentro + Fiesta": {"F7F", "VOL", "BAS"},
        "Pichanga + Fiesta": {"F7M"},
        "Dúo + Fiesta Box": {"VOL", "BAS"},
        "Trío + Fiesta Box": {"F7M", "VOL", "BAS"},
    }
    for nombre, siglas_esperadas in disciplinas_por_paquete.items():
        paquete = Paquete.objects.get(evento=fest_evento, nombre=nombre)
        siglas = set(
            PaqueteDisciplina.objects.filter(paquete=paquete).values_list(
                "disciplina__sigla",
                flat=True,
            )
        )
        assert siglas == siglas_esperadas

    # A destructive rerun removes superseded FEST 2026 categories.
    obsolete_names = ["Sub-14", "Sub-16", "Sub-18", "Sub-20"]
    Categoria.objects.create(
        evento=fest_evento,
        nombre=obsolete_names[0],
        promocion_desde=2012,
        promocion_hasta=2012,
    )
    call_command("seed_catalogo_fest", stdout=StringIO())
    for name in obsolete_names:
        assert not Categoria.objects.filter(evento=fest_evento, nombre=name).exists(), \
            f"Obsolete category {name} should be deleted"


@pytest.mark.django_db
def test_seed_catalogo_fest_idempotent():
    """
    GIVEN: seed_catalogo_fest has been run once
    WHEN: the command is run again
    THEN: no duplicates are created (idempotent)
    """
    from modules.salesianos_fest.domain.models import Promocion, Categoria
    from io import StringIO
    from django.core.management import call_command
    from modules.eventos.domain.models import Evento

    # Run twice
    call_command("seed_catalogo_fest", stdout=StringIO())
    call_command("seed_catalogo_fest", stdout=StringIO())

    fest_evento = Evento.objects.get(nombre="Salesianos FEST 2026")

    # Should still have exactly 56 Promociones
    assert Promocion.objects.count() == 56

    # Should still have exactly 4 active Categoria for FEST 2026
    fest_categorias = Categoria.objects.filter(evento=fest_evento, esta_activa=True)
    assert fest_categorias.count() == 4
