"""La activación de derechos: exactamente una vez, reintentable y visible.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.1 I-2, §2.3, §4; RN-C06, RN-C08)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Estos tests son **de comportamiento**: describen el GIVEN/WHEN/THEN de cada
garantía congelada, no la forma interna del código.

| Test | Garantía congelada |
|---|---|
| `test_la_activacion_habilita_el_derecho_una_sola_vez` | I-2 — una activación por `(compra, origen)` |
| `test_el_duplicado_no_vuelve_a_invocar_al_dominio` | I-2 — la repetición converge |
| `test_la_confirmacion_tardia_converge_en_una_sola_activacion` | RN-C06 — un webhook tardío no duplica derechos |
| `test_el_fallo_del_dominio_conserva_el_pago_y_registra_la_incidencia` | RN-C08 — el cobro se conserva, la incidencia es visible |
| `test_el_reintento_tras_un_fallo_habilita_el_derecho` | RN-C08 — reintento seguro |
| `test_un_reintento_concurrente_no_habilita_el_derecho_dos_veces` | I-2 — un reintento que llega en curso no despacha |
| `test_la_clave_de_activacion_es_estable_entre_reintentos` | I-2 — la clave no cambia |
| `test_el_coordinador_despacha_al_origen_correspondiente` | `funcional/01` §5 — el origen decide |
| `test_sin_activador_de_dominio_la_activacion_queda_pendiente` | RN-C08 — la incidencia es recuperable |
| `test_una_compra_no_pagada_no_se_activa` | RN-C08 — pago y derecho son hechos separados |
| `test_la_incidencia_no_expone_el_texto_del_fallo_ni_el_detalle_crudo` | FR-04 §4 — nada de secretos ni payloads |
| `test_el_coordinador_no_depende_de_capas_de_presentacion` | arquitectura — el coordinador es de aplicación |
"""

from decimal import Decimal
from pathlib import Path

import pytest

from modules.commerce.domain.constants import (
    EstadoActivacionCompra,
    EstadoCompra,
    OrigenCompra,
)
from modules.commerce.domain.models import ActivacionCompra, Compra
from modules.commerce.domain.services.core.coordinador_activacion_compra import (
    ACCION_REINTENTAR,
    CODIGO_ACTIVACION_COMPLETADA,
    CODIGO_ACTIVACION_EN_CURSO,
    CODIGO_ACTIVACION_FALLIDA,
    CODIGO_ACTIVACION_YA_COMPLETADA,
    CODIGO_ACTIVADOR_NO_DISPONIBLE,
    CODIGO_COMPRA_NO_PAGADA,
    CoordinadorActivacionCompra,
)
from modules.pagos.domain.constants import EstadoOrdenPago
from modules.pagos.domain.models import OrdenPago

pytestmark = pytest.mark.django_db


@pytest.fixture
def coordinador(injector, registro_activadores):
    """El coordinador real, con el registro de activadores del proceso."""
    return injector.get(CoordinadorActivacionCompra)


@pytest.fixture
def compra_pagada(persona):
    """Una compra PAGADA con su orden de pago confirmada."""
    orden = OrdenPago.objects.create(
        referencia="ORD-FND05-0001",
        estado=EstadoOrdenPago.CONFIRMADA,
        monto=Decimal("100.00"),
        moneda="PEN",
    )
    return Compra.objects.create(
        persona=persona,
        origen=OrigenCompra.INSCRIPCION,
        estado=EstadoCompra.PAGADA,
        total=Decimal("100.00"),
        moneda="PEN",
        lineas_snapshot=[
            {
                "concepto_tipo": "PAQUETE",
                "concepto_id": "paquete-1",
                "concepto_nombre": "Paquete competitivo",
                "cantidad": 1,
                "precio_unitario": "100.00",
                "precio_aplicado": "100.00",
            }
        ],
        referencia="INSCRIPCION:1:INICIAL",
        orden_pago=orden,
    )


# ── Una activación por compra y origen ──────────────────────────────────────


