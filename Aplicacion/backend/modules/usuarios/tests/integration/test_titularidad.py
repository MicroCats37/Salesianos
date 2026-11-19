"""
Titularidad: rol, recurso y conocimiento del documento.

GIVEN: una cuenta autenticada y un recurso que pertenece a otra persona.
WHEN: se comprueba la titularidad.
THEN: la respuesta es la del recurso, el grupo NO sustituye la titularidad y
conocer un documento NO da acceso a la operación de otro
(`RN-U02`, `RN-U04`).

Cubre `FR-03` §2 · `RN-U02` · `RN-U04`.
"""

import pytest

from modules.usuarios.domain.constants import TitularidadChoices
from modules.usuarios.domain.services.core.titularidad_service import (
    RecursoTitularidad,
    TitularidadService,
)


@pytest.fixture
def servicio_titularidad():
    """Servicio de titularidad con su grupo funcional."""
    return TitularidadService()


@pytest.mark.django_db(transaction=True)
def test_el_responsable_es_titular_de_su_recurso(
    servicio_titularidad,
    cuenta_con_persona,
):
    """GIVEN una cuenta con persona · WHEN se comprueba la titularidad del
    recurso que le pertenece · THEN es titular (`FR-03` §2 fila 1)."""
    recurso = RecursoTitularidad(responsable_id=str(cuenta_con_persona.persona_fk_id))

    resultado = servicio_titularidad.verificar(
        titularidad=TitularidadChoices.RESPONSABLE.value,
        usuario=cuenta_con_persona,
        recurso=recurso,
    )

    assert resultado.permitida is True
    assert resultado.titularidad == "TITULARIDAD_RESPONSABLE"


@pytest.mark.django_db(transaction=True)
def test_un_responsable_ajeno_no_es_titular(
    servicio_titularidad,
    cuenta_con_persona,
    persona_creada,
):
    """GIVEN una cuenta · WHEN se comprueba un recurso de OTRA persona ·
    THEN no es titular (`FR-03` §2.1 regla 4)."""
    recurso = RecursoTitularidad(responsable_id="otro-identificador")

    resultado = servicio_titularidad.verificar(
        titularidad=TitularidadChoices.RESPONSABLE.value,
        usuario=cuenta_con_persona,
        recurso=recurso,
    )

    assert resultado.permitida is False
    assert resultado.motivo == "NO_ES_TITULAR"


@pytest.mark.django_db(transaction=True)
def test_el_comprador_es_titular_de_su_compra(
    servicio_titularidad,
    cuenta_con_persona,
):
    """GIVEN una cuenta · WHEN se comprueba la titularidad de su compra ·
    THEN es titular (`FR-03` §2 fila 2)."""
    recurso = RecursoTitularidad(persona_id=str(cuenta_con_persona.persona_fk_id))

    resultado = servicio_titularidad.verificar(
        titularidad=TitularidadChoices.COMPRADOR.value,
        usuario=cuenta_con_persona,
        recurso=recurso,
    )

    assert resultado.permitida is True


@pytest.mark.django_db(transaction=True)
def test_un_beneficiario_con_derecho_revocado_no_es_titular(
    servicio_titularidad,
    cuenta_con_persona,
):
    """GIVEN un pase revocado · WHEN se comprueba la titularidad del
    beneficiario · THEN no es titular (`FR-03` §2 fila 3)."""
    recurso = RecursoTitularidad(
        persona_id=str(cuenta_con_persona.persona_fk_id),
        derecho_revocado=True,
    )

    resultado = servicio_titularidad.verificar(
        titularidad=TitularidadChoices.BENEFICIARIO.value,
        usuario=cuenta_con_persona,
        recurso=recurso,
    )

    assert resultado.permitida is False
    assert resultado.motivo == "DERECHO_REVOCADO"


