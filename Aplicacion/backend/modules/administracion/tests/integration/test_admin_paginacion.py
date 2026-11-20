"""La PAGINACIÓN del panel: el filtro va ANTES de la página.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` · Lote D2

GIVEN  una edición con pagos de veredictos operativos distintos
WHEN   el listado se filtra por `estado_operativo` y se pagina
THEN   `total` y `total_pages` describen las filas FILTRADAS, y cada página
       trae filas que CUMPLEN el filtro: el filtro se aplica ANTES de paginar.

> **El defecto que este archivo fija.** El filtro `estado_operativo` se
> aplicaba DESPUÉS de recortar la página: `total` contaba las filas SIN
> filtrar y una página podía venir VACÍA aunque quedaran filas que cumplían
> el filtro. El navegador, que pagina sobre `total`, quedaba descolocado: la
> última página no existía y la primera podía no traer nada.
>
> El veredicto lo calcula el DUEÑO (`EstadoOperativoPagoService`): aquí sólo
> se copia. La regla NO se reimplementa ni se filtra en SQL.
"""

from datetime import timedelta
from decimal import Decimal

import pytest

from modules.pagos.domain.constants import EstadoOrdenPago, EstadoOperativoPago


# ── Fixtures de este archivo ─────────────────────────────────────────────────


class _EstadoCompraDePrueba:
    """El puerto de estado de la compra: NINGUNA compra consta pagada.

    Con esta bandera el veredicto del DUEÑO depende sólo del estado de la
    orden, que es lo que el test quiere distinguir.
    """

    def obtener_estado_compra(self, orden_pago_id: str):
        class _Estado:
            pagada = False
            cancelada = False

        return _Estado()


class _ActivacionDePrueba:
    """El puerto de activación: no hay activación registrada."""

    def estado_activacion(self, orden_pago_id: str):
        from modules.pagos.domain.schemas.pago_schemas import (
            EstadoActivacionCompraData,
        )

        return EstadoActivacionCompraData(existe=False)

    def activar_por_orden(self, orden_pago_id: str):  # pragma: no cover
        raise NotImplementedError("Este test no activa derechos.")


@pytest.fixture
def servicio_operacion():
    """El servicio de la capa operativa, con sus selectores."""
    from modules.administracion.domain.selectors.admin_operacion_selector import (
        AdminEquipoSelector,
        AdminInscripcionSelector,
        AdminParticipanteSelector,
        AdminPagoSelector,
        AdminPersonaSelector,
    )
    from modules.administracion.domain.services.core.admin_operacion_service import (
        AdminOperacionService,
    )
    from modules.pagos.domain.services.core.estado_operativo_pago_service import (
        EstadoOperativoPagoService,
    )

    return AdminOperacionService(
        inscripcion_selector=AdminInscripcionSelector(),
        equipo_selector=AdminEquipoSelector(),
        participante_selector=AdminParticipanteSelector(),
        pago_selector=AdminPagoSelector(),
        persona_selector=AdminPersonaSelector(),
        estado_operativo_pago=EstadoOperativoPagoService(
            estado_compra_service=_EstadoCompraDePrueba(),
            activacion_service=_ActivacionDePrueba(),
        ),
    )


@pytest.fixture
def pagos_de_la_edicion(db, edicion_publicada, persona):
    """Tres lotes de pases con tres veredictos distintos.

    - `pendiente-1` y `pendiente-2`: la orden NO está confirmada ⇒ el
      veredicto del dueño es `PENDIENTE`.
    - `confirmado`: la orden está confirmada ⇒ el veredicto del dueño es
      `PAGADA_SIN_LIQUIDAR` (el dinero entró, el hecho comercial todavía no).

    El filtro `PENDIENTE` tiene que devolver DOS filas de TRES.
    """
    from django.utils import timezone

    from modules.commerce.domain.constants import EstadoCompra, OrigenCompra
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.models import OrdenPago
    from modules.salesianos_fest.domain.models import CompraPase, Pase

    pase = Pase.objects.create(
        edicion=edicion_publicada,
        nombre="Pase del panel",
        slug="pase-del-panel",
    )

    def _lote(nombre, estado_orden):
        orden = OrdenPago.objects.create(
            referencia=f"ORD-{nombre}",
            estado=estado_orden,
            monto=Decimal("70.00"),
            moneda="PEN",
        )
        compra = Compra.objects.create(
            persona=persona,
            origen=OrigenCompra.PASE,
            estado=EstadoCompra.PENDIENTE,
            total=Decimal("70.00"),
            moneda="PEN",
            lineas_snapshot=[
                {
                    "concepto_tipo": "PASE",
                    "concepto_id": str(pase.id),
                    "concepto_nombre": pase.nombre,
                    "concepto": "Pase del panel",
                    "cantidad": 2,
                    "precio_unitario": "35.00",
                    "precio_aplicado": "35.00",
                }
            ],
            referencia=f"COMPRA-{nombre}",
            orden_pago=orden,
        )

        return CompraPase.objects.create(
            edicion=edicion_publicada,
            pase=pase,
            comprador=persona,
            cantidad=2,
            asignados=0,
            precio_unitario=Decimal("35.00"),
            total=Decimal("70.00"),
            moneda="PEN",
            token=f"token-panel-{nombre}",
            token_expira_en=timezone.now() + timedelta(days=30),
            referencia=f"PASE-{nombre}",
            compra=compra,
        )

    return {
        "pendiente_1": _lote("PENDIENTE-1", EstadoOrdenPago.PENDIENTE),
        "pendiente_2": _lote("PENDIENTE-2", EstadoOrdenPago.PENDIENTE),
        "confirmado": _lote("CONFIRMADO", EstadoOrdenPago.CONFIRMADA),
    }