def test_la_activacion_habilita_el_derecho_una_sola_vez(
    coordinador, compra_pagada, activador
):
    """GIVEN una compra pagada con su activador de dominio
    WHEN  se pide la activación
    THEN  el derecho queda habilitado y el registro queda ACTIVADA.
    """
    resultado = coordinador.activar_por_compra(compra_pagada.id)

    assert resultado.activada is True
    assert resultado.ya_activada is False
    assert resultado.codigo == CODIGO_ACTIVACION_COMPLETADA
    assert resultado.proxima_accion == "NINGUNA"
    assert activador.llamadas_efectivas == 1

    activacion = ActivacionCompra.objects.get(compra=compra_pagada)
    assert activacion.estado == EstadoActivacionCompra.ACTIVADA
    assert activacion.activada_en is not None
    assert activacion.intentos == 1


def test_el_duplicado_no_vuelve_a_invocar_al_dominio(
    coordinador, compra_pagada, activador
):
    """GIVEN una compra ya activada
    WHEN  se pide la activación otra vez (un webhook duplicado)
    THEN  el dominio NO vuelve a invocarse: el derecho se habilita una vez.
    """
    coordinador.activar_por_compra(compra_pagada.id)
    resultado = coordinador.activar_por_compra(compra_pagada.id)

    assert resultado.activada is True
    assert resultado.ya_activada is True
    assert resultado.codigo == CODIGO_ACTIVACION_YA_COMPLETADA
    assert activador.llamadas_efectivas == 1
    assert len(activador.llamadas) == 1
    assert ActivacionCompra.objects.count() == 1


def test_la_confirmacion_tardia_converge_en_una_sola_activacion(
    coordinador, compra_pagada, activador
):
    """GIVEN una activación que falló y quedó reintentable
    WHEN  llega la confirmación tardía y se reintenta
    THEN  converge: una sola activación efectiva y el pago nunca se revierte.
    """
    activador.fallar = True
    primero = coordinador.activar_por_compra(compra_pagada.id)

    assert primero.recuperable is True
    assert primero.proxima_accion == ACCION_REINTENTAR

    activador.fallar = False
    segundo = coordinador.activar_por_compra(compra_pagada.id)
    assert segundo.activada is True

    # Otra vuelta duplicada: ya no se invoca al dominio.
    tercero = coordinador.activar_por_compra(compra_pagada.id)
    assert tercero.ya_activada is True

    assert activador.llamadas_efectivas == 1
    assert len(activador.llamadas) == 2

    activacion = ActivacionCompra.objects.get(compra=compra_pagada)
    assert activacion.estado == EstadoActivacionCompra.ACTIVADA
    assert activacion.intentos == 2


# ── El fallo no revierte el pago ───────────────────────────────────────────


def test_el_fallo_del_dominio_conserva_el_pago_y_registra_la_incidencia(
    coordinador, compra_pagada, activador
):
    """GIVEN un pago confirmado y un dominio que falla
    WHEN  se pide la activación
    THEN  el pago sigue confirmado, la incidencia queda registrada y la
          activación es reintentable.
    """
    activador.fallar = True

    resultado = coordinador.activar_por_compra(compra_pagada.id)

    assert resultado.activada is False
    assert resultado.recuperable is True
    assert resultado.codigo == CODIGO_ACTIVACION_FALLIDA
    assert resultado.proxima_accion == ACCION_REINTENTAR

    # El cobro NO se revierte (RN-C08).
    compra_pagada.refresh_from_db()
    assert compra_pagada.estado == EstadoCompra.PAGADA
    assert compra_pagada.orden_pago.estado == EstadoOrdenPago.CONFIRMADA

    activacion = ActivacionCompra.objects.get(compra=compra_pagada)
    assert activacion.estado == EstadoActivacionCompra.FALLIDA
    assert activacion.incidencia["codigo"] == CODIGO_ACTIVACION_FALLIDA
    assert activacion.incidencia["origen"] == OrigenCompra.INSCRIPCION
    assert activacion.incidencia["intento"] == 1


