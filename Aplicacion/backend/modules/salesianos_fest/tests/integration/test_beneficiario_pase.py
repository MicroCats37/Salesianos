"""La ASIGNACIÓN de un pase comprado a una persona.

GIVEN  un lote de pases PAGADO y su titular
WHEN   se asigna un beneficiario, se repite la asignación y se intenta
       asignar sobre un lote pendiente
THEN   sólo se asigna la capacidad pagada, un derecho NO se duplica y el
       acceso al lote es de ÁMBITO POR COMPRA (`RN-P02`, `RN-P04`, `RN-P07`,
       `QA-P02`).

**NO EJECUTADO.** La verificación en runtime de este paquete está DIFERIDA
por instrucción explícita del usuario. Ver
`evidence/domains/DOM-03-pases-beneficios-cortesia.md` §6.
"""

import pytest
from asgiref.sync import async_to_sync

from modules.salesianos_fest.domain.exceptions import (
    CompraPaseNoAutorizadaError,
    CompraPaseNoEncontradaError,
    CompraPaseNoPagadaError,
    PaseDuplicadoError,
    SinPasesDisponiblesError,
    TokenPaseInvalidoError,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import (
    AsignarBeneficiarioData,
    RevocarBeneficiarioData,
)
from modules.salesianos_fest.domain.services.flujos.beneficiario_flujo import (
    BeneficiarioFlujo,
)
from modules.salesianos_fest.domain.services.orchestrators.pase_orchestrator import (
    PaseOrchestrator,
)

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def flujo(injector):
    """El flujo de beneficiarios, resuelto por el inyector real."""
    return injector.get(BeneficiarioFlujo)


@pytest.fixture
def orquestador(injector):
    """El orquestador de pases, resuelto por el inyector real."""
    return injector.get(PaseOrchestrator)


def _asignacion(persona_id=None, documento=None):
    """La intención de asignar un pase a una persona."""
    return AsignarBeneficiarioData(
        persona_id=str(persona_id) if persona_id else None,
        tipo_documento="DNI" if documento else None,
        numero_documento=documento,
        nombres="" if persona_id else "Beneficiario",
        apellidos="" if persona_id else "De Prueba",
        motivo="Asignación de la prueba.",
    )


# ── La capacidad pagada ─────────────────────────────────────────────────────


def test_asignar_a_un_lote_pendiente_se_rechaza(
    flujo, compra_pase_pendiente, persona_participante
):
    """GIVEN un lote PENDIENTE
    WHEN  se intenta asignar un beneficiario
    THEN  se rechaza con `COMPRA_PASE_NO_PAGADA`: una compra pendiente NO
       habilita ningún pase (`RN-P02`).
    """
    with pytest.raises(CompraPaseNoPagadaError):
        async_to_sync(flujo.asignar_beneficiario)(
            compra_pase_pendiente.id,
            _asignacion(persona_id=persona_participante.id),
            None,
        )


def test_asignar_reduce_la_capacidad_disponible(
    flujo, compra_pase_pagada, persona_participante
):
    """GIVEN un lote pagado de dos pases
    WHEN  se asigna un beneficiario
    THEN  la capacidad asignada sube y la disponible baja: la aritmética la
       hace el servidor (`RN-C07`).
    """
    resultado = async_to_sync(flujo.asignar_beneficiario)(
        compra_pase_pagada.id,
        _asignacion(persona_id=persona_participante.id),
        None,
    )

    assert resultado.asignados == 1
    assert resultado.disponibles == 1
    assert len(resultado.beneficiarios) == 1
    assert resultado.beneficiarios[0].origen == "COMPRA"


def test_no_se_asigna_mas_de_la_capacidad_comprada(
    flujo, compra_pase_pagada, persona_participante, persona_otro_participante
):
    """GIVEN un lote pagado de DOS pases
    WHEN  se asignan tres personas distintas
    THEN  la tercera se rechaza con `SIN_PASES_DISPONIBLES`: sólo se
       asigna lo comprado (`RN-P02`).
    """
    async_to_sync(flujo.asignar_beneficiario)(
        compra_pase_pagada.id,
        _asignacion(persona_id=persona_participante.id),
        None,
    )
    async_to_sync(flujo.asignar_beneficiario)(
        compra_pase_pagada.id,
        _asignacion(persona_id=persona_otro_participante.id),
        None,
    )

    with pytest.raises(SinPasesDisponiblesError):
        async_to_sync(flujo.asignar_beneficiario)(
            compra_pase_pagada.id,
            _asignacion(documento="56565656"),
            None,
        )


# ── El beneficiario puede no ser el comprador ──────────────────────────────


def test_el_beneficiario_puede_no_ser_el_comprador(
    flujo, compra_pase_pagada, persona_participante
):
    """GIVEN un lote comprado por una persona
    WHEN  se asigna el pase a OTRA persona
    THEN  el derecho es de la OTRA: el comprador y quien asiste pueden ser
       distintos (`RN-P04`).
    """
    resultado = async_to_sync(flujo.asignar_beneficiario)(
        compra_pase_pagada.id,
        _asignacion(persona_id=persona_participante.id),
        None,
    )

    beneficiario = resultado.beneficiarios[0]
    assert beneficiario.persona_id == str(persona_participante.id)
    assert beneficiario.persona_id != str(compra_pase_pagada.comprador_id)


def test_el_beneficiario_se_resuelve_por_documento(
    flujo, compra_pase_pagada, persona_otro_participante
):
    """GIVEN un lote pagado
    WHEN  se asigna por DOCUMENTO
    THEN  se resuelve la persona del padrón y se registra si no existía
       (`FL-06` paso 5).
    """
    resultado = async_to_sync(flujo.asignar_beneficiario)(
        compra_pase_pagada.id,
        _asignacion(documento=persona_otro_participante.numero_documento),
        None,
    )

    assert resultado.beneficiarios[0].persona_id == str(
        persona_otro_participante.id
    )


# ── La no duplicación ───────────────────────────────────────────────────────


def test_no_se_duplica_un_derecho_activo(
    flujo, compra_pase_pagada, persona_participante
):
    """GIVEN una persona que YA tiene un derecho activo de ese pase
    WHEN  se intenta asignarle otro
    THEN  se rechaza con `PASE_DUPLICADO`: la base de datos es la autoridad
       (`RN-P07`).
    """
    async_to_sync(flujo.asignar_beneficiario)(
        compra_pase_pagada.id,
        _asignacion(persona_id=persona_participante.id),
        None,
    )

    with pytest.raises(PaseDuplicadoError):
        async_to_sync(flujo.asignar_beneficiario)(
            compra_pase_pagada.id,
            _asignacion(persona_id=persona_participante.id),
            None,
        )


def test_no_se_duplica_una_cortesia_con_una_compra(
    flujo, compra_pase_pagada, persona_ajena, cortesia_pase
):
    """GIVEN una persona con una CORTESÍA activa de ese pase
    WHEN  se intenta asignarle un pase comprado
    THEN  se rechaza con `PASE_DUPLICADO`: los dos orígenes comparten la
       misma regla (`RN-P02`, `RN-P07`).
    """
    with pytest.raises(PaseDuplicadoError):
        async_to_sync(flujo.asignar_beneficiario)(
            compra_pase_pagada.id,
            _asignacion(persona_id=persona_ajena.id),
            None,
        )


# ── El acceso al lote ───────────────────────────────────────────────────────


def test_sin_credencial_no_se_abre_el_lote(
    orquestador, compra_pase_pagada, persona_participante
):
    """GIVEN un lote pagado
    WHEN  se consulta SIN cuenta y SIN token
    THEN  se rechaza con `TOKEN_PASE_INVALIDO` (401): la autenticación va
       antes que la autorización.
    """
    with pytest.raises(TokenPaseInvalidoError):
        async_to_sync(orquestador.obtener_compra)(
            None,
            compra_pase_pagada.id,
            None,
        )


def test_el_token_de_otra_compra_no_abre_este_lote(
    orquestador, compra_pase_pagada, persona_participante
):
    """GIVEN un token que NO es el de esta compra
    WHEN  se intenta abrir este lote
    THEN  se rechaza: el token es de ÁMBITO POR COMPRA (`contratos/02` §5).
    """
    from modules.salesianos_fest.domain.services.core.pase_core_service import (
        PaseCoreService,
    )

    with pytest.raises(TokenPaseInvalidoError):
        async_to_sync(orquestador.obtener_compra)(
            None,
            compra_pase_pagada.id,
            PaseCoreService.generar_token(),
        )


def test_el_token_del_enlace_abre_su_lote(
    orquestador, compra_pase_pagada, persona_participante
):
    """GIVEN el token de la compra
    WHEN  se consulta SIN cuenta
    THEN  se abre: el token es la credencial del enlace de gestión
       (`contratos/02` §5).
    """
    resultado = async_to_sync(orquestador.obtener_compra)(
        None,
        compra_pase_pagada.id,
        compra_pase_pagada.token,
    )

    assert resultado.compra_pase_id == str(compra_pase_pagada.id)


def test_el_titular_autenticado_abre_su_lote(
    orquestador, compra_pase_pagada, persona_participante, usuario_responsable
):
    """GIVEN la cuenta del COMPRADOR
    WHEN  se consulta el lote SIN token
    THEN  se abre: la titularidad la decide el módulo dueño (`FR-03` §2.1).
    """
    resultado = async_to_sync(orquestador.obtener_compra)(
        usuario_responsable,
        compra_pase_pagada.id,
        None,
    )

    assert resultado.compra_pase_id == str(compra_pase_pagada.id)


def test_una_cuenta_ajena_no_abre_el_lote(
    orquestador, compra_pase_pagada, persona_participante, usuario_ajeno
):
    """GIVEN una cuenta que NO es la compradora
    WHEN  se consulta el lote
    THEN  se rechaza con 403: una cuenta ajena no sustituye la titularidad
       (`FR-03` §2.1 regla 3).
    """
    with pytest.raises(CompraPaseNoAutorizadaError):
        async_to_sync(orquestador.obtener_compra)(
            usuario_ajeno,
            compra_pase_pagada.id,
            None,
        )


# ── La revocación ───────────────────────────────────────────────────────────


def test_revocar_es_permanente_y_auditada(
    flujo, compra_pase_pagada, beneficiario_pase, usuario_responsable
):
    """GIVEN un derecho activo
    WHEN  se revoca
    THEN  queda `REVOCADO`, con instante y motivo: la revocación es
       permanente y auditada (`RN-P08`, `FR-05` §2.3).
    """
    resultado = async_to_sync(flujo.revocar_beneficiario)(
        compra_pase_pagada.id,
        beneficiario_pase.persona_id,
        RevocarBeneficiarioData(motivo="Solicitud del titular."),
        usuario_responsable,
    )

    assert resultado.estado == "REVOCADO"
    assert resultado.ya_revocado is False
    assert resultado.motivo == "Solicitud del titular."
    assert resultado.revocado_en is not None


def test_revocar_dos_veces_es_idempotente(
    flujo, compra_pase_pagada, beneficiario_pase, usuario_responsable
):
    """GIVEN un derecho ya revocado
    WHEN  se revoca otra vez
    THEN  NO es un error: informa del estado final (`FR-05` §2.3).
    """
    async_to_sync(flujo.revocar_beneficiario)(
        compra_pase_pagada.id,
        beneficiario_pase.persona_id,
        RevocarBeneficiarioData(motivo="Primera."),
        usuario_responsable,
    )

    resultado = async_to_sync(flujo.revocar_beneficiario)(
        compra_pase_pagada.id,
        beneficiario_pase.persona_id,
        RevocarBeneficiarioData(motivo="Segunda."),
        usuario_responsable,
    )

    assert resultado.ya_revocado is True
    assert resultado.estado == "REVOCADO"


def test_la_revocacion_no_devuelve_la_unidad(
    flujo, compra_pase_pagada, beneficiario_pase, usuario_responsable
):
    """GIVEN un derecho revocado
    WHEN  se consulta el lote
    THEN  la unidad sigue ocupada: la revocación NO devuelve el cupo
       (`FR-05` §2.3). La política de reasignación sigue ABIERTA (`PD-02`).
    """
    async_to_sync(flujo.revocar_beneficiario)(
        compra_pase_pagada.id,
        beneficiario_pase.persona_id,
        RevocarBeneficiarioData(motivo="Motivo."),
        usuario_responsable,
    )

    resultado = async_to_sync(flujo.obtener_beneficiarios)(compra_pase_pagada.id)

    assert resultado.asignados == 1
    assert resultado.disponibles == 1


def test_un_lote_inexistente_es_404(flujo, persona_participante):
    """GIVEN un identificador de lote que no existe
    WHEN  se consulta
    THEN  se rechaza con `COMPRA_PASE_NO_ENCONTRADA` (404).
    """
    with pytest.raises(CompraPaseNoEncontradaError):
        async_to_sync(flujo.obtener_beneficiarios)(
            "00000000-0000-0000-0000-000000000000"
        )
