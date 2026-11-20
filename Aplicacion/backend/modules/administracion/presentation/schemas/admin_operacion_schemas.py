"""Los esquemas HTTP de la CAPA OPERATIVA del panel.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

Estos esquemas son el CONTRATO del wire. El frontend los refleja 1:1 en sus
esquemas Zod (`features/admin/**/schemas/*.schema.ts`): si un campo aparece
aquí, aparece allí, y al revés (`contract/api-wrapper-presenter-contract.md`
§7 — sin `z.any()` y sin campo genérico).

## Los tres veredictos que el panel lee

- `EstadoOperativoOut` — el veredicto con su código, su etiqueta y su
  explicación. El código es el del DUEÑO del hecho.
- `CausaOut` — una causa con su código y su prosa pública.
- `AccionOperativaOut` — una acción PROYECTADA. No es una autorización: el
  403 del backend sigue siendo el control.

## Lo que NO viaja

- El contexto crudo de la auditoría: el acta publica una lista blanca.
- `referencia_proveedor`, `evidencia`, `metadata` y `mensaje_respuesta` de
  los intentos del proveedor: son datos técnicos (`FR-04` §1.3).
- El `motivo` técnico de la participación: no sale al cliente.
"""

from datetime import datetime
from typing import List, Optional

from ninja import Schema
from pydantic import Field


# ── Vocabulario compartido ───────────────────────────────────────────────────


class ReferenciaOut(Schema):
    """Una referencia a un registro del área."""

    id: str
    nombre: str


class PersonaOut(Schema):
    """La persona responsable de una inscripción."""

    id: str
    nombre: str


class EstadoOperativoOut(Schema):
    """El veredicto operativo: código, etiqueta y explicación."""

    codigo: str
    etiqueta: str
    descripcion: str


class AccionOperativaOut(Schema):
    """La acción que el presenter proyecta."""

    codigo: str
    etiqueta: str
    href: Optional[str] = None


class CausaOut(Schema):
    """Una causa con su código de máquina y su prosa pública."""

    codigo: str
    mensaje: str


class CuposOperativosOut(Schema):
    """Los tres cupos, como tres hechos distintos."""

    adquiridos: int
    asignados: int
    disponibles: int


# ── Superficie de las inscripciones ──────────────────────────────────────────


class ParticipanteDeEquipoOut(Schema):
    """Una persona de la plantilla de un equipo."""

    id: str
    persona_id: str
    nombre: str
    documento: str
    rol: str
    estado: str


class EquipoDeInscripcionOut(Schema):
    """Un equipo de una inscripción, con su plantilla."""

    id: str
    nombre: str
    disciplina: ReferenciaOut
    estado: str
    participantes: List[ParticipanteDeEquipoOut]
    estado_operativo: EstadoOperativoOut


class ParticipacionPoolOut(Schema):
    """Una participación del pool de una inscripción."""

    id: str
    persona_id: str
    equipo_id: str
    equipo_nombre: str
    disciplina_nombre: str
    rol: str
    estado: str
    ocupa_cupo: bool


class PoolOut(Schema):
    """El pool de una inscripción, con los impedimentos del dueño."""

    cupos_pagados: int
    cupos_asignados: int
    cupos_disponibles: int
    participaciones: List[ParticipacionPoolOut]
    impedimentos: List[CausaOut]


class CompraDeCuposOut(Schema):
    """Una compra que financia la inscripción."""

    compra_id: str
    orden_pago_id: Optional[str] = None
    estado: str
    total: str
    moneda: str
    estado_operativo: EstadoOperativoOut


class EventoHistorialOut(Schema):
    """Un evento del historial del registro."""

    occurred_at: datetime
    tipo: str
    descripcion: str
    actor: str = ""


class AdminInscripcionListItemOut(Schema):
    """Una fila de la lista administrativa de las inscripciones (`RT-IN-07`)."""

    id: str
    responsable: PersonaOut
    paquete: ReferenciaOut
    edicion: ReferenciaOut
    equipos: int
    personas: int
    estado: EstadoOperativoOut
    cupos: CuposOperativosOut
    pago: Optional[EstadoOperativoOut] = None
    alerta: Optional[CausaOut] = None
    siguiente_accion: Optional[AccionOperativaOut] = None


class AdminInscripcionDetalleOut(AdminInscripcionListItemOut):
    """El detalle administrativo de una inscripción (`RT-IN-08`)."""

    equipos_detalle: List[EquipoDeInscripcionOut]
    pool: Optional[PoolOut] = None
    compras: List[CompraDeCuposOut]
    historial: List[EventoHistorialOut]


# ── Superficie de los equipos ────────────────────────────────────────────────


class PlantillaEquipoOut(Schema):
    """Los tres números de la plantilla de un equipo."""

    registrados: int
    minimo: int
    maximo: int


class CandidatoAEquipoOut(Schema):
    """Un candidato a entrar en un equipo."""

    id: str
    persona_id: str
    nombre: str
    documento: str
    estado_operativo: EstadoOperativoOut


class AdminEquipoListItemOut(Schema):
    """Una fila de la lista administrativa de los equipos (`RT-IN-09`)."""

    id: str
    nombre: str
    disciplina: ReferenciaOut
    categoria: Optional[ReferenciaOut] = None
    plantilla: PlantillaEquipoOut
    estado_operativo: EstadoOperativoOut
    acciones_disponibles: List[str]
    responsable: ReferenciaOut
    inscripcion: ReferenciaOut