def test_el_reintento_tras_un_fallo_habilita_el_derecho(
    coordinador, compra_pagada, activador
):
    """GIVEN una activación fallida
    WHEN  se reintenta y el dominio funciona
    THEN  el derecho queda habilitado y los intentos quedan contados.
    """
    activador.fallar = True
    coordinador.activar_por_compra(compra_pagada.id)

    activador.fallar = False
    resultado = coordinador.activar_por_compra(compra_pagada.id)

    assert resultado.activada is True
    assert resultado.intentos == 2

    activacion = ActivacionCompra.objects.get(compra=compra_pagada)
    assert activacion.estado == EstadoActivacionCompra.ACTIVADA
    assert activacion.intentos == 2
    assert activador.llamadas_efectivas == 1


# ── Concurrencia ───────────────────────────────────────────────────────────


def test_un_reintento_concurrente_no_habilita_el_derecho_dos_veces(
    coordinador, compra_pagada, activador
):
    """GIVEN una activación en curso
    WHEN  llega un reintento mientras el primer intento la tiene reservada
    THEN  el reintento NO despacha: espera su turno y el derecho se habilita
          una sola vez.
    """
    concurrente = {}

    def al_activar(contexto):
        # Simula la llegada de un reintento concurrente: el primer intento
        # tiene la activación reservada en este instante.
        concurrente["resultado"] = coordinador.activar_por_compra(compra_pagada.id)

    activador.al_activar = al_activar

    resultado = coordinador.activar_por_compra(compra_pagada.id)

    assert resultado.activada is True
    assert concurrente["resultado"].en_curso is True
    assert concurrente["resultado"].codigo == CODIGO_ACTIVACION_EN_CURSO
    assert activador.llamadas_efectivas == 1
    assert len(activador.llamadas) == 1


# ── El origen decide ───────────────────────────────────────────────────────


def test_el_coordinador_despacha_al_origen_correspondiente(
    coordinador, persona, registro_activadores
):
    """GIVEN tres orígenes con su activador
    WHEN  se pide la activación de cada compra
    THEN  cada compra la atiende SU activador y sólo el suyo.
    """
    from modules.commerce.tests.fixtures.activacion_fakes import ActivadorDominioFake

    dobles = {}
    for origen in OrigenCompra.values:
        doble = ActivadorDominioFake(origen=origen)
        registro_activadores.registrar(origen, doble)
        dobles[origen] = doble

    for origen in OrigenCompra.values:
        orden = OrdenPago.objects.create(
            referencia=f"ORD-FND05-{origen}",
            estado=EstadoOrdenPago.CONFIRMADA,
            monto=Decimal("50.00"),
            moneda="PEN",
        )
        compra = Compra.objects.create(
            persona=persona,
            origen=origen,
            estado=EstadoCompra.PAGADA,
            total=Decimal("50.00"),
            moneda="PEN",
            lineas_snapshot=[],
            referencia=f"{origen}:1:INICIAL",
            orden_pago=orden,
        )
        resultado = coordinador.activar_por_compra(compra.id)
        assert resultado.activada is True

    for origen, doble in dobles.items():
        assert doble.llamadas_efectivas == 1
        assert doble.llamadas[0].origen == origen


def test_sin_activador_de_dominio_la_activacion_queda_pendiente(
    coordinador, compra_pagada, registro_activadores
):
    """GIVEN una compra pagada sin activador registrado para su origen
    WHEN  se pide la activación
    THEN  la activación queda PENDIENTE y reintentable, y el pago se conserva.
    """
    resultado = coordinador.activar_por_compra(compra_pagada.id)

    assert resultado.activada is False
    assert resultado.recuperable is True
    assert resultado.codigo == CODIGO_ACTIVADOR_NO_DISPONIBLE
    assert resultado.proxima_accion == ACCION_REINTENTAR

    activacion = ActivacionCompra.objects.get(compra=compra_pagada)
    assert activacion.estado == EstadoActivacionCompra.PENDIENTE
    assert activacion.en_curso is False

    compra_pagada.refresh_from_db()
    assert compra_pagada.estado == EstadoCompra.PAGADA


