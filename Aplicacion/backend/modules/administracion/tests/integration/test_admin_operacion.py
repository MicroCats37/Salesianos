"""Tests de la CAPA OPERATIVA del panel (work unit 2 de `XCT-02`).

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

GIVEN  una edición publicada con sus inscripciones, equipos y participantes
WHEN   el panel lee el listado operativo, aplica un filtro y ejecuta un
       comando sensible
THEN   el filtro declarado por el resumen es el MISMO que acepta el
       listado, el comando exige MOTIVO, rechaza una VERSIÓN desfasada y
       deja el ACTA, y un actor sin capacidad NO puede entrar.

> **Estas suites están ESCRITAS y NO EJECUTADAS.** La restricción vigente del
> paquete no permite ejecutar `pytest`. Nada de lo que sigue puede leerse
> como un resultado verde.
"""

import pytest

from core.exceptions import ConflictError, UnprocessableEntityError
from core.permissions import RequireAdminVer
from modules.administracion.domain.constants import (
    FiltroResumen,
    ValorEstadoPago,
    ValorPlantilla,
)
from modules.administracion.domain.services.core.admin_accion_sensible_service import (
    AdminAccionSensibleService,
)
from modules.administracion.domain.services.core.admin_auditoria_service import (
    AdminAuditoriaService,
)
from modules.administracion.domain.services.core.admin_operacion_service import (
    AdminOperacionService,
)
from modules.administracion.presentation.presenters.admin_resumen_presenter import (
    AdminResumenPresenter,
)


# ── Fixtures de este paquete ─────────────────────────────────────────────────


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


class _EstadoCompraDePrueba:
    """El puerto de estado de la compra, con una respuesta de prueba.

    La compra NO está pagada: el veredicto que publica el dueño es
    `PAGADA_SIN_LIQUIDAR` y el panel lo COPIA, no lo recalcula.
    """

    def obtener_estado_compra(self, orden_pago_id: str):
        class _Estado:
            pagada = False
            cancelada = False

        return _Estado()


class _ActivacionDePrueba:
    """El puerto de activación de derechos, con una respuesta de prueba.

    No hay activación registrada: el SEGUNDO canal del veredicto es
    `SIN_ACTIVACION` y el panel lo COPIA, no lo recalcula.

    Es el segundo puerto que `EstadoOperativoPagoService` recibe (XCT-03 lo
    añadió cuando publicó el canal `estado_activacion`).
    """

    def estado_activacion(self, orden_pago_id: str):
        from modules.pagos.domain.schemas.pago_schemas import (
            EstadoActivacionCompraData,
        )

        return EstadoActivacionCompraData(existe=False)

    def activar_por_orden(self, orden_pago_id: str):  # pragma: no cover
        raise NotImplementedError(
            "Este test no activa derechos: sólo consulta el veredicto."
        )


@pytest.fixture
def servicio_accion():
    """El servicio de las acciones sensibles."""
    return AdminAccionSensibleService(AdminAuditoriaService())


@pytest.fixture
def admin(db):
    """Un actor con la capacidad `admin.ver`."""
    from modules.usuarios.domain.models import Usuario

    return Usuario.objects.create_user(
        username="admin.operativo",
        password="Prueba-12345",
        is_staff=True,
    )


# ── El filtro del drilldown es el MISMO que acepta el listado ────────────────


def test_el_filtro_estado_pago_devuelve_las_inscripciones_sin_pagar(
    db,
    servicio_operacion,
    edicion_publicada,
    inscripcion,
    inscripcion_sin_pagos,
):
    """El filtro DECLARADO por el resumen devuelve exactamente su drilldown."""
    items, total, *_ = servicio_operacion.listar_inscripciones(
        edicion_publicada.id,
        estado_pago=ValorEstadoPago.PENDIENTE,
    )

    assert total == 1
    assert [item.id for item in items] == [str(inscripcion_sin_pagos.id)]
    assert str(inscripcion.id) not in [item.id for item in items]


def test_el_filtro_plantilla_devuelve_los_equipos_incompletos(
    db,
    servicio_operacion,
    edicion_publicada,
    equipo,
    disciplina,
):
    """`plantilla=INCOMPLETA` usa el mínimo que publica la disciplina."""
    items, total, *_ = servicio_operacion.listar_equipos(
        edicion_publicada.id,
        plantilla=ValorPlantilla.INCOMPLETA,
    )

    assert total == 1
    assert items[0].id == str(equipo.id)
    assert items[0].plantilla.minimo == disciplina.minimo_por_equipo
    assert items[0].plantilla.registrados == 0
    assert items[0].estado_operativo.codigo == ValorPlantilla.INCOMPLETA