class InscripcionDetalleEquipoOut(Schema):
    """La inscripción a la que pertenece un equipo."""

    id: str
    nombre: str
    referencia: str


class AdminEquipoDetalleOut(AdminEquipoListItemOut):
    """El detalle administrativo de un equipo (`RT-IN-10`)."""

    participantes: List[ParticipanteDeEquipoOut]
    cupos: Optional[CuposOperativosOut] = None
    inscripcion_detalle: Optional[InscripcionDetalleEquipoOut] = None
    elegibilidad: List[CandidatoAEquipoOut]


# ── Superficie de los participantes y de las personas ────────────────────────


class ParticipacionAdminOut(Schema):
    """Una participación de una persona, con su edición, equipo y disciplina."""

    id: str
    edicion: ReferenciaOut
    equipo: ReferenciaOut
    disciplina: ReferenciaOut
    rol: str
    estado: str
    conflicto: Optional[CausaOut] = None


class EventoHistorialAdminOut(Schema):
    """Un evento del historial de una persona."""

    occurred_at: datetime
    tipo: str
    descripcion: str


class ParticipanteAdminOut(Schema):
    """Una persona de la búsqueda administrativa, con sus participaciones."""

    id: str
    nombre: str
    documento: str
    participaciones: List[ParticipacionAdminOut]
    historial: List[EventoHistorialAdminOut]


class AdminPersonaListItemOut(ParticipanteAdminOut):
    """Una fila de la búsqueda administrativa de personas (`RT-ID-07`)."""


class AdminPersonaDetalleOut(AdminPersonaListItemOut):
    """El detalle administrativo de una persona (`RT-ID-08`)."""

    telefono: str = ""
    whatsapp: str = ""
    email: str = ""


# ── Superficie de los pagos ──────────────────────────────────────────────────


class CompradorOut(Schema):
    """El comprador de una compra."""

    persona_id: str
    nombre: str


class EntregaDerechosOut(Schema):
    """Qué habilita la compra: el código y la etiqueta."""

    codigo: str
    etiqueta: str


class CompraOut(Schema):
    """La compra que financia el pago.

    `reutilizada` NO se publica: el objetivo no lo persiste.
    """

    id: str
    estado: str
    total: str
    moneda: str


class IntentoPagoOut(Schema):
    """Un intento del proveedor, con su posición y su verificación."""

    id: str
    intento: int
    estado: str
    verificada: bool
    codigo_respuesta: str
    metodo_pago: str
    creada_en: datetime


class OperacionManualOut(Schema):
    """Una operación manual de un administrador sobre un pago."""

    id: str
    canal: str
    monto: str
    moneda: str
    motivo: str
    registrada_en: datetime
    actor: str


class AdminPagoListItemOut(Schema):
    """Una fila de la lista operativa de los pagos (`RT-PG-04`)."""

    compra_id: str
    orden_pago_id: Optional[str] = None
    inscripcion_id: Optional[str] = None
    tipo_compra: str
    resumen_concepto: str
    comprador: CompradorOut
    monto: str
    moneda: str
    estado_operativo: EstadoOperativoOut
    entrega_derechos: EntregaDerechosOut
    acciones_disponibles: List[str]
    fecha: datetime


class AdminPagoDetalleOut(AdminPagoListItemOut):
    """El detalle comercial de un pago (`RT-PG-07`)."""

    compra: Optional[CompraOut] = None
    origen_pago: str = ""
    intentos: List[IntentoPagoOut]
    operaciones_manuales: List[OperacionManualOut]
    siguiente_accion: Optional[AccionOperativaOut] = None


# ── El cuerpo del comando sensible ───────────────────────────────────────────


class RetirarParticipanteIn(Schema):
    """El comando de la retirada administrativa de un participante.

    El MOTIVO es obligatorio: sin motivo el comando no se ejecuta. La
    VERSIÓN viaja cuando el cliente la conoce: si el registro cambió, el
    backend responde 409 `RESOURCE_CHANGED`.
    """

    motivo: str
    version: Optional[str] = None


class AprobarPagoManualIn(Schema):
    """Evidencia externa que un administrador registra sobre una orden."""

    canal: str = Field(min_length=1, max_length=32)
    referencia: str = Field(min_length=1, max_length=100)
    motivo: str = Field(min_length=1, max_length=1000)


__all__ = [
    "AccionOperativaOut",
    "AdminEquipoDetalleOut",
    "AdminEquipoListItemOut",
    "AdminInscripcionDetalleOut",
    "AdminInscripcionListItemOut",
    "AdminPagoDetalleOut",
    "AdminPagoListItemOut",
    "AdminPersonaDetalleOut",
    "AdminPersonaListItemOut",
    "AprobarPagoManualIn",
    "CandidatoAEquipoOut",
    "CausaOut",
    "CompraDeCuposOut",
    "CompraOut",
    "CompradorOut",
    "CuposOperativosOut",
    "EntregaDerechosOut",
    "EquipoDeInscripcionOut",
    "EstadoOperativoOut",
    "EventoHistorialAdminOut",
    "EventoHistorialOut",
    "IntentoPagoOut",
    "InscripcionDetalleEquipoOut",
    "OperacionManualOut",
    "ParticipacionAdminOut",
    "ParticipacionPoolOut",
    "ParticipanteAdminOut",
    "ParticipanteDeEquipoOut",
    "PersonaOut",
    "PlantillaEquipoOut",
    "PoolOut",
    "ReferenciaOut",
    "RetirarParticipanteIn",
]