def test_una_compra_no_pagada_no_se_activa(coordinador, persona):
    """GIVEN una compra PENDIENTE
    WHEN  se pide la activación
    THEN  no se activa: sin pago confirmado no hay derecho que entregar.
    """
    orden = OrdenPago.objects.create(
        referencia="ORD-FND05-PENDIENTE",
        estado=EstadoOrdenPago.PENDIENTE,
        monto=Decimal("10.00"),
        moneda="PEN",
    )
    compra = Compra.objects.create(
        persona=persona,
        origen=OrigenCompra.INSCRIPCION,
        estado=EstadoCompra.PENDIENTE,
        total=Decimal("10.00"),
        moneda="PEN",
        lineas_snapshot=[],
        referencia="INSCRIPCION:9:INICIAL",
        orden_pago=orden,
    )

    resultado = coordinador.activar_por_compra(compra.id)

    assert resultado.activada is False
    assert resultado.codigo == CODIGO_COMPRA_NO_PAGADA
    assert ActivacionCompra.objects.count() == 0


# ── La clave y la seguridad ────────────────────────────────────────────────


def test_la_clave_de_activacion_es_estable_entre_reintentos(
    coordinador, compra_pagada, activador
):
    """GIVEN una activación con un fallo
    WHEN  se reintenta
    THEN  la clave NO cambia: es lo que permite que el dominio deduplique.
    """
    activador.fallar = True
    coordinador.activar_por_compra(compra_pagada.id)

    activador.fallar = False
    coordinador.activar_por_compra(compra_pagada.id)

    claves = [contexto.clave for contexto in activador.llamadas]
    assert len(claves) == 2
    assert claves[0] == claves[1]
    assert str(compra_pagada.id) in claves[0]
    assert OrigenCompra.INSCRIPCION in claves[0]


def test_la_incidencia_no_expone_el_texto_del_fallo_ni_el_detalle_crudo(
    coordinador, compra_pagada, activador
):
    """GIVEN un dominio que falla con un mensaje sensible
    WHEN  se pide la activación
    THEN  ni la incidencia ni el resultado guardan el mensaje ni el detalle
          crudo del dominio.
    """
    activador.fallar = True
    activador.mensaje_fallo = "token=secreto-123 payload={\"card\":\"4111\"}"
    activador.detalle = {"cantidad": 1, "secreto": "clave-del-comercio"}

    resultado = coordinador.activar_por_compra(compra_pagada.id)

    activacion = ActivacionCompra.objects.get(compra=compra_pagada)

    assert set(activacion.incidencia.keys()) == {"codigo", "origen", "intento", "fecha"}
    assert "secreto" not in str(activacion.incidencia)
    assert "4111" not in str(activacion.incidencia)
    assert "token=" not in str(resultado.codigo)
    assert resultado.codigo == CODIGO_ACTIVACION_FALLIDA

    # El detalle del dominio sólo conserva las claves permitidas.
    activador.fallar = False
    activador.detalle = {"cantidad": 2, "secreto": "clave-del-comercio"}
    activacion.estado = EstadoActivacionCompra.PENDIENTE
    activacion.save(update_fields=["estado"])

    coordinador.activar_por_compra(compra_pagada.id)

    activacion.refresh_from_db()
    assert activacion.detalle == {"cantidad": 2}
    assert "secreto" not in str(activacion.detalle)


def test_el_coordinador_no_depende_de_capas_de_presentacion():
    """GIVEN el módulo `commerce`
    WHEN  se busca una dependencia de la capa de presentación
    THEN  no hay ninguna: el coordinador es un servicio de aplicación.
    """
    import modules.commerce as paquete

    raiz = Path(paquete.__file__).parent
    infractores = []
    for ruta in raiz.rglob("*.py"):
        # Ni la propia capa de presentación ni los tests (que la nombran al
        # describir la garantía) son dependencias del coordinador.
        if "presentation" in ruta.parts or "tests" in ruta.parts:
            continue
        if "presentation" in ruta.read_text(encoding="utf-8"):
            infractores.append(str(ruta.relative_to(raiz)))

    assert infractores == []
