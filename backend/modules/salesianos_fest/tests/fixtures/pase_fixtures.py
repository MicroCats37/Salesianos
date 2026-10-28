"""
Fixtures for the independent party-pass catalogue (Apply 1), its purchase
(Apply 2) and its settlement (Apply 3).

Pure data builders over the real models — no HTTP, no mocking.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import OrdenPagoStatus
from modules.pagos.domain.models import OrdenPago
from modules.salesianos_fest.domain.constants import EtapaChoices
from modules.salesianos_fest.domain.models import CompraPase, Pase, PasePrecio
from modules.usuarios.domain.constants import GeneroChoices, TipoDocumentoChoices
from modules.usuarios.domain.models import Persona


@pytest.fixture
def pase_fiesta(db, evento):
    """Active pass of the active event, with a PREVENTA price that is vigente."""
    pase = Pase.objects.create(
        evento=evento,
        nombre="Pase de Fiesta",
        descripcion="Acceso a la fiesta de cierre.",
        cantidad_maxima=0,
        activo=True,
    )
    PasePrecio.objects.create(
        pase=pase,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("25.00"),
        vigente_desde=date.today() - timedelta(days=1),
        vigente_hasta=date.today() + timedelta(days=30),
        activo=True,
    )
    PasePrecio.objects.create(
        pase=pase,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("35.00"),
        vigente_desde=date.today() + timedelta(days=31),
        vigente_hasta=None,
        activo=True,
    )
    return pase


@pytest.fixture
def pase_inactivo(db, evento):
    """Inactive pass — it must never be published."""
    return Pase.objects.create(
        evento=evento,
        nombre="Pase Retirado",
        descripcion="Pase despublicado.",
        cantidad_maxima=10,
        activo=False,
    )


@pytest.fixture
def pase_sin_precio(db, evento):
    """Active pass without any price row."""
    return Pase.objects.create(
        evento=evento,
        nombre="Pase Sin Precio",
        descripcion="Pase todavía sin precio configurado.",
        cantidad_maxima=5,
        activo=True,
    )


@pytest.fixture
def pase_precios_fuera_de_ventana(db, evento):
    """Active pass whose two stages are both outside their validity window."""
    pase = Pase.objects.create(
        evento=evento,
        nombre="Pase Fuera de Ventana",
        descripcion="Sus dos etapas están fuera de vigencia.",
        cantidad_maxima=0,
        activo=True,
    )
    PasePrecio.objects.create(
        pase=pase,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("20.00"),
        vigente_desde=date.today() - timedelta(days=30),
        vigente_hasta=date.today() - timedelta(days=1),
        activo=True,
    )
    PasePrecio.objects.create(
        pase=pase,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("30.00"),
        vigente_desde=date.today() + timedelta(days=10),
        vigente_hasta=None,
        activo=True,
    )
    return pase


@pytest.fixture
def evento_no_activo(db):
    """Inactive edition — its passes must never be published."""
    return Evento.objects.create(
        nombre="Salesianos FEST 2025",
        fecha_inicio=date(2025, 11, 15),
        fecha_fin=date(2025, 11, 20),
        esta_activo=False,
    )


@pytest.fixture
def pase_de_edicion_inactiva(db, evento_no_activo):
    """Active pass that belongs to an INACTIVE edition."""
    return Pase.objects.create(
        evento=evento_no_activo,
        nombre="Pase de la Edición Anterior",
        descripcion="Pertenece a una edición que no está activa.",
        cantidad_maxima=0,
        activo=True,
    )


# ── Compradores (Apply 2) ────────────────────────────────────────────────────


@pytest.fixture
def persona_comprador(db):
    """Persona of the buyer — the owner of the purchase (`Compra.responsable`)."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Compradora",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="70000001",
        genero=GeneroChoices.FEMENINO,
    )


@pytest.fixture
def usuario_comprador(db, persona_comprador):
    """Authenticated user linked to the buyer persona."""
    User = get_user_model()
    return User.objects.create_user(
        username="ana_compradora",
        email="ana@example.com",
        password="testpass123",
        persona_fk=persona_comprador,
    )


