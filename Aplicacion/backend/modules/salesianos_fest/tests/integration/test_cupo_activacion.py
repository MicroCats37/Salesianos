"""La activación de derechos: los cupos se habilitan UNA sola vez.

GIVEN  una compra pagada de una inscripción
WHEN   el coordinador de `commerce` activa el origen INSCRIPCION
THEN   los cupos pagados suben exactamente una vez, la ampliación NO duplica
       los beneficios `FIJO_INICIAL` y los beneficios `POR_CUPO` siguen
       PENDIENTES porque su regla está ABIERTA (`RN-I02`, `RN-I06`, `QA-I02`,
       `QA-I03`, `PD-09`).
"""

import pytest

from modules.commerce.domain.constants import EstadoActivacionCompra, OrigenCompra
from modules.commerce.domain.models import ActivacionCompra, Compra
from modules.commerce.domain.schemas.compra_schemas import (
    ContextoActivacionCompra,
)
from modules.commerce.domain.services.core.coordinador_activacion_compra import (
    CODIGO_ACTIVACION_COMPLETADA,
    CODIGO_ACTIVACION_YA_COMPLETADA,
    CoordinadorActivacionCompra,
)
from modules.commerce.domain.services.core.registro_activadores_compra import (
    obtener_registro,
)
from modules.salesianos_fest.domain.constants import (
    CODIGO_CAPACIDAD_ACTIVADA,
    CODIGO_CAPACIDAD_YA_ACTIVADA,
    CODIGO_REFERENCIA_NO_RECONOCIDA,
    TipoBeneficioPaquete,
)
from modules.salesianos_fest.domain.models import (
    ActivacionCapacidad,
    BeneficioConcedido,
)
from modules.salesianos_fest.domain.referencia import (
    referencia_expansion,
    referencia_inicial,
)
from modules.salesianos_fest.domain.services.core.activador_inscripcion import (
    ActivadorInscripcion,
)

pytestmark = pytest.mark.django_db


def _contexto(compra_id, referencia: str, cantidad: int, clave: str):
    """El contexto de activación que entrega el coordinador."""
    return ContextoActivacionCompra(
        compra_id=compra_id,
        origen=OrigenCompra.INSCRIPCION,
        clave=clave,
        persona_id="11111111-1111-1111-1111-111111111111",
        referencia=referencia,
        total=100,
        moneda="PEN",
        lineas_snapshot=[
            {
                "concepto_tipo": "PAQUETE",
                "concepto_id": "22222222-2222-2222-2222-222222222222",
                "concepto_nombre": "Paquete",
                "cantidad": cantidad,
                "precio_unitario": "10.00",
                "precio_aplicado": "10.00",
            }
        ],
    )


def _compra_pagada(inscripcion, referencia: str, cantidad: int):
    """Una compra PAGADA de la inscripción, con su línea congelada."""
    return Compra.objects.create(
        persona_id=inscripcion.responsable_id,
        origen=OrigenCompra.INSCRIPCION,
        total=2500,
        moneda="PEN",
        lineas_snapshot=[
            {
                "concepto_tipo": "PAQUETE",
                "concepto_id": str(inscripcion.paquete_id),
                "concepto_nombre": "Paquete",
                "cantidad": cantidad,
                "precio_unitario": "250.00",
                "precio_aplicado": "250.00",
            }
        ],
        referencia=referencia,
        estado="PAGADA",
    )


# ── El registro ─────────────────────────────────────────────────────────────


def test_el_modulo_registra_su_activador_para_el_origen_inscripcion():
    """GIVEN el proceso arrancado
    WHEN  se pregunta al registro de activadores
    THEN  el origen INSCRIPCION tiene un activador: sin él, la activación
       quedaría PENDIENTE y reintentable (`RN-C08`).
    """
    activador = obtener_registro().resolver(OrigenCompra.INSCRIPCION)

    assert activador is not None
    assert isinstance(activador, ActivadorInscripcion)


# ── La activación ───────────────────────────────────────────────────────────


