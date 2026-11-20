"""Tests del acta de auditoría transversal.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

GIVEN  una acción sensible ejecutada por un administrador
WHEN   se registra y se lee su acta
THEN   el acta nombra QUIÉN, CUÁNDO, QUÉ y POR QUÉ, exige el motivo y no
       guarda secretos ni el contexto crudo.
"""

import pytest

from core.exceptions import UnprocessableEntityError
from modules.administracion.domain.selectors.admin_auditoria_selector import (
    AdminAuditoriaSelector,
)
from modules.administracion.domain.services.core.admin_auditoria_service import (
    sanear_datos,
)


def test_el_contexto_auditable_no_guarda_claves_prohibidas():
    limpio = sanear_datos({"password": "secreto", "token": "abc", "cantidad": 3})

    assert limpio == {"cantidad": 3}


def test_la_accion_sensible_exige_un_motivo(servicio_auditoria):
    with pytest.raises(UnprocessableEntityError):
        servicio_auditoria.registrar(
            None,
            "RETIRAR_PARTICIPANTE",
            "INSCRIPCION",
            "   ",
        )


def test_el_acta_nombra_actor_momento_y_motivo(
    db,
    servicio_auditoria,
    edicion_publicada,
    usuario_responsable,
):
    acta = servicio_auditoria.registrar(
        usuario_responsable,
        "RETIRAR_PARTICIPANTE",
        "INSCRIPCION",
        "El participante no pertenece a la edición",
        edicion_id=edicion_publicada.id,
        entidad_id="registro-1",
        datos={"password": "secreto", "motivo_corto": "ok"},
    )

    assert acta.motivo == "El participante no pertenece a la edición"
    assert acta.accion == "RETIRAR_PARTICIPANTE"
    assert acta.entidad == "INSCRIPCION"
    assert acta.created_at is not None
    assert "password" not in acta.datos
    assert acta.datos["motivo_corto"] == "ok"

    listado = AdminAuditoriaSelector().listar(edicion_id=edicion_publicada.id)

    assert listado.total == 1
    assert listado.items[0].actor
    assert listado.items[0].motivo == "El participante no pertenece a la edición"


def test_el_acta_no_publica_el_contexto_crudo(servicio_auditoria):
    from modules.administracion.presentation.presenters.admin_auditoria_presenter import (
        AdminAuditoriaPresenter,
    )
    from modules.administracion.domain.results.admin_resultados import (
        AuditoriaItemResultado,
    )
    from datetime import datetime

    item = AuditoriaItemResultado(
        id="1",
        edicion_id=None,
        actor="Administrador",
        accion="RETIRAR_PARTICIPANTE",
        entidad="INSCRIPCION",
        entidad_id="registro-1",
        motivo="Motivo declarado",
        registrado_en=datetime(2026, 1, 1),
    )

    forma = AdminAuditoriaPresenter.present_item(item)

    assert forma.actor == "Administrador"
    assert forma.motivo == "Motivo declarado"
    assert not hasattr(forma, "datos")
