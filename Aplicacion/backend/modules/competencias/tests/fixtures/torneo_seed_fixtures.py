"""Ephemeral catalog used by the reference tournament command tests."""

import pytest

from modules.competencias.data.fixture import load_reference_fixture
from modules.eventos.domain.constants import EstadoEdicion
from modules.eventos.domain.models import Edicion, Evento
from modules.salesianos_fest.domain.models import Disciplina, Paquete, Promocion


@pytest.fixture
def catalogo_torneo_referencia(db):
    fixture = load_reference_fixture()
    evento = Evento.objects.create(
        nombre="Salesianos FEST",
        slug="salesianos-fest-seed-test",
    )
    edicion = Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2026",
        slug="2026",
        anio=2026,
        estado=EstadoEdicion.PUBLICADA,
    )
    catalogs = {}
    for item in fixture["competitions"]:
        discipline = Disciplina.objects.create(
            edicion=edicion,
            nombre=item["source_discipline"],
            slug=item["slug"],
        )
        package = Paquete.objects.create(
            edicion=edicion,
            nombre=item["name"],
            slug=item["slug"],
            minimo_compra_inicial=1,
        )
        catalogs[item["code"]] = (discipline, package)

    years = {
        team["promotion_year"]
        for group in fixture["groups"]
        for team in group["teams"]
    }
    promotions = {
        year: Promocion.objects.create(anio=year, nombre=f"Promoción {year}")
        for year in years
    }
    return {
        "edicion": edicion,
        "catalogs": catalogs,
        "promotions": promotions,
    }


__all__ = ["catalogo_torneo_referencia"]