def test_la_activacion_habilita_los_cupos_de_la_compra(inscripcion_sin_pagos):
    """GIVEN una inscripción con cero cupos pagados
    WHEN  se activa el alta de la compra
    THEN  los cupos pagados suben a los que compró la inscripción
       (`RN-I02`).
    """
    activador = ActivadorInscripcion()
    resultado = activador.activar(
        _contexto(
            "33333333-3333-3333-3333-333333333333",
            referencia_inicial(inscripcion_sin_pagos.id),
            10,
            "activacion:INSCRIPCION:33333333-3333-3333-3333-333333333333",
        )
    )

    assert resultado.exito is True
    assert resultado.codigo == CODIGO_CAPACIDAD_ACTIVADA
    assert resultado.detalle["cantidad"] == 10

    inscripcion_sin_pagos.refresh_from_db()
    assert inscripcion_sin_pagos.cupos_pagados == 10
    assert ActivacionCapacidad.objects.count() == 1


def test_la_activacion_es_idempotente_por_clave(inscripcion_sin_pagos):
    """GIVEN una activación YA aplicada
    WHEN  llega el MISMO derecho otra vez (un reintento o un webhook
    duplicado)
    THEN  NO se suman cupos otra vez: la clave es la autoridad
       (`QA-I02`, `RN-C06`).
    """
    activador = ActivadorInscripcion()
    contexto = _contexto(
        "44444444-4444-4444-4444-444444444444",
        referencia_inicial(inscripcion_sin_pagos.id),
        10,
        "activacion:INSCRIPCION:44444444-4444-4444-4444-444444444444",
    )

    primera = activador.activar(contexto)
    segunda = activador.activar(contexto)

    assert primera.exito is True
    assert segunda.exito is True
    assert segunda.codigo == CODIGO_CAPACIDAD_YA_ACTIVADA
    assert segunda.detalle["cantidad"] == 10

    inscripcion_sin_pagos.refresh_from_db()
    assert inscripcion_sin_pagos.cupos_pagados == 10
    assert ActivacionCapacidad.objects.count() == 1


def test_una_referencia_desconocida_no_se_activita(inscripcion_sin_pagos):
    """GIVEN una compra que NO es de este módulo
    WHEN  llega su activación
    THEN  el activador la rechaza con un código explícito: no inventa a qué
       inscripción pertenece.
    """
    activador = ActivadorInscripcion()
    resultado = activador.activar(
        _contexto(
            "55555555-5555-5555-5555-555555555555",
            "PASE:otra-cosa",
            1,
            "activacion:INSCRIPCION:55555555-5555-5555-5555-555555555555",
        )
    )

    assert resultado.exito is False
    assert resultado.codigo == CODIGO_REFERENCIA_NO_RECONOCIDA
    assert ActivacionCapacidad.objects.count() == 0


# ── Los beneficios ──────────────────────────────────────────────────────────


def test_la_activacion_del_alta_concede_el_beneficio_fijo_inicial(
    inscripcion_sin_pagos, beneficio
):
    """GIVEN un paquete con un beneficio `FIJO_INICIAL`
    WHEN  se activa el ALTA
    THEN  el beneficio queda CONCEDIDO una vez (`RN-P01`, `RN-I06`).
    """
    activador = ActivadorInscripcion()
    activador.activar(
        _contexto(
            "66666666-6666-6666-6666-666666666666",
            referencia_inicial(inscripcion_sin_pagos.id),
            10,
            "activacion:INSCRIPCION:66666666-6666-6666-6666-666666666666",
        )
    )

    assert BeneficioConcedido.objects.count() == 1
    concesion = BeneficioConcedido.objects.get()
    assert concesion.beneficio_id == beneficio.id
    assert concesion.cantidad == beneficio.cantidad


def test_la_ampliacion_no_duplica_el_beneficio_fijo_inicial(
    inscripcion_sin_pagos, beneficio
):
    """GIVEN una inscripción que YA recibió su beneficio `FIJO_INICIAL`
    WHEN  se activa una AMPLIACIÓN
    THEN  el beneficio NO se vuelve a conceder: comprar cupos extra no
       duplica los beneficios fijos (`RN-I06`, `QA-I03`).
    """
    activador = ActivadorInscripcion()
    activador.activar(
        _contexto(
            "77777777-7777-7777-7777-777777777777",
            referencia_inicial(inscripcion_sin_pagos.id),
            10,
            "activacion:INSCRIPCION:77777777-7777-7777-7777-777777777777",
        )
    )
    activador.activar(
        _contexto(
            "88888888-8888-8888-8888-888888888888",
            referencia_expansion(inscripcion_sin_pagos.id, 5),
            5,
            "activacion:INSCRIPCION:88888888-8888-8888-8888-888888888888",
        )
    )

    assert BeneficioConcedido.objects.count() == 1

    inscripcion_sin_pagos.refresh_from_db()
    assert inscripcion_sin_pagos.cupos_pagados == 15