@pytest.fixture
def persona_ajena(db):
    """Persona of a buyer that does NOT own the purchase."""
    return Persona.objects.create(
        nombres="Luis",
        apellidos="Ajeno",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="70000002",
        genero=GeneroChoices.MASCULINO,
    )


@pytest.fixture
def usuario_ajeno(db, persona_ajena):
    """Authenticated user that is not the owner of the purchase."""
    User = get_user_model()
    return User.objects.create_user(
        username="luis_ajeno",
        email="luis@example.com",
        password="testpass123",
        persona_fk=persona_ajena,
    )


@pytest.fixture
def pase_con_inventario_limitado(db, evento):
    """Active pass with a capped inventory (5) and a vigente PREVENTA price."""
    pase = Pase.objects.create(
        evento=evento,
        nombre="Pase con Inventario",
        descripcion="Pase con cantidad máxima limitada.",
        cantidad_maxima=5,
        activo=True,
    )
    PasePrecio.objects.create(
        pase=pase,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("20.00"),
        vigente_desde=date.today() - timedelta(days=1),
        vigente_hasta=date.today() + timedelta(days=30),
        activo=True,
    )
    return pase


# ── Liquidación (Apply 3) ────────────────────────────────────────────────────


@pytest.fixture
def compra_pase_pendiente(db, usuario_comprador, pase_fiesta):
    """A PENDIENTE pass purchase funded by a PENDIENTE payment order.

    Built with the models (like the sports settlement fixture) so the
    settlement tests exercise the settlement, not the purchase endpoint.
    """
    precio_unitario = Decimal("25.00")
    cantidad = 2
    total = precio_unitario * cantidad

    orden_pago = OrdenPago.objects.create(
        numero=f"OP-PASE-{uuid.uuid4().hex[:8].upper()}",
        monto_total=total,
        moneda="PEN",
        estado=OrdenPagoStatus.PENDIENTE,
    )
    compra = Compra.objects.create(
        responsable=usuario_comprador.persona_fk,
        descripcion=f"Compra de pases - {pase_fiesta.nombre}",
        referencia_externa=f"PASE-{str(pase_fiesta.id)[:8]}",
        total=total,
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraPase.objects.create(
        compra=compra,
        pase=pase_fiesta,
        evento=pase_fiesta.evento,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        total=total,
    )
    return compra


@pytest.fixture
def usuario_admin_pases(db):
    """
    An authenticated administrator for the SENSITIVE payment operations.

    Approving, annulling or cancelling a payment is a capability the project
    grants to the break-glass tier ONLY (`core.capacidades`: the operational
    staff reads the area but never approves a payment). The fixture is
    therefore a superuser, the tier that really holds it.
    """
    User = get_user_model()
    persona = Persona.objects.create(
        nombres="Admin",
        apellidos="Pases",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="70000003",
        genero=GeneroChoices.MASCULINO,
    )
    usuario = User.objects.create_user(
        username="admin_pases",
        email="admin_pases@example.com",
        password="testpass123",
        persona_fk=persona,
    )
    usuario.is_staff = True
    usuario.is_superuser = True
    usuario.save(update_fields=["is_staff", "is_superuser"])
    return usuario


# ── Derechos nominativos (Apply 4) ───────────────────────────────────────────


def _crear_persona(nombres, apellidos, numero_documento, genero):
    """Create a Persona without any sports registration nor account."""
    return Persona.objects.create(
        nombres=nombres,
        apellidos=apellidos,
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento=numero_documento,
        genero=genero,
    )


@pytest.fixture
def persona_beneficiaria_1(db):
    """First person that can receive a pass (no Usuario, no registration)."""
    return _crear_persona("Ana", "Beneficiaria", "71000001", GeneroChoices.FEMENINO)


@pytest.fixture
def persona_beneficiaria_2(db):
    """Second person that can receive a pass."""
    return _crear_persona("Beto", "Beneficiario", "71000002", GeneroChoices.MASCULINO)


@pytest.fixture
def persona_beneficiaria_3(db):
    """Third person that can receive a pass."""
    return _crear_persona("Carla", "Beneficiaria", "71000003", GeneroChoices.FEMENINO)


@pytest.fixture
def persona_beneficiaria_4(db):
    """Fourth person that can receive a pass."""
    return _crear_persona("Diego", "Beneficiario", "71000004", GeneroChoices.MASCULINO)


@pytest.fixture
def persona_beneficiaria_5(db):
    """Fifth person that can receive a pass (so a batch of four can overflow)."""
    return _crear_persona("Eva", "Beneficiaria", "71000005", GeneroChoices.FEMENINO)


@pytest.fixture
def compra_pase_pagada(db, usuario_comprador, pase_fiesta):
    """A PAID pass purchase of FOUR passes, ready to receive beneficiaries."""
    return _crear_compra_pase(
        usuario_comprador=usuario_comprador,
        pase=pase_fiesta,
        cantidad=4,
        estado=EstadoCompraChoices.PAGADA,
        marca="PAG",
    )


@pytest.fixture
def compra_pase_pagada_otro_lote(db, usuario_comprador, pase_fiesta):
    """A SECOND paid purchase of the same pass — another batch of the event."""
    return _crear_compra_pase(
        usuario_comprador=usuario_comprador,
        pase=pase_fiesta,
        cantidad=2,
        estado=EstadoCompraChoices.PAGADA,
        marca="PAG2",
    )


def _crear_compra_pase(*, usuario_comprador, pase, cantidad, estado, marca):
    """Build a pass purchase with its payment order and its commercial line."""
    precio_unitario = Decimal("25.00")
    total = precio_unitario * cantidad

    orden_pago = OrdenPago.objects.create(
        numero=f"OP-{marca}-{uuid.uuid4().hex[:8].upper()}",
        monto_total=total,
        moneda="PEN",
        estado=OrdenPagoStatus.PAGADA if estado == EstadoCompraChoices.PAGADA else OrdenPagoStatus.PENDIENTE,
    )
    compra = Compra.objects.create(
        responsable=usuario_comprador.persona_fk,
        descripcion=f"Compra de pases - {pase.nombre}",
        referencia_externa=f"PASE-{marca}-{str(pase.id)[:8]}",
        total=total,
        estado=estado,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraPase.objects.create(
        compra=compra,
        pase=pase,
        evento=pase.evento,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        total=total,
    )
    # The generic `commerce.Compra` has NO event: the event of a pass purchase
    # comes from its commercial line. The fixture exposes it on the instance so
    # the tests can read `compra.evento` without a second query.
    compra.evento = pase.evento
    compra.evento_id = pase.evento_id
    return compra


@pytest.fixture
def persona_con_beneficio_deportivo(
    db, evento, paquete_reencuentro, promocion_junior
):
    """
    A person whose PAID sports capacity grants the FIESTA benefit.

    It is the SECOND source of fiesta access: a person can hold both a
    sports benefit and a pass, and revoking one of them must not remove the
    access granted by the other.
    """
    from modules.salesianos_fest.domain.constants import (
        EstadoAsignacionCupoChoices,
        EstadoInscripcionChoices,
        EstadoInscripcionPersonaChoices,
        TipoCompraChoices,
    )
    from modules.salesianos_fest.domain.models import (
        AsignacionCupo,
        CompraInscripcion,
        Inscripcion,
        InscripcionPersona,
    )

    persona = _crear_persona(
        "Sol", "Deportiva", "72000001", GeneroChoices.FEMENINO
    )
    inscripcion = Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    orden_pago = OrdenPago.objects.create(
        numero=f"OP-DEP-{uuid.uuid4().hex[:8].upper()}",
        monto_total=Decimal("40.00"),
        moneda="PEN",
        estado=OrdenPagoStatus.PAGADA,
    )
    compra = Compra.objects.create(
        responsable=persona,
        descripcion="Compra deportiva",
        referencia_externa=f"DEP-{str(inscripcion.id)[:8]}",
        total=Decimal("40.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=1,
        precio_unitario=Decimal("40.00"),
        total=Decimal("40.00"),
    )
    inscripcion_persona = InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion,
        compra=compra,
        inscripcion_persona=inscripcion_persona,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    return persona