# ── El filtro se aplica ANTES de paginar ────────────────────────────────────


def test_el_total_cuenta_solo_las_filas_que_cumplen_el_filtro(
    db,
    servicio_operacion,
    edicion_publicada,
    pagos_de_la_edicion,
):
    """`total` describe el conjunto FILTRADO, no el conjunto crudo.

    Tres pagos, dos con veredicto `PENDIENTE`: `total` es 2 y `total_pages`
    es 2 con una página de tamaño 1. Con el filtro aplicado DESPUÉS de
    paginar, `total` era 3 y `total_pages` era 3.
    """
    items, total, pagina, tamano, paginas = servicio_operacion.listar_pagos(
        edicion_publicada.id,
        estado_operativo=EstadoOperativoPago.PENDIENTE,
        page=1,
        page_size=1,
    )

    assert total == 2
    assert tamano == 1
    assert paginas == 2
    assert pagina == 1
    assert len(items) == 1


def test_cada_pagina_trae_filas_que_cumplen_el_filtro(
    db,
    servicio_operacion,
    edicion_publicada,
    pagos_de_la_edicion,
):
    """Ninguna página viene VACÍA ni trae filas que no cumplen el filtro.

    La segunda página existe porque hay DOS filas que cumplen el filtro: con
    el defecto, la página 2 se recortaba sobre el conjunto SIN filtrar y
    podía devolver cero filas.
    """
    vistos = []

    for pagina in (1, 2):
        items, total, _, _, paginas = servicio_operacion.listar_pagos(
            edicion_publicada.id,
            estado_operativo=EstadoOperativoPago.PENDIENTE,
            page=pagina,
            page_size=1,
        )

        assert total == 2
        assert paginas == 2
        assert len(items) == 1, f"la página {pagina} vino vacía"
        assert items[0].estado_operativo.codigo == EstadoOperativoPago.PENDIENTE

        vistos.append(items[0].compra_id)

    assert vistos[0] != vistos[1]
    assert set(vistos) == {
        str(pagos_de_la_edicion["pendiente_1"].compra_id),
        str(pagos_de_la_edicion["pendiente_2"].compra_id),
    }


def test_el_pago_confirmado_no_entra_en_el_filtro_de_pendientes(
    db,
    servicio_operacion,
    edicion_publicada,
    pagos_de_la_edicion,
):
    """El filtro EXCLUYE la fila cuyo veredicto es otro.

    El veredicto lo publica el DUEÑO (`PAGADA_SIN_LIQUIDAR`): el panel lo
    copia, no lo recalcula.
    """
    items, total, *_ = servicio_operacion.listar_pagos(
        edicion_publicada.id,
        estado_operativo=EstadoOperativoPago.PENDIENTE,
        page=1,
        page_size=25,
    )

    assert str(pagos_de_la_edicion["confirmado"].compra_id) not in [
        item.compra_id for item in items
    ]
    assert total == 2


def test_sin_filtro_la_paginacion_describe_el_conjunto_completo(
    db,
    servicio_operacion,
    edicion_publicada,
    pagos_de_la_edicion,
):
    """SIN filtro, la paginación es la de siempre: `total` cuenta las tres.

    La corrección del filtro no puede cambiar el camino SIN filtro.
    """
    items, total, pagina, tamano, paginas = servicio_operacion.listar_pagos(
        edicion_publicada.id,
        page=1,
        page_size=25,
    )

    assert total == 3
    assert len(items) == 3
    assert paginas == 1
    assert pagina == 1
    assert tamano == 25


def test_un_filtro_sin_coincidencias_devuelve_una_pagina_vacia_y_consistente(
    db,
    servicio_operacion,
    edicion_publicada,
    pagos_de_la_edicion,
):
    """Un veredicto que no existe NO inventa páginas.

    `total` es 0, `total_pages` es 0 y la página viene vacía: el navegador no
    puede navegar a una página que no existe.
    """
    items, total, pagina, tamano, paginas = servicio_operacion.listar_pagos(
        edicion_publicada.id,
        estado_operativo="VEREDICTO_QUE_NO_EXISTE",
        page=1,
        page_size=25,
    )

    assert items == []
    assert total == 0
    assert paginas == 0


# ── El MISMO contrato en el cable ────────────────────────────────────────────


@pytest.fixture
def cliente_admin(db):
    """Un cliente con sesión de un operador (`admin.ver`)."""
    from django.test import Client
    from ninja_jwt.tokens import AccessToken

    from modules.usuarios.domain.models import Usuario

    usuario = Usuario.objects.create_user(
        username="admin.paginacion",
        password="Prueba-12345",
        is_staff=True,
    )

    cliente = Client()
    cliente.defaults["HTTP_AUTHORIZATION"] = f"Bearer {AccessToken.for_user(usuario)}"

    return cliente


def test_la_api_publica_un_total_consistente_con_el_filtro(
    cliente_admin,
    edicion_publicada,
    pagos_de_la_edicion,
):
    """`GET /api/administracion/pagos` publica el total FILTRADO.

    El navegador pagina sobre `data.total`: si el total contase filas que la
    página no trae, la última página sería inalcanzable y la primera podría
    venir vacía. El envelope es el único que puede publicar esas tres cosas
    (`FR-01` §4.3): `items`, `total` y `total_pages`.
    """
    respuesta = cliente_admin.get(
        "/api/administracion/pagos",
        data={"estado_operativo": EstadoOperativoPago.PENDIENTE, "page_size": 1},
    )

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert cuerpo["success"] is True

    data = cuerpo["data"]

    assert data["total"] == 2
    assert data["total_pages"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["estado_operativo"]["codigo"] == EstadoOperativoPago.PENDIENTE
