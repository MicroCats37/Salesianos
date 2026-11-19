"""El catálogo de paquetes: real, por edición y SIN precio de reserva.

GIVEN  una edición publicada con su catálogo
WHEN   se consulta el catálogo de paquetes
THEN   devuelve los paquetes COMPRABLES de ESA edición, con el precio
       vigente del catálogo — y un paquete sin precio vigente NO aparece
       (`FL-01` paso 3, `RN-E01`, `RN-C02`).

Cliente del flujo: `async_to_sync`, el puente correcto para un flujo async
con `sync_to_async(thread_sensitive=True)`.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.eventos.domain.exceptions import ModuloNoHabilitadoError
from modules.salesianos_fest.domain.models import PaquetePrecio
from modules.salesianos_fest.domain.services.flujos.catalogo_flujo import CatalogoFlujo

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real del catálogo."""
    return injector.get(CatalogoFlujo)


def test_el_paquete_se_publica_con_su_precio_vigente_y_sus_beneficios(
    flujo, edicion_publicada, paquete, precio, beneficio
):
    """GIVEN un paquete con precio, beneficio y disciplina
    WHEN  se consulta el catálogo
    THEN  el paquete aparece con su precio, sus beneficios y sus disciplinas.
    """
    resultado = async_to_sync(flujo.listar_paquetes)(edicion_publicada.id)

    assert len(resultado.paquetes) == 1
    publicado = resultado.paquetes[0]
    assert publicado.nombre == "Paquete competitivo"
    assert publicado.estado == "VIGENTE"
    assert publicado.cupos_incluidos == 10
    assert publicado.precio.monto == Decimal("250.00")
    assert publicado.precio.moneda == "PEN"
    assert [beneficio.codigo for beneficio in publicado.beneficios] == ["BIENVENIDA"]
    assert [disciplina.nombre for disciplina in publicado.disciplinas] == [
        "Vóley Mixto"
    ]
    assert publicado.edicion_id == str(edicion_publicada.id)


def test_un_paquete_sin_precio_no_esta_a_la_venta(flujo, edicion_publicada, paquete_sin_precio):
    """GIVEN un paquete VIGENTE sin precio
    WHEN  se consulta el catálogo
    THEN  NO aparece: el catálogo no inventa un precio de reserva.
    """
    resultado = async_to_sync(flujo.listar_paquetes)(edicion_publicada.id)

    assert resultado.paquetes == []


def test_un_paquete_con_precio_vencido_no_esta_a_la_venta(
    flujo, edicion_publicada, paquete
):
    """GIVEN un paquete cuyo precio ya venció
    WHEN  se consulta el catálogo
    THEN  NO aparece: el precio vigente es un hecho del catálogo.
    """
    PaquetePrecio.objects.filter(paquete=paquete).update(
        vigente_desde=date.today() - timedelta(days=10),
        vigente_hasta=date.today() - timedelta(days=1),
    )

    resultado = async_to_sync(flujo.listar_paquetes)(edicion_publicada.id)

    assert resultado.paquetes == []


def test_el_catalogo_es_por_edicion(flujo, edicion_publicada, edicion_otra, paquete, precio):
    """GIVEN un catálogo de la edición A
    WHEN  se consulta el catálogo de la edición B
    THEN  el catálogo de A NO aparece: el alcance es la edición.
    """
    resultado = async_to_sync(flujo.listar_paquetes)(edicion_otra.id)

    assert resultado.paquetes == []
    assert resultado.edicion_id == str(edicion_otra.id)


def test_un_paquete_retirado_no_se_ofrece(flujo, edicion_publicada, paquete_retirado):
    """GIVEN un paquete RETIRADO
    WHEN  se consulta el catálogo
    THEN  NO aparece: el catálogo histórico se conserva, pero no se ofrece.
    """
    resultado = async_to_sync(flujo.listar_paquetes)(edicion_publicada.id)

    assert resultado.paquetes == []


def test_una_edicion_sin_el_modulo_no_expone_catalogo(flujo, edicion_sin_modulo):
    """GIVEN una edición sin el módulo `inscripciones` habilitado
    WHEN  se consulta su catálogo
    THEN  responde el error de módulo no habilitado, no un catálogo vacío.
    """
    with pytest.raises(ModuloNoHabilitadoError):
        async_to_sync(flujo.listar_paquetes)(edicion_sin_modulo.id)
