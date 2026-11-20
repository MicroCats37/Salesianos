"""Garantías del seed de catálogo que el resto de la suite NO cubre.

Este archivo es COMPLEMENTARIO de
`modules/salesianos_fest/tests/integration/test_seed_catalogo.py`: vive en su
propio archivo a propósito, para no competir por la misma ruta con otro
paquete de trabajo y para que estas garantías sobrevivan aunque aquél se
rehaga.

Cubre las cuatro propiedades que el resto de la suite NO verifica:

1. **Reejecutar NO reescribe ninguna fila** — no basta con comparar conteos:
   una reescritura conserva los conteos. Se compara el contenido íntegro de
   cada fila, incluido su `updated_at`.
2. **Una categoría con otro rango se preserva** — el seed no pisa la
   configuración comercial del operador.
3. **Ni disciplinas ni categorías ajenas se borran** — el seed sólo AGREGA.
4. **Los parámetros del operador se respetan** — edición indicada por
   parámetro y módulos que se suman sin deshabilitar los existentes.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §8 y §10.5.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command

from modules.eventos.domain.constants import EstadoEdicion
from modules.eventos.domain.models import Edicion, Evento
from modules.salesianos_fest.domain.models import (
    Categoria,
    Disciplina,
    Paquete,
    PaqueteBeneficio,
    PaqueteDisciplina,
    PaquetePrecio,
    Promocion,
)
from modules.salesianos_fest.management.commands.seed_catalogo import (
    CATEGORIAS_OFICIALES,
    DISCIPLINAS_OFICIALES,
    PAQUETES_OFICIALES,
)

pytestmark = pytest.mark.django_db


# ── Utilidades ───────────────────────────────────────────────────────────────


def _sembrar(*argumentos):
    """Ejecuta el comando de seed con sus valores por defecto."""
    call_command("seed_catalogo", *argumentos)


def _instantanea_del_catalogo() -> list:
    """El contenido ÍNTEGRO del catálogo, para comparar dos ejecuciones.

    Incluye `created_at` y `updated_at`: si la segunda ejecución reescribiera
    una fila, su `updated_at` cambiaría y la comparación fallaría. Comparar
    sólo los CONTOS no alcanza: una reescritura los conserva.
    """
    instantanea = []
    for modelo in (
        Promocion,
        Categoria,
        Disciplina,
        Paquete,
        PaquetePrecio,
        PaqueteDisciplina,
        PaqueteBeneficio,
    ):
        for fila in modelo.objects.order_by("pk").values():
            instantanea.append((modelo.__name__, fila))
    return instantanea


def _edicion_operador(estado=EstadoEdicion.PUBLICADA, modulos=("inscripciones",)):
    """Una edición ya existente, creada por el operador."""
    evento = Evento.objects.create(nombre="Salesianos FEST", slug="salesianos-fest")
    return Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2026",
        slug="2026",
        anio=2026,
        estado=estado,
        modulos_habilitados=list(modulos),
    )


# ── 1. Reejecutar no reescribe nada ──────────────────────────────────────────


def test_el_seed_no_reescribe_ninguna_fila_en_reejecucion():
    """GIVEN un catálogo ya sembrado
    WHEN  se ejecuta el seed otra vez
    THEN  NINGUNA fila cambia: ni de contenido ni de `updated_at`. El seed
          no reescribe lo que ya existe: sólo lo crea cuando falta.
    """
    _sembrar()
    antes = _instantanea_del_catalogo()

    _sembrar()

    assert _instantanea_del_catalogo() == antes


def test_el_seed_no_reescribe_el_precio_ya_sembrado():
    """GIVEN un paquete con sus dos precios sembrados
    WHEN  se ejecuta el seed otra vez
    THEN  el `updated_at` de los precios NO cambia: no los reescribe ni los
          duplica.
    """
    _sembrar()
    antes = {
        precio.pk: precio.updated_at
        for precio in PaquetePrecio.objects.all()
    }
    assert antes, "El seed debe sembrar precios."

    _sembrar()

    despues = {
        precio.pk: precio.updated_at
        for precio in PaquetePrecio.objects.all()
    }
    assert despues == antes


# ── 2. No pisa la configuración comercial ─────────────────────────────────────


def test_el_seed_preserva_el_rango_de_una_categoria_del_operador():
    """GIVEN una categoría del operador con el MISMO nombre y otro rango
    WHEN  se ejecuta el seed
    THEN  el rango se preserva: el seed no pisa la configuración comercial.
    """
    edicion = _edicion_operador()
    Categoria.objects.create(
        edicion=edicion,
        nombre=CATEGORIAS_OFICIALES[0]["nombre"],
        promocion_desde=2000,
        promocion_hasta=2010,
        estado="ACTIVA",
    )

    _sembrar()

    categoria = Categoria.objects.get(
        edicion=edicion,
        nombre=CATEGORIAS_OFICIALES[0]["nombre"],
    )
    assert categoria.promocion_desde == 2000
    assert categoria.promocion_hasta == 2010
    assert Categoria.objects.filter(edicion=edicion).count() == (
        len(CATEGORIAS_OFICIALES)
    )


def test_el_seed_preserva_el_precio_configurado_por_el_operador():
    """GIVEN un paquete oficial cuyo precio ya fue configurado por el operador
    WHEN  se ejecuta el seed
    THEN  el precio se preserva: el seed no crea los precios oficiales ni
          modifica el existente.
    """
    edicion = _edicion_operador()
    oficial = PAQUETES_OFICIALES[0]
    paquete = Paquete.objects.create(
        edicion=edicion,
        nombre=oficial["nombre"],
        slug=oficial["slug"],
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        monto=Decimal("99.00"),
        vigente_desde=date(2026, 1, 1),
    )

    _sembrar()

    precios = PaquetePrecio.objects.filter(paquete=paquete)
    assert precios.count() == 1
    assert precios.first().monto == Decimal("99.00")


# ── 3. Sólo agrega: nunca borra ──────────────────────────────────────────────


def test_el_seed_no_borra_las_disciplinas_del_operador():
    """GIVEN una disciplina propia del operador, con su propio slug
    WHEN  se ejecuta el seed
    THEN  la disciplina sigue ahí: el seed sólo AGREGA las suyas, nunca
          borra las ajenas.
    """
    edicion = _edicion_operador()
    Disciplina.objects.create(
        edicion=edicion,
        nombre="Atletismo",
        slug="atletismo",
    )

    _sembrar()

    assert Disciplina.objects.filter(edicion=edicion, slug="atletismo").exists()
    assert Disciplina.objects.filter(edicion=edicion).count() == (
        len(DISCIPLINAS_OFICIALES) + 1
    )


def test_el_seed_no_borra_las_categorias_inactivas_del_operador():
    """GIVEN una categoría OBSOLETA del operador, inactiva
    WHEN  se ejecuta el seed
    THEN  sigue ahí: el seed no borra el catálogo histórico, sólo lo marca
          como retirable (`estado = INACTIVA`).
    """
    edicion = _edicion_operador()
    Categoria.objects.create(
        edicion=edicion,
        nombre="Sub-14",
        promocion_desde=2010,
        promocion_hasta=2011,
        estado="INACTIVA",
    )

    _sembrar()

    obsoleta = Categoria.objects.get(edicion=edicion, nombre="Sub-14")
    assert obsoleta.estado == "INACTIVA"


def test_el_seed_no_borra_los_vinculos_del_operador():
    """GIVEN un vínculo disciplina↔paquete añadido por el operador
    WHEN  se ejecuta el seed
    THEN  el vínculo sigue ahí: el seed sólo AGREGA, nunca borra.
    """
    _sembrar()
    edicion = Edicion.objects.get(slug="2026")
    paquete = Paquete.objects.get(edicion=edicion, slug=PAQUETES_OFICIALES[0]["slug"])
    # Una disciplina que el seed NO vinculó a este paquete: el vínculo del
    # operador es una fila NUEVA, no una repetición de la sembrada.
    disciplina = Disciplina.objects.get(edicion=edicion, slug="futbol-7-masculino")
    assert not PaqueteDisciplina.objects.filter(
        paquete=paquete,
        disciplina=disciplina,
    ).exists()
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)
    vinculos = PaqueteDisciplina.objects.count()

    _sembrar()

    assert PaqueteDisciplina.objects.count() == vinculos
    assert PaqueteDisciplina.objects.filter(
        paquete=paquete,
        disciplina=disciplina,
    ).exists()


# ── 4. Respeta los parámetros del operador ───────────────────────────────────


def test_el_seed_siembra_la_edicion_indicada_por_parametro():
    """GIVEN una base de datos vacía
    WHEN  se ejecuta el seed con OTRA edición por parámetro
    THEN  siembra esa edición —con su año y su nombre— y no la de por
          defecto: la identidad se pide por parámetro, nunca por constante.
    """
    _sembrar(
        "--edicion-slug",
        "2027",
        "--edicion-nombre",
        "Salesianos FEST 2027",
        "--anio",
        "2027",
    )

    edicion = Edicion.objects.get(slug="2027")
    assert edicion.nombre == "Salesianos FEST 2027"
    assert edicion.anio == 2027
    assert edicion.estado == EstadoEdicion.PUBLICADA
    assert Edicion.objects.filter(slug="2026").count() == 0


def test_el_seed_habilita_los_modulos_pedidos_y_conserva_los_existentes():
    """GIVEN una edición del operador con el módulo `pases` habilitado
    WHEN  se ejecuta el seed pidiendo además `marketplace`
    THEN  la edición termina con `pases`, `inscripciones` y `marketplace`:
          el seed SUME módulos, nunca deshabilita los que ya estaban.
    """
    edicion = _edicion_operador(modulos=("pases",))

    _sembrar("--modulo", "marketplace")

    edicion.refresh_from_db()
    assert edicion.modulo_habilitado("inscripciones")
    assert edicion.modulo_habilitado("marketplace")
    assert edicion.modulo_habilitado("pases")