def test_el_beneficio_por_cupo_no_se_concede_mientras_su_regla_este_abierta(
    inscripcion_sin_pagos, beneficio_por_cupo
):
    """GIVEN un beneficio `POR_CUPO`
    WHEN  se activa el alta
    THEN  NO se concede: su regla de reparto por tipo sigue ABIERTA
       (`PD-09`) y concederla sería inventar un derecho con dinero detrás.
    """
    activador = ActivadorInscripcion()
    resultado = activador.activar(
        _contexto(
            "99999999-9999-9999-9999-999999999999",
            referencia_inicial(inscripcion_sin_pagos.id),
            10,
            "activacion:INSCRIPCION:99999999-9999-9999-9999-999999999999",
        )
    )

    assert resultado.exito is True
    assert BeneficioConcedido.objects.count() == 0
    assert (
        BeneficioConcedido.objects.filter(
            beneficio__tipo=TipoBeneficioPaquete.POR_CUPO
        ).count()
        == 0
    )


def test_el_beneficio_fijo_inicial_no_se_concede_dos_veces_en_la_misma_inscripcion(
    inscripcion_sin_pagos, beneficio
):
    """GIVEN dos activaciones con DISTINTAS claves sobre la MISMA inscripción
    WHEN  las dos activan
    THEN  el beneficio `FIJO_INICIAL` sigue concedido UNA sola vez: la
       restricción única de la base de datos es la autoridad (`RN-I06`).
    """
    activador = ActivadorInscripcion()
    activador.activar(
        _contexto(
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            referencia_inicial(inscripcion_sin_pagos.id),
            10,
            "activacion:INSCRIPCION:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
    )
    activador.activar(
        _contexto(
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            referencia_expansion(inscripcion_sin_pagos.id, 3),
            3,
            "activacion:INSCRIPCION:bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )
    )

    assert BeneficioConcedido.objects.count() == 1


# ── La integración con el coordinador de `commerce` ─────────────────────────


def test_el_coordinador_de_commerce_habilita_los_cupos(
    injector, inscripcion_sin_pagos
):
    """GIVEN una compra PAGADA de la inscripción
    WHEN  el coordinador de `commerce` activa el origen
    THEN  los cupos pagados de la inscripción suben UNA vez y la activación
       queda `ACTIVADA` (`RN-C06`, `QA-I02`).
    """
    compra = _compra_pagada(
        inscripcion_sin_pagos,
        referencia_inicial(inscripcion_sin_pagos.id),
        10,
    )

    coordinador = injector.get(CoordinadorActivacionCompra)
    resultado = coordinador.activar_por_compra(compra.id)

    assert resultado.codigo == CODIGO_ACTIVACION_COMPLETADA
    assert resultado.activada is True

    inscripcion_sin_pagos.refresh_from_db()
    assert inscripcion_sin_pagos.cupos_pagados == 10

    activacion = ActivacionCompra.objects.get(compra=compra)
    assert activacion.estado == EstadoActivacionCompra.ACTIVADA


def test_el_coordinador_no_rechama_los_cupos(injector, inscripcion_sin_pagos):
    """GIVEN una compra PAGADA que YA activó sus cupos
    WHEN  el coordinador la activa otra vez
    THEN  el resultado es `ACTIVACION_YA_COMPLETADA` y los cupos NO suman
       otra vez (`RN-C06`).
    """
    compra = _compra_pagada(
        inscripcion_sin_pagos,
        referencia_inicial(inscripcion_sin_pagos.id),
        10,
    )

    coordinador = injector.get(CoordinadorActivacionCompra)
    primera = coordinador.activar_por_compra(compra.id)
    segunda = coordinator_activar_otra_vez(coordinador, compra.id)

    assert primera.codigo == CODIGO_ACTIVACION_COMPLETADA
    assert segunda.codigo == CODIGO_ACTIVACION_YA_COMPLETADA

    inscripcion_sin_pagos.refresh_from_db()
    assert inscripcion_sin_pagos.cupos_pagados == 10


def coordinator_activar_otra_vez(coordinador, compra_id):
    """Activa la misma compra por segunda vez."""
    return coordinador.activar_por_compra(compra_id)
