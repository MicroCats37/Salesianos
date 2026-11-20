"""La ACTIVACIÓN de derechos de pases (FND-05) aplicada al dominio de pases.

GIVEN  una compra de pases CONFIRMADA y el contexto congelado del
       coordinador
WHEN   el activador del origen `PASE` recibe el contexto
THEN   el lote pasa a `PAGADA` exactamente una vez, un reintento no vuelve a
       habilitar los pases y una referencia que no es de este módulo se
       rechaza sin adivinar (`FR-04` I-2, `RN-P02`, `QA-P01`).

**NO EJECUTADO.** La verificación en runtime de este paquete está DIFERIDA
por instrucción explícita del usuario. Ver
`evidence/domains/DOM-03-pases-beneficios-cortesia.md` §6.
"""

import pytest

from modules.commerce.domain.schemas.compra_schemas import ContextoActivacionCompra
from modules.salesianos_fest.domain.constants import (
    CODIGO_COMPRA_PASE_NO_ENCONTRADA,
    CODIGO_PASES_ACTIVADOS,
    CODIGO_PASES_YA_ACTIVADOS,
    CODIGO_REFERENCIA_PASE_NO_RECONOCIDA,
)
from modules.salesianos_fest.domain.models import ActivacionPase
from modules.salesianos_fest.domain.services.core.activador_pase import ActivadorPase

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def activador():
    """El activador del origen `PASE`."""
    return ActivadorPase()


def _contexto(lote, clave="activacion:PASE:00000000-0000-0000-0000-000000000000"):
    """El contexto congelado que entrega el coordinador de `commerce`."""
    return ContextoActivacionCompra(
        compra_id=lote.compra_id,
        origen="PASE",
        clave=clave,
        persona_id=lote.comprador_id,
        referencia=lote.referencia,
        total=lote.total,
        moneda=lote.moneda,
        lineas_snapshot=[
            {
                "concepto_tipo": "PASE",
                "concepto_id": str(lote.pase_id),
                "concepto_nombre": lote.pase.nombre,
                "cantidad": lote.cantidad,
                "precio_unitario": "35.00",
                "precio_aplicado": "35.00",
            }
        ],
    )


# ── La activación ───────────────────────────────────────────────────────────


def test_la_activacion_habilita_el_lote(activador, compra_pase_con_compra):
    """GIVEN una compra de pases confirmada
    WHEN  el activador recibe el contexto
    THEN  el lote pasa a `PAGADA` y queda el ACTA de la activación
       (`RN-P02`).
    """
    resultado = activador.activar(_contexto(compra_pase_con_compra))

    assert resultado.exito is True
    assert resultado.codigo == CODIGO_PASES_ACTIVADOS
    assert resultado.detalle["cantidad"] == 2

    compra_pase_con_compra.refresh_from_db()
    assert compra_pase_con_compra.estado == "PAGADA"
    assert ActivacionPase.objects.count() == 1


def test_la_activacion_es_idempotente(activador, compra_pase_con_compra):
    """GIVEN una activación ya aplicada
    WHEN  llega el MISMO contexto otra vez
    THEN  no vuelve a habilitar los pases: la clave es la autoridad del
       «exactamente una vez» (`FR-04` I-2, `QA-P01`).
    """
    contexto = _contexto(compra_pase_con_compra)
    activador.activar(contexto)

    segundo = activador.activar(contexto)

    assert segundo.exito is True
    assert segundo.codigo == CODIGO_PASES_YA_ACTIVADOS
    assert ActivacionPase.objects.count() == 1


def test_una_referencia_ajena_no_se_adivina(activador, compra_pase_con_compra):
    """GIVEN una referencia que NO es de este módulo
    WHEN  llega al activador
    THEN  se rechaza con `REFERENCIA_PASE_NO_RECONOCIDA`: no se inventa a
       quién pertenece la compra.
    """
    contexto = _contexto(compra_pase_con_compra)
    contexto = contexto.model_copy(update={"referencia": "PAQUETE:algo"})

    resultado = activador.activar(contexto)

    assert resultado.exito is False
    assert resultado.codigo == CODIGO_REFERENCIA_PASE_NO_RECONOCIDA
    assert ActivacionPase.objects.count() == 0


def test_una_compra_desconocida_no_se_adivina(activador, compra_pase_con_compra):
    """GIVEN una compra que no corresponde a ningún lote
    WHEN  llega al activador
    THEN  se rechaza con `COMPRA_PASE_NO_ENCONTRADA`.
    """
    contexto = _contexto(compra_pase_con_compra)
    contexto = contexto.model_copy(
        update={"compra_id": "00000000-0000-0000-0000-000000000000"}
    )

    resultado = activador.activar(contexto)

    assert resultado.exito is False
    assert resultado.codigo == CODIGO_COMPRA_PASE_NO_ENCONTRADA
    assert ActivacionPase.objects.count() == 0


def test_un_lote_pendiente_no_habilita_nada(
    compra_pase_pendiente, persona_participante, injector
):
    """GIVEN un lote PENDIENTE
    WHEN  se intenta asignar un beneficiario
    THEN  se rechaza: una compra pendiente NO habilita ningún pase
       (`RN-P02`).
    """
    from asgiref.sync import async_to_sync

    from modules.salesianos_fest.domain.exceptions import CompraPaseNoPagadaError
    from modules.salesianos_fest.domain.schemas.pase_schemas import (
        AsignarBeneficiarioData,
    )
    from modules.salesianos_fest.domain.services.flujos.beneficiario_flujo import (
        BeneficiarioFlujo,
    )

    flujo = injector.get(BeneficiarioFlujo)

    with pytest.raises(CompraPaseNoPagadaError):
        async_to_sync(flujo.asignar_beneficiario)(
            compra_pase_pendiente.id,
            AsignarBeneficiarioData(
                persona_id=str(persona_participante.id),
                motivo="Asignación de la prueba.",
            ),
            None,
        )
