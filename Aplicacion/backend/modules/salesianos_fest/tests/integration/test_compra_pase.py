"""La COMPRA de un lote de pases, con cuenta y como invitado.

GIVEN  un pase vigente con precio en la edición
WHEN   un visitante compra pases sin cuenta, o una cuenta compra pases
THEN   la compra queda PENDIENTE, el importe lo congela el servidor, NO se
       crea ninguna cuenta y un reintento RECUPERA la misma compra
       (`FL-06`, `RN-C02`, `RN-P02`, `QA-P01`).

**NO EJECUTADO.** La verificación en runtime de este paquete está DIFERIDA
por instrucción explícita del usuario: las pruebas se ESCRIBEN pero no se
ejecutan. Ver `evidence/domains/DOM-03-pases-beneficios-cortesia.md` §6.
"""

from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.salesianos_fest.domain.exceptions import (
    CantidadInvalidaError,
    PaseNoDisponibleError,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import ComprarPaseData
from modules.salesianos_fest.domain.services.flujos.compra_pase_flujo import (
    CompraPaseFlujo,
)
from modules.usuarios.domain.models import Persona, Usuario

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def flujo(injector):
    """El flujo de compra de pases, resuelto por el inyector real."""
    return injector.get(CompraPaseFlujo)


def _datos(pase, cantidad=2, documento="99999999"):
    """La intención de compra de un invitado."""
    return ComprarPaseData(
        pase_id=str(pase.id),
        cantidad=cantidad,
        tipo_documento="DNI",
        numero_documento=documento,
        nombres="Visitante",
        apellidos="Invitado",
        contacto_email="visitante@example.com",
    )


# ── La compra sin cuenta ────────────────────────────────────────────────────


def test_la_compra_invitada_no_crea_ninguna_cuenta(flujo, pase):
    """GIVEN una compra de un visitante SIN cuenta
    WHEN  se completa la compra
    THEN  se registra una `Persona` —identidad civil— y NINGÚN `Usuario`
       (`FL-06` paso 2, `FR-03` §1.1: la `Persona` existe sin cuenta).
    """
    cuentas_antes = Usuario.objects.count()
    personas_antes = Persona.objects.count()

    resultado = async_to_sync(flujo.comprar_pase)(_datos(pase), None)

    assert Usuario.objects.count() == cuentas_antes
    assert Persona.objects.count() == personas_antes + 1
    assert resultado.comprador_persona_id


def test_la_compra_invitada_deja_el_lote_pendiente(flujo, pase):
    """GIVEN una compra recién creada
    WHEN  se consulta el lote
    THEN  queda `PENDIENTE`: una compra pendiente NO habilita ningún pase
       (`RN-P02`, `QA-P01`).
    """
    resultado = async_to_sync(flujo.comprar_pase)(_datos(pase), None)

    assert resultado.estado == "PENDIENTE"
    assert resultado.cantidad == 2


def test_el_precio_lo_congela_el_servidor(flujo, pase):
    """GIVEN un pase con precio vigente
    WHEN  se compra
    THEN  el total es el DERIVADO del catálogo, no un importe del cliente
       (`RN-C02`).
    """
    resultado = async_to_sync(flujo.comprar_pase)(_datos(pase, cantidad=2), None)

    assert resultado.precio_unitario == Decimal("35.00")
    assert resultado.total == Decimal("70.00")
    assert resultado.moneda == "PEN"


def test_un_reintento_recupera_la_misma_compra(flujo, pase):
    """GIVEN una compra pendiente
    WHEN  se repite la misma intención
    THEN  se RECUPERA la misma compra: no se duplica (`FR-04` I-4).
    """
    primera = async_to_sync(flujo.comprar_pase)(_datos(pase), None)
    segunda = async_to_sync(flujo.comprar_pase)(_datos(pase), None)

    assert primera.compra_pase_id == segunda.compra_pase_id
    assert primera.compra_id == segunda.compra_id
    assert segunda.reutilizada is True
    assert segunda.causa_operativa == "COMPRA_PASE_REUTILIZADA"


# ── La compra con cuenta ────────────────────────────────────────────────────


def test_el_comprador_autenticado_es_el_actor(flujo, pase, usuario_responsable):
    """GIVEN una petición AUTENTICADA
    WHEN  se compra
    THEN  el comprador es el ACTOR: el documento del payload se IGNORA
       (`FR-03` §2.1 — la identidad sale de la cuenta, no del documento).
    """
    datos = _datos(pase, documento="88888888")

    resultado = async_to_sync(flujo.comprar_pase)(
        datos,
        usuario_responsable,
    )

    assert resultado.comprador_persona_id == str(usuario_responsable.persona_fk_id)


def test_la_cuenta_autenticada_no_puede_comprar_en_nombre_de_otro(
    flujo, pase, usuario_responsable
):
    """GIVEN una cuenta autenticada
    WHEN  declara el documento de OTRA persona
    THEN  el servidor compra en nombre del ACTOR (`RN-U04`: el documento no es
       una credencial).
    """
    datos = _datos(pase, documento="77777777")

    resultado = async_to_sync(flujo.comprar_pase)(datos, usuario_responsable)

    assert resultado.comprador_persona_id == str(usuario_responsable.persona_fk_id)
    assert not Persona.objects.filter(numero_documento="77777777").exists()


# ── Los rechazos ────────────────────────────────────────────────────────────


def test_una_cantidad_fuera_de_limites_se_rechaza(flujo, pase):
    """GIVEN una cantidad que no está dentro de los límites de dominio
    WHEN  se intenta comprar
    THEN  se rechaza con `CANTIDAD_INVALIDA` (422, código CONGELADO).
    """
    with pytest.raises(CantidadInvalidaError):
        async_to_sync(flujo.comprar_pase)(_datos(pase, cantidad=51), None)


def test_un_pase_sin_precio_no_se_compra(flujo, pase_sin_precio):
    """GIVEN un pase VIGENTE sin precio vigente
    WHEN  se intenta comprar
    THEN  se rechaza con `PASE_NO_DISPONIBLE`: no hay precio de reserva
       (`FL-01` paso 3).
    """
    with pytest.raises(PaseNoDisponibleError):
        async_to_sync(flujo.comprar_pase)(_datos(pase_sin_precio), None)


def test_un_pase_retirado_no_se_compra(flujo, pase_retirado):
    """GIVEN un pase `RETIRADO`
    WHEN  se intenta comprar
    THEN  se rechaza con `PASE_NO_DISPONIBLE` (409, código CONGELADO).
    """
    with pytest.raises(PaseNoDisponibleError):
        async_to_sync(flujo.comprar_pase)(_datos(pase_retirado), None)


# ── El token de gestión ─────────────────────────────────────────────────────


def test_la_compra_entrega_un_token_de_gestión(flujo, pase):
    """GIVEN una compra recién creada
    WHEN  se consulta el resultado
    THEN  entrega un token privado con vencimiento: es la credencial del
       enlace de gestión (`contratos/02` §5).
    """
    resultado = async_to_sync(flujo.comprar_pase)(_datos(pase), None)

    assert resultado.token
    assert len(resultado.token) >= 32
    assert resultado.token_expira_en is not None


def test_el_token_es_distinto_en_cada_compra(flujo, pase):
    """GIVEN dos compras de personas DISTINTAS
    WHEN  se crean
    THEN  cada una tiene SU token: la credencial no se comparte.
    """
    primera = async_to_sync(flujo.comprar_pase)(
        _datos(pase, documento="11111199"),
        None,
    )
    segunda = async_to_sync(flujo.comprar_pase)(
        _datos(pase, documento="22222299"),
        None,
    )

    assert primera.token != segunda.token
