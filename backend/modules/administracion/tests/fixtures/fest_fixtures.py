"""
Administracion test fixtures — the operational scenario with EXACT metrics.

The scenario is hand-built so every number of the overview can be asserted
EXACTLY (`sdd/administracion-operativa-fest/admin-surface` §10.9 — "metric
correctness: hand-built fixture with exact expected numbers").

What the scenario proves:

- the EVENT scope (rows of another edition are never counted),
- the PAID CAPACITY comes only from `PAGADA` purchases,
- the PAYMENT state is independent of the REGISTRATION state,
- `personas` and `participaciones` are two different numbers,
- the roster rule (`min_jugadores` of the discipline).

Expected numbers of the scenario (active event):

| Block                | Value                                                       |
|----------------------|-------------------------------------------------------------|
| inscripciones        | total 2 · RECIBIDA 1 · VALIDADA 1 · created 7d 2           |
| pagos                | 5 compras · 2 pagadas · 2 pendientes · 1 cancelada          |
|                      | monto 200.00 / 35.00 · 1 vencida · 1 pagada sin liquidar    |
| cupos                | contratado 5 · pagado 3 · asignado 2 · disponible 1 · 1 agotada |
| equipos              | 3 activos · 2 completos · 1 incompleto                      |
| participantes         | 5 personas · 4 participaciones · 2 en pool · 3 sin cupo     |
| acreditaciones       | 4 · 2 con acceso · 1 bloqueada por admin                     |
| accesos              | 1 permitido · 2 denegados                                   |
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.salesianos_fest.domain.constants import (
    AutorizacionFiestaChoices,
    EstadoAcreditacionChoices,
    EstadoAsignacionCupoChoices,
    EstadoEquipoChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    EstadoParticipacionChoices,
    MedioAceptacionChoices,
    ModalidadChoices,
    ModoDisciplinasChoices,
    ResultadoAccesoChoices,
    RolParticipanteChoices,
    TipoAceptacionChoices,
    TipoCompraChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.models import (
    AceptacionInscripcion,
    AcreditacionEvento,
    AsignacionCupo,
    Categoria,
    CompraInscripcion,
    ControlAcceso,
    Disciplina,
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Participacion,
    Paquete,
    Promocion,
)
from modules.usuarios.domain.models.persona import Persona


@pytest.fixture
def escenario_paginacion(db, evento):
    """Build a scenario with 12 registrations of the active event.

    It exists to exercise the PAGINATION and the ORDERING of the
    administrative lists: with a single row every order looks the same.

    It is INDEPENDENT from `escenario_operativo` on purpose: the exact metrics
    of the overview must not drift when this scenario is added.
    """
    promocion = Promocion.objects.create(
        anio=2027,
        nombre="Promoción 2027",
        activa=True,
    )
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Pack Paginación",
        descripcion="Pack para las pruebas de paginación",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )

    inscripciones = []
    for indice in range(12):
        responsable = _crear_persona(
            f"Responsable{indice:02d}",
            "Paginacion",
            f"9{indice:07d}",
        )
        inscripciones.append(
            Inscripcion.objects.create(
                evento=evento,
                responsable=responsable,
                paquete=paquete,
                promocion=promocion,
                estado=EstadoInscripcionChoices.RECIBIDA,
            )
        )

    return {
        "evento": evento,
        "paquete": paquete,
        "promocion": promocion,
        "inscripciones": inscripciones,
    }


def _crear_persona(nombres: str, apellidos: str, documento: str) -> Persona:
    """Create a person with a unique document."""
    return Persona.objects.create(
        nombres=nombres,
        apellidos=apellidos,
        tipo_documento="DNI",
        numero_documento=documento,
        genero="M",
    )


def _crear_orden(numero: str, monto: Decimal, estado: str) -> OrdenPago:
    """Create a payment order with a stable number."""
    return OrdenPago.objects.create(
        numero=numero,
        monto_total=monto,
        estado=estado,
        pagada_en=(
            "2026-10-01T12:00:00Z" if estado == OrdenPagoStatus.PAGADA else None
        ),
    )


@pytest.fixture
def escenario_otra_edicion(db, evento):
    """Build rows that belong to ANOTHER edition of the event.

    Every row created here EXISTS in the database, but it belongs to an
    edition that is not the active one. The administrative surface resolves
    the active event SERVER-SIDE, so NONE of these rows may appear in any
    list of the area.

    It covers EVERY event-scoped surface at once: registrations, teams, roster
    rows, people, purchases, accreditations and access records.

    It is INDEPENDENT from `escenario_operativo`: a test that uses this
    fixture sees an active event with NO rows of its own, which is the
    clearest possible proof of the event scope.
    """
    evento_anterior = Evento.objects.create(
        nombre="Edición Previa",
        fecha_inicio=date(2025, 11, 1),
        fecha_fin=date(2025, 11, 5),
        esta_activo=False,
    )
    promocion_anterior = Promocion.objects.create(
        anio=2025,
        nombre="Promoción 2025",
        activa=True,
    )
    paquete_anterior = Paquete.objects.create(
        evento=evento_anterior,
        nombre="Pack Previo",
        descripcion="Pack de la edición previa",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )
    disciplina_anterior = Disciplina.objects.create(
        nombre="Fútbol 5 Previo",
        sigla="F5P",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=2,
        max_jugadores=11,
        esta_activa=True,
    )

    responsable = _crear_persona("Otra", "Edicion", "88888888")
    inscripcion_fuera = Inscripcion.objects.create(
        evento=evento_anterior,
        responsable=responsable,
        paquete=paquete_anterior,
        promocion=promocion_anterior,
        estado=EstadoInscripcionChoices.CONFIRMADA,
    )
    equipo_fuera = Equipo.objects.create(
        inscripcion=inscripcion_fuera,
        disciplina=disciplina_anterior,
        nombre="Equipo Previo",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )
    persona_fuera = _crear_persona("Persona", "Previa", "99999999")
    inscripcion_persona_fuera = InscripcionPersona.objects.create(
        inscripcion=inscripcion_fuera,
        persona=persona_fuera,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_fuera,
        equipo=equipo_fuera,
        evento=evento_anterior,
        disciplina=disciplina_anterior,
        persona=persona_fuera,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    orden_fuera = _crear_orden("ORD-EDICION-PREVIA", Decimal("999.00"), OrdenPagoStatus.PAGADA)
    compra_fuera = Compra.objects.create(
        responsable=responsable,
        descripcion="Compra de la edición previa",
        total=Decimal("999.00"),
        estado=EstadoCompraChoices.PAGADA,
        orden_pago=orden_fuera,
    )
    CompraInscripcion.objects.create(
        compra=compra_fuera,
        inscripcion=inscripcion_fuera,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("99.90"),
        total=Decimal("999.00"),
    )

    acreditacion_fuera = AcreditacionEvento.objects.create(
        evento=evento_anterior,
        persona=persona_fuera,
        estado=EstadoAcreditacionChoices.ACTIVA,
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
        habilitado=None,
    )
    ControlAcceso.objects.create(
        acreditacion=acreditacion_fuera,
        resultado=ResultadoAccesoChoices.PERMITIDO,
        punto_acceso="Puerta Previa",
    )

    return {
        "evento_anterior": evento_anterior,
        "inscripcion_fuera": inscripcion_fuera,
        "equipo_fuera": equipo_fuera,
        "participacion_fuera": persona_fuera,
        "compra_fuera": compra_fuera,
        "acreditacion_fuera": acreditacion_fuera,
    }


@pytest.fixture
def escenario_operativo(db, evento):
    """Build the operational scenario of the active event.

    Returns:
        A dict with the created objects and the EXPECTED metrics, so the tests
        assert the numbers without duplicating the construction logic.
    """
    # ── Catálogos ───────────────────────────────────────────────────────────
    disciplina_futbol = Disciplina.objects.create(
        nombre="Fútbol 7",
        sigla="F7",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=2,
        max_jugadores=11,
        esta_activa=True,
    )
    disciplina_voley = Disciplina.objects.create(
        nombre="Vóley Mixto",
        sigla="VM",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=1,
        max_jugadores=12,
        esta_activa=True,
    )
    promocion = Promocion.objects.create(
        anio=2026,
        nombre="Promoción 2026",
        activa=True,
    )
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Pack FEST",
        descripcion="Pack del evento",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=2,
        minimo_compra_inicial=1,
        activo=True,
    )
    Categoria.objects.create(
        evento=evento,
        nombre="Senior",
        promocion_desde=1,
        promocion_hasta=5,
        esta_activa=True,
    )

    # Another edition — its rows must NEVER enter the metrics of the active one.
    evento_anterior = Evento.objects.create(
        nombre="Edición Anterior",
        fecha_inicio=date(2025, 11, 1),
        fecha_fin=date(2025, 11, 5),
        esta_activo=False,
    )
    paquete_anterior = Paquete.objects.create(
        evento=evento_anterior,
        nombre="Pack Anterior",
        descripcion="Pack de la edición anterior",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )

    # ── Personas ────────────────────────────────────────────────────────────
    responsable_1 = _crear_persona("Ana", "Torres", "11111111")
    responsable_2 = _crear_persona("Luis", "Ramos", "22222222")
    persona_1 = _crear_persona("Pedro", "Alvarez", "33333333")
    persona_2 = _crear_persona("Lucia", "Mendoza", "44444444")
    persona_3 = _crear_persona("Sofia", "Quispe", "55555555")
    persona_4 = _crear_persona("Mateo", "Rojas", "66666666")
    persona_5 = _crear_persona("Retirada", "Persona", "77777777")
    persona_6 = _crear_persona("Enespera", "Pool", "88888888")

    # ── Inscripciones ───────────────────────────────────────────────────────
    inscripcion_1 = Inscripcion.objects.create(
        evento=evento,
        responsable=responsable_1,
        paquete=paquete,
        promocion=promocion,
        estado=EstadoInscripcionChoices.RECIBIDA,
    )
    inscripcion_2 = Inscripcion.objects.create(
        evento=evento,
        responsable=responsable_2,
        paquete=paquete,
        promocion=promocion,
        estado=EstadoInscripcionChoices.VALIDADA,
    )
    inscripcion_fuera = Inscripcion.objects.create(
        evento=evento_anterior,
        responsable=responsable_1,
        paquete=paquete_anterior,
        promocion=promocion,
        estado=EstadoInscripcionChoices.CONFIRMADA,
    )

    # ── Participantes (pool) ────────────────────────────────────────────────
    inscripcion_persona_1 = InscripcionPersona.objects.create(
        inscripcion=inscripcion_1,
        persona=persona_1,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    inscripcion_persona_2 = InscripcionPersona.objects.create(
        inscripcion=inscripcion_1,
        persona=persona_2,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    inscripcion_persona_3 = InscripcionPersona.objects.create(
        inscripcion=inscripcion_2,
        persona=persona_3,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    inscripcion_persona_4 = InscripcionPersona.objects.create(
        inscripcion=inscripcion_2,
        persona=persona_4,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    InscripcionPersona.objects.create(
        inscripcion=inscripcion_2,
        persona=persona_5,
        estado=EstadoInscripcionPersonaChoices.RETIRADO,
    )
    inscripcion_persona_6 = InscripcionPersona.objects.create(
        inscripcion=inscripcion_2,
        persona=persona_6,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )

    # ── Equipos ─────────────────────────────────────────────────────────────
    equipo_1 = Equipo.objects.create(
        inscripcion=inscripcion_1,
        disciplina=disciplina_futbol,
        nombre="Los Tigres",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )
    equipo_2 = Equipo.objects.create(
        inscripcion=inscripcion_1,
        disciplina=disciplina_voley,
        nombre="Las Panteras",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )
    equipo_3 = Equipo.objects.create(
        inscripcion=inscripcion_2,
        disciplina=disciplina_futbol,
        nombre="Los Leones",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )
    Equipo.objects.create(
        inscripcion=inscripcion_1,
        disciplina=disciplina_futbol,
        nombre="Equipo Cancelado",
        estado=EstadoEquipoChoices.EQUIPO_CANCELADO,
    )

    # ── Participaciones ──────────────────────────────────────────────────────
    Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_1,
        equipo=equipo_1,
        evento=evento,
        disciplina=disciplina_futbol,
        persona=persona_1,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )
    Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_2,
        equipo=equipo_1,
        evento=evento,
        disciplina=disciplina_futbol,
        persona=persona_2,
        rol=RolParticipanteChoices.CAPITAN,
        estado=EstadoParticipacionChoices.ACTIVA,
    )
    # One person, TWO disciplines: a paid cup authorises every contracted one.
    Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_2,
        equipo=equipo_2,
        evento=evento,
        disciplina=disciplina_voley,
        persona=persona_2,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )
    # Withdrawn participation: its person stays in the pool.
    Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_3,
        equipo=equipo_3,
        evento=evento,
        disciplina=disciplina_futbol,
        persona=persona_3,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.RETIRADA,
    )
    Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_4,
        equipo=equipo_3,
        evento=evento,
        disciplina=disciplina_futbol,
        persona=persona_4,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    # ── Compras y órdenes de pago ───────────────────────────────────────────
    def _compra(inscripcion, tipo, cantidad, precio, estado_compra, estado_orden):
        numero = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        total = (Decimal(precio) * cantidad).quantize(Decimal("0.01"))
        orden = _crear_orden(numero, total, estado_orden)
        compra = Compra.objects.create(
            responsable=inscripcion.responsable,
            descripcion=f"Compra {tipo}",
            total=total,
            estado=estado_compra,
            orden_pago=orden,
        )
        CompraInscripcion.objects.create(
            compra=compra,
            inscripcion=inscripcion,
            tipo=tipo,
            cantidad=cantidad,
            precio_unitario=Decimal(precio),
            total=total,
        )
        return compra, orden

    compra_inicial, orden_inicial = _compra(
        inscripcion_1,
        TipoCompraChoices.INICIAL,
        2,
        "75.00",
        EstadoCompraChoices.PAGADA,
        OrdenPagoStatus.PAGADA,
    )
    _compra(
        inscripcion_1,
        TipoCompraChoices.AMPLIACION,
        1,
        "20.00",
        EstadoCompraChoices.PENDIENTE,
        OrdenPagoStatus.VENCIDA,
    )
    _compra(
        inscripcion_1,
        TipoCompraChoices.AMPLIACION,
        9,
        "111.00",
        EstadoCompraChoices.CANCELADA,
        OrdenPagoStatus.CANCELADA,
    )
    compra_pagada_2, orden_pagada_2 = _compra(
        inscripcion_2,
        TipoCompraChoices.INICIAL,
        1,
        "50.00",
        EstadoCompraChoices.PAGADA,
        OrdenPagoStatus.PAGADA,
    )
    # Paid order, purchase still PENDIENTE → the settlement gap.
    _compra(
        inscripcion_2,
        TipoCompraChoices.AMPLIACION,
        1,
        "15.00",
        EstadoCompraChoices.PENDIENTE,
        OrdenPagoStatus.PAGADA,
    )

    # ── Cupos asignados ─────────────────────────────────────────────────────
    asignacion_1 = AsignacionCupo.objects.create(
        inscripcion=inscripcion_1,
        compra=compra_inicial,
        inscripcion_persona=inscripcion_persona_1,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    asignacion_2 = AsignacionCupo.objects.create(
        inscripcion=inscripcion_2,
        compra=compra_pagada_2,
        inscripcion_persona=inscripcion_persona_4,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    # ── Acreditaciones ──────────────────────────────────────────────────────
    acreditacion_1 = AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_1,
        estado=EstadoAcreditacionChoices.ACTIVA,
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
        habilitado=None,
    )
    acreditacion_2 = AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_2,
        estado=EstadoAcreditacionChoices.PENDIENTE,
        acceso_fiesta=False,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
        habilitado=None,
    )
    acreditacion_3 = AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_4,
        estado=EstadoAcreditacionChoices.REVOCADA,
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.BLOQUEADA,
        habilitado=False,
    )
    acreditacion_4 = AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_6,
        estado=EstadoAcreditacionChoices.ACTIVA,
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
        habilitado=True,
    )
    acreditacion_fuera = AcreditacionEvento.objects.create(
        evento=evento_anterior,
        persona=persona_5,
        estado=EstadoAcreditacionChoices.ACTIVA,
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
        habilitado=None,
    )

    # ── Accesos ─────────────────────────────────────────────────────────────
    ControlAcceso.objects.create(
        acreditacion=acreditacion_1,
        resultado=ResultadoAccesoChoices.PERMITIDO,
        punto_acceso="Puerta 1",
    )
    ControlAcceso.objects.create(
        acreditacion=acreditacion_2,
        resultado=ResultadoAccesoChoices.DENEGADO,
        punto_acceso="Puerta 2",
    )
    control_ultimo = ControlAcceso.objects.create(
        acreditacion=acreditacion_3,
        resultado=ResultadoAccesoChoices.DENEGADO,
        punto_acceso="Puerta 1",
    )
    ControlAcceso.objects.create(
        acreditacion=acreditacion_fuera,
        resultado=ResultadoAccesoChoices.PERMITIDO,
        punto_acceso="Puerta 3",
    )

    # ── Legal acceptances ───────────────────────────────────────────────────
    # The acceptance block of the drilldown (A4). They do NOT change any
    # metric of the overview.
    for _tipo in (
        TipoAceptacionChoices.BASES,
        TipoAceptacionChoices.APTITUD_FISICA,
    ):
        AceptacionInscripcion.objects.create(
            inscripcion_persona=inscripcion_persona_1,
            tipo_aceptacion=_tipo,
            documento_version="BASES-SF26-2026-09-06",
            actor_id=str(persona_1.id),
            medio=MedioAceptacionChoices.WEB,
        )
    AceptacionInscripcion.objects.create(
        inscripcion_persona=inscripcion_persona_2,
        tipo_aceptacion=TipoAceptacionChoices.BASES,
        documento_version="BASES-SF26-2026-09-06",
        actor_id=str(persona_2.id),
        medio=MedioAceptacionChoices.MOBILE,
    )

    # ── Payment attempts ────────────────────────────────────────────────────
    # The attempts carry EVERY forbidden field on purpose: the administrative
    # surface must never serialize them.
    transaccion_exitosa = TransaccionPago.objects.create(
        orden_pago=orden_inicial,
        transaction_id="TXN-SECRETO-0001",
        order_number=orden_inicial.numero,
        amount=Decimal("150.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
        response_code="0000",
        response_message="Operacion aprobada por el proveedor",
        metodo_pago="TARJETA",
        metadata={
            "token_sesion": "sesion-secreta-abc",
            "auth_token": "auth-token-secreto",
            "source": "fest",
        },
    )
    transaccion_fallida = TransaccionPago.objects.create(
        orden_pago=orden_inicial,
        transaction_id="TXN-SECRETO-0002",
        order_number=orden_inicial.numero,
        amount=Decimal("150.00"),
        currency="PEN",
        status=IzipayStatus.FALLIDO,
        response_code="9999",
        response_message="Rechazada por el proveedor",
        metodo_pago="TARJETA",
        metadata={"token_sesion": "sesion-secreta-xyz"},
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pagada_2,
        transaction_id="TXN-SECRETO-0003",
        order_number=orden_pagada_2.numero,
        amount=Decimal("50.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
        response_code="0000",
        response_message="Operacion aprobada por el proveedor",
        metodo_pago="YAPE",
        metadata={"token_sesion": "sesion-secreta-def"},
    )

    return {
        "evento": evento,
        "evento_anterior": evento_anterior,
        "disciplina_futbol": disciplina_futbol,
        "disciplina_voley": disciplina_voley,
        "paquete": paquete,
        "paquete_anterior": paquete_anterior,
        "promocion": promocion,
        "responsable_1": responsable_1,
        "inscripcion_1": inscripcion_1,
        "inscripcion_2": inscripcion_2,
        "inscripcion_fuera": inscripcion_fuera,
        "equipo_1": equipo_1,
        "equipo_2": equipo_2,
        "equipo_3": equipo_3,
        "compra_inicial": compra_inicial,
        "orden_inicial": orden_inicial,
        "orden_pagada_2": orden_pagada_2,
        "asignacion_1": asignacion_1,
        "asignacion_2": asignacion_2,
        "acreditacion_1": acreditacion_1,
        "acreditacion_fuera": acreditacion_fuera,
        "control_ultimo": control_ultimo,
        "transaccion_exitosa": transaccion_exitosa,
        "transaccion_fallida": transaccion_fallida,
        "esperado": {
            "inscripciones": {
                "total": 2,
                "por_estado": {
                    EstadoInscripcionChoices.BORRADOR: 0,
                    EstadoInscripcionChoices.RECIBIDA: 1,
                    EstadoInscripcionChoices.EN_REVISION: 0,
                    EstadoInscripcionChoices.OBSERVADA: 0,
                    EstadoInscripcionChoices.VALIDADA: 1,
                    EstadoInscripcionChoices.CONFIRMADA: 0,
                    EstadoInscripcionChoices.RECHAZADA: 0,
                    EstadoInscripcionChoices.CANCELADA: 0,
                },
                "creadas_ultimos_7_dias": 2,
            },
            "pagos": {
                "compras_total": 5,
                "compras_pagadas": 2,
                "compras_pendientes": 2,
                "compras_canceladas": 1,
                "monto_pagado": 200.00,
                "monto_pendiente": 35.00,
                "ordenes_vencidas": 1,
                "compras_pagadas_sin_liquidar": 1,
            },
            "cupos": {
                "contratado": 5,
                "pagado": 3,
                "asignado_activo": 2,
                "disponible_pagado": 1,
                "inscripciones_con_capacidad_exhaustada": 1,
            },
            "equipos": {
                "total": 3,
                "completos": 2,
                "incompletos": 1,
                "por_disciplina": [
                    {
                        "disciplina_id": str(disciplina_futbol.id),
                        "sigla": "F7",
                        "nombre": "Fútbol 7",
                        "total": 2,
                    },
                    {
                        "disciplina_id": str(disciplina_voley.id),
                        "sigla": "VM",
                        "nombre": "Vóley Mixto",
                        "total": 1,
                    },
                ],
            },
            "participantes": {
                "personas_distintas": 5,
                "participaciones_activas": 4,
                "en_pool": 2,
                "sin_cupo_activo": 3,
            },
            "acreditaciones": {
                "total": 4,
                "por_estado": {
                    EstadoAcreditacionChoices.PENDIENTE: 1,
                    EstadoAcreditacionChoices.ACTIVA: 2,
                    EstadoAcreditacionChoices.SUSPENDIDA: 0,
                    EstadoAcreditacionChoices.REVOCADA: 1,
                },
                "con_acceso_fiesta": 2,
                "bloqueadas_por_admin": 1,
            },
            "accesos": {
                "permitidos": 1,
                "denegados": 2,
            },
        },
    }