@pytest.mark.django_db(transaction=True)
def test_el_grupo_administrador_da_titularidad_de_administracion(
    servicio_titularidad,
    usuario_administrador,
):
    """GIVEN una cuenta del grupo `Administrador` · WHEN se comprueba la
    titularidad de administración · THEN es titular (`FR-03` §2 fila 4)."""
    resultado = servicio_titularidad.verificar(
        titularidad=TitularidadChoices.ADMIN.value,
        usuario=usuario_administrador,
        recurso=RecursoTitularidad(),
    )

    assert resultado.permitida is True


@pytest.mark.django_db(transaction=True)
def test_una_cuenta_normal_no_administra(
    servicio_titularidad,
    usuario_normal,
):
    """GIVEN una cuenta `Normal` · WHEN se comprueba la titularidad de
    administración · THEN no es titular."""
    resultado = servicio_titularidad.verificar(
        titularidad=TitularidadChoices.ADMIN.value,
        usuario=usuario_normal,
        recurso=RecursoTitularidad(),
    )

    assert resultado.permitida is False


@pytest.mark.django_db(transaction=True)
def test_el_grupo_no_sustituye_la_titularidad(
    servicio_titularidad,
    usuario_administrador,
):
    """GIVEN una cuenta administradora · WHEN se comprueba si es responsable
    de una inscripción ajena · THEN NO lo es (`FR-03` §2.1 regla 3)."""
    recurso = RecursoTitularidad(responsable_id="responsable-de-otra-persona")

    resultado = servicio_titularidad.verificar(
        titularidad=TitularidadChoices.RESPONSABLE.value,
        usuario=usuario_administrador,
        recurso=recurso,
    )

    assert resultado.permitida is False


@pytest.mark.django_db(transaction=True)
async def test_conocer_un_documento_no_autoriza_la_operacion_de_otro(
    auth_client,
    cuenta_con_persona,
    consulta_documento_client,
):
    """GIVEN una cuenta que resuelve el documento de OTRA persona · WHEN se
    comprueba la titularidad de esa persona sobre SU recurso · THEN la
    cuenta NO es titular (`RN-U04` — el DNI es identificador, no credencial)."""
    from modules.usuarios.domain.constants import EstadoConsultaDocumentoChoices
    from modules.usuarios.tests.fixtures.factories import make_resolver_payload
    from modules.usuarios.tests.fixtures.persona_fixtures import (
        construir_resultado_externo,
    )

    consulta_documento_client.resultado = construir_resultado_externo(
        estado=EstadoConsultaDocumentoChoices.ENCONTRADO,
        numero_documento="99999999",
        nombre_completo="OTRO, PERSONA",
    )
    respuesta = await auth_client.post(
        "/personas/resolver",
        json=make_resolver_payload(numero_documento="99999999"),
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["origen"] == "EXTERNO"

    # El recurso pertenece a la persona resuelta, que NO es la cuenta
    # autenticada: la titularidad se rechaza.
    recurso = RecursoTitularidad(responsable_id="99999999")
    veredicto = TitularidadService().verificar(
        titularidad=TitularidadChoices.RESPONSABLE.value,
        usuario=cuenta_con_persona,
        recurso=recurso,
    )

    assert veredicto.permitida is False
    assert veredicto.motivo == "NO_ES_TITULAR"


@pytest.mark.django_db(transaction=True)
def test_una_cuenta_sin_persona_no_puede_ser_titular(
    servicio_titularidad,
    cuenta_sin_persona,
):
    """GIVEN una cuenta técnica sin `Persona` · WHEN se comprueba una
    titularidad de persona · THEN se rechaza (`FR-03` §2 fila 1 — la
    persona debe estar vinculada a la cuenta)."""
    recurso = RecursoTitularidad(responsable_id="cualquier-identificador")

    resultado = servicio_titularidad.verificar(
        titularidad=TitularidadChoices.RESPONSABLE.value,
        usuario=cuenta_sin_persona,
        recurso=recurso,
    )

    assert resultado.permitida is False
    assert resultado.motivo == "SIN_PERSONA_VINCULADA"