def test_cada_incidencia_del_resumen_apunta_a_un_filtro_que_el_listado_acepta(
    db,
    servicio_operacion,
    edicion_publicada,
    inscripcion_sin_pagos,
    equipo,
):
    """El drilldown del resumen NO es un enlace roto.

    Cada incidencia declara un filtro del vocabulario cerrado y el listado
    que la atiende lo acepta: el problema visible LLEGA a sus registros.
    """
    from modules.administracion.domain.results.admin_resultados import (
        ResumenIncidenciaResultado,
    )

    incidencias = _selector_resumen().incidencias(edicion_publicada.id)

    assert incidencias

    for incidencia in incidencias:
        forma = AdminResumenPresenter.present_incidencia(incidencia)
        href = forma.accion.href

        assert "/administracion/" in href
        assert "?" in href
        nombre_filtro, valor_filtro = href.split("?", 1)[1].split("=", 1)

        assert nombre_filtro in {
            FiltroResumen.ESTADO_PAGO,
            FiltroResumen.PLANTILLA,
            FiltroResumen.ESTADO_OPERATIVO,
        }
        assert valor_filtro

    # Y el listado de inscripciones acepta el filtro que declara el resumen.
    items, total, *_ = servicio_operacion.listar_inscripciones(
        edicion_publicada.id,
        estado_pago=ValorEstadoPago.PENDIENTE,
    )

    assert total == 1
    assert items[0].alerta is not None
    assert items[0].siguiente_accion is not None
    assert items[0].siguiente_accion.href == (
        "/administracion/pagos?estado_operativo=PENDIENTE"
    )


def _selector_resumen():
    from modules.administracion.domain.selectors.admin_resumen_selector import (
        AdminResumenSelector,
    )

    return AdminResumenSelector()


# ── El comando sensible: MOTIVO, VERSIÓN y ACTA ─────────────────────────────


def test_un_comando_sensible_sin_motivo_es_422(servicio_accion):
    with pytest.raises(UnprocessableEntityError):
        servicio_accion.validar_motivo("   ")


def test_una_version_desfasada_es_409(servicio_accion, db, edicion_publicada):
    """El comando sobre un registro que cambió se rechaza con 409."""
    from modules.salesianos_fest.domain.models import Participacion

    participacion = Participacion(id="x", updated_at=None)

    with pytest.raises(ConflictError):
        servicio_accion.validar_version(participacion, "2000-01-01T00:00:00+00:00")


def test_la_accion_sensible_escribe_el_acta_con_actor_y_motivo(
    db,
    servicio_accion,
    admin,
    edicion_publicada,
):
    """El ACTA nombra QUIÉN, CUÁNDO, QUÉ y POR QUÉ."""
    acta = servicio_accion.registrar_acta(
        actor=admin,
        accion="RETIRAR_PARTICIPANTE",
        entidad="PARTICIPACION",
        motivo="El participante no pertenece a la disciplina",
        edicion_id=str(edicion_publicada.id),
        entidad_id="participacion-1",
        datos={"password": "secreto", "rol": "JUGADOR"},
    )

    assert acta.actor_usuario_id == admin.id
    assert acta.actor_nombre
    assert acta.motivo == "El participante no pertenece a la disciplina"
    assert "password" not in acta.datos
    assert acta.datos["rol"] == "JUGADOR"


# ── Los permisos: 401 antes que 403 ──────────────────────────────────────────


def test_un_actor_sin_capacidad_no_pasa_la_comprobacion(db, admin):
    """La capacidad `admin.ver` es la del mapa ÚNICO del proyecto."""
    from modules.usuarios.domain.models import Usuario

    class _Peticion:
        def __init__(self, usuario):
            self.user = usuario

    usuario = Usuario.objects.create_user(
        username="usuario.sin.capacidad",
        password="Prueba-12345",
    )

    assert RequireAdminVer().has_permission(_Peticion(admin), None) is True
    assert RequireAdminVer().has_permission(_Peticion(usuario), None) is False
    assert RequireAdminVer().has_permission(_Peticion(None), None) is False
