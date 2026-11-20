"""Fixtures del dominio de PASES (`DOM-03`).

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3 — las fixtures viven
aquí; `tests/conftest.py` sólo las importa y registra.

Este archivo NO toca las fixtures de `DOM-01`/`DOM-02`: el módulo `pases`
habilitado en la edición se resuelve en una fixture PROPIA, para que el
catálogo de inscripción siga siendo exactamente el que era.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from modules.commerce.domain.constants import OrigenCompra
from modules.commerce.domain.models import Compra
from modules.eventos.domain.constants import ModuloLogico
from modules.salesianos_fest.domain.constants import (
    EstadoCompraPase,
    EstadoCortesiaPase,
    EstadoDerechoPase,
    EstadoPase,
    OrigenDerechoPase,
)
from modules.salesianos_fest.domain.models import (
    CompraPase,
    CortesiaPase,
    Pase,
    PaseBeneficiario,
    PasePrecio,
)
from modules.salesianos_fest.domain.referencia_pase import referencia_compra_pase
from modules.usuarios.domain.models import Usuario

#: Token de gestión de las fixtures: es una CREDENCIAL y sólo existe en el
#: proceso de prueba.
TOKEN_PASE_FIJO = "token-de-prueba-dom-03-no-usar-en-produccion"


# ── Edición ─────────────────────────────────────────────────────────────────


@pytest.fixture
def edicion_con_pases(db, edicion_publicada):
    """La edición publicada con el módulo `pases` habilitado.

    `RN-E02`: un módulo no habilitado no expone catálogo. Es una fixture
    PROPIA para no alterar el catálogo de inscripción de `DOM-01`.
    """
    edicion_publicada.modulos_habilitados = list(
        edicion_publicada.modulos_habilitados or []
    ) + [ModuloLogico.PASES]
    edicion_publicada.save(update_fields=["modulos_habilitados"])
    return edicion_publicada


# ── Catálogo ────────────────────────────────────────────────────────────────


@pytest.fixture
def pase(db, edicion_con_pases):
    """Pase vigente de la edición, con su precio vigente."""
    pase = Pase.objects.create(
        edicion=edicion_con_pases,
        nombre="Pase FEST",
        slug="pase-fest",
        descripcion="Entrada general del FEST.",
    )
    PasePrecio.objects.create(
        pase=pase,
        monto=Decimal("35.00"),
        moneda="PEN",
        vigente_desde=date.today() - timedelta(days=1),
    )
    return pase


@pytest.fixture
def pase_sin_precio(db, edicion_con_pases):
    """Pase VIGENTE sin precio: NO está a la venta."""
    return Pase.objects.create(
        edicion=edicion_con_pases,
        nombre="Pase sin precio",
        slug="sin-precio",
    )


@pytest.fixture
def pase_retirado(db, edicion_con_pases):
    """Pase `RETIRADO`: no se ofrece ni se compra."""
    return Pase.objects.create(
        edicion=edicion_con_pases,
        nombre="Pase retirado",
        slug="retirado",
        estado=EstadoPase.RETIRADO,
    )


# ── Compras de pases ────────────────────────────────────────────────────────


def _crear_compra_pase(
    *,
    edicion,
    pase,
    comprador,
    cantidad=2,
    estado=EstadoCompraPase.PAGADA,
    token=TOKEN_PASE_FIJO,
    compra=None,
    referencia=None,
):
    """Crea un lote de pases para las fixtures.

    La referencia por defecto es la REFERENCIA DE INTENCIÓN real del módulo
    (`domain/referencia_pase.py`): el activador de derechos la desarma, así
    que una referencia de adorno haría fallar la activación.
    """
    if referencia is None:
        referencia = referencia_compra_pase(
            edicion_id=edicion.id,
            pase_id=pase.id,
            comprador_id=comprador.id,
            cantidad=cantidad,
        )
    return CompraPase.objects.create(
        edicion=edicion,
        pase=pase,
        comprador=comprador,
        cantidad=cantidad,
        asignados=0,
        precio_unitario=Decimal("35.00"),
        total=Decimal("35.00") * cantidad,
        moneda="PEN",
        estado=estado,
        token=token,
        token_expira_en=_vencimiento(),
        referencia=referencia,
        compra=compra,
    )


def _vencimiento():
    """Un instante futuro de vencimiento del token."""
    from django.utils import timezone

    return timezone.now() + timedelta(days=30)


@pytest.fixture
def compra_pase_pagada(db, edicion_con_pases, pase, persona):
    """Un lote YA PAGADO de dos pases, con su token de gestión."""
    return _crear_compra_pase(
        edicion=edicion_con_pases,
        pase=pase,
        comprador=persona,
        cantidad=2,
        estado=EstadoCompraPase.PAGADA,
    )


@pytest.fixture
def compra_pase_pendiente(db, edicion_con_pases, pase, persona):
    """Un lote PENDIENTE: no habilita ningún pase (`RN-P02`)."""
    return _crear_compra_pase(
        edicion=edicion_con_pases,
        pase=pase,
        comprador=persona,
        cantidad=2,
        estado=EstadoCompraPase.PENDIENTE,
        token="token-pendiente-dom-03",
    )


@pytest.fixture
def compra_pase_con_compra(db, edicion_con_pases, pase, persona):
    """Un lote pendiente financiado por una compra real de `commerce`.

    Es el caso que necesita la ACTIVACIÓN de derechos (`FND-05`): el lote se
    resuelve por `compra_id`.
    """
    referencia = referencia_compra_pase(
        edicion_id=edicion_con_pases.id,
        pase_id=pase.id,
        comprador_id=persona.id,
        cantidad=2,
    )
    compra = Compra.objects.create(
        persona=persona,
        origen=OrigenCompra.PASE,
        total=Decimal("70.00"),
        moneda="PEN",
        lineas_snapshot=[
            {
                "concepto_tipo": "PASE",
                "concepto_id": str(pase.id),
                "concepto_nombre": pase.nombre,
                "cantidad": 2,
                "precio_unitario": "35.00",
                "precio_aplicado": "35.00",
            }
        ],
        referencia=referencia,
    )
    lote = _crear_compra_pase(
        edicion=edicion_con_pases,
        pase=pase,
        comprador=persona,
        cantidad=2,
        estado=EstadoCompraPase.PENDIENTE,
        token="token-activacion-dom-03",
        compra=compra,
        referencia=referencia,
    )
    return lote


# ── Derechos ───────────────────────────────────────────────────────────────


@pytest.fixture
def beneficiario_pase(db, compra_pase_pagada, persona_participante):
    """Un derecho ACTIVO de una persona sobre el lote pagado."""
    derecho = PaseBeneficiario.objects.create(
        edicion_id=compra_pase_pagada.edicion_id,
        pase_id=compra_pase_pagada.pase_id,
        persona=persona_participante,
        origen=OrigenDerechoPase.COMPRA,
        compra_pase=compra_pase_pagada,
        cantidad=1,
        estado=EstadoDerechoPase.ACTIVO,
        motivo="Beneficiario de la prueba.",
    )
    compra_pase_pagada.asignados = 1
    compra_pase_pagada.save(update_fields=["asignados"])
    return derecho


@pytest.fixture
def cortesia_pase(db, edicion_con_pases, pase, persona_ajena, usuario_admin):
    """Una cortesía concedida: el acta y su derecho."""
    cortesia = CortesiaPase.objects.create(
        edicion=edicion_con_pases,
        pase=pase,
        persona=persona_ajena,
        actor_usuario=usuario_admin,
        actor_persona=usuario_admin.persona_fk,
        motivo="Invitación del inteligible.",
        estado=EstadoCortesiaPase.ACTIVA,
    )
    PaseBeneficiario.objects.create(
        edicion=edicion_con_pases,
        pase=pase,
        persona=persona_ajena,
        origen=OrigenDerechoPase.CORTESIA,
        cortesia=cortesia,
        cantidad=1,
        estado=EstadoDerechoPase.ACTIVO,
        actor_usuario=usuario_admin,
        actor_persona=usuario_admin.persona_fk,
        motivo="Invitación del inteligible.",
    )
    return cortesia


# ── Identidad ───────────────────────────────────────────────────────────────


@pytest.fixture
def usuario_admin(db):
    """Cuenta de ADMINISTRADOR: es `staff`, que es la autoridad del proyecto."""
    return Usuario.objects.create_user(
        username="administrador",
        password="Prueba-12345",
        is_staff=True,
    )


__all__ = [
    "TOKEN_PASE_FIJO",
    "beneficiario_pase",
    "compra_pase_con_compra",
    "compra_pase_pagada",
    "compra_pase_pendiente",
    "cortesia_pase",
    "edicion_con_pases",
    "pase",
    "pase_retirado",
    "pase_sin_precio",
    "usuario_admin",
]
