"""Resultados (DTO de salida) de la CAPA OPERATIVA del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

Estos dataclasses son el modelo de LECTURA que consume el panel. No son
esquemas HTTP: el presenter los proyecta a las formas de `presentation/`.

## El vocabulario que travels

Los resultados ya llevan la PROSA que se publica (etiqueta, descripción,
mensaje). El cliente nunca inventa la etiqueta de un estado ni de una
causa: la recibe y la imprime verbatim.

## Lo que NO hay aquí

- **Ninguna regla de negocio.** El veredicto del pago lo calcula
  `EstadoOperativoPagoService` (dueño `pagos`); el pool lo calcula
  `PoolFlujo` (dueño `salesianos_fest`); la plantilla completa la decide la
  disciplina del dueño. Este archivo sólo TRANSPORTA lo que ya es un hecho.
- **Ninguna aritmética de negocio.** `disponibles` es la diferencia que el
  dueño ya publicó (`RN-I03`), no una resta de este módulo.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


# ── Vocabulario compartido por las cinco superficies ─────────────────────────


@dataclass(frozen=True)
class ReferenciaAdminResultado:
    """Una referencia a un registro del área: la edición, el paquete, el equipo."""

    id: str
    nombre: str


@dataclass(frozen=True)
class PersonaAdminResultado:
    """La persona responsable de una inscripción."""

    id: str
    nombre: str


@dataclass(frozen=True)
class EstadoOperativoAdminResultado:
    """El veredicto operativo: código, etiqueta y explicación.

    El `codigo` es el del DUEÑO del hecho (`EstadoInscripcion`,
    `EstadoOperativoPago`, …). Este módulo no renumera ningún vocabulario.
    """

    codigo: str
    etiqueta: str
    descripcion: str


@dataclass(frozen=True)
class AccionOperativaAdminResultado:
    """La acción que el presenter proyecta.

    Es una PROYECCIÓN y no una autorización: la interfaz puede usarla para
    ocultar una afordencia, pero el 403 del backend sigue siendo el control.
    """

    codigo: str
    etiqueta: str
    href: Optional[str] = None


@dataclass(frozen=True)
class CausaAdminResultado:
    """Una causa con su código de máquina y su prosa pública."""

    codigo: str
    mensaje: str


@dataclass(frozen=True)
class CuposOperativosAdminResultado:
    """Los tres cupos, como TRES hechos distintos.

    `disponibles` NUNCA es negativo: es el valor que el dueño ya publicó.
    """

    adquiridos: int
    asignados: int
    disponibles: int


# ── Superficie de las inscripciones (RT-IN-07 · RT-IN-08) ────────────────────


@dataclass(frozen=True)
class ParticipanteDeEquipoAdminResultado:
    """Una persona de la plantilla de un equipo."""

    id: str
    persona_id: str
    nombre: str
    documento: str
    rol: str
    estado: str


@dataclass(frozen=True)
class EquipoDeInscripcionAdminResultado:
    """Un equipo de una inscripción, con su plantilla y su veredicto."""

    id: str
    nombre: str
    disciplina: ReferenciaAdminResultado
    estado: str
    participantes: List[ParticipanteDeEquipoAdminResultado] = field(default_factory=list)
    estado_operativo: EstadoOperativoAdminResultado = None  # type: ignore[assignment]


@dataclass(frozen=True)
class ParticipacionPoolAdminResultado:
    """Una participación del pool de una inscripción."""

    id: str
    persona_id: str
    equipo_id: str
    equipo_nombre: str
    disciplina_nombre: str
    rol: str
    estado: str
    ocupa_cupo: bool


@dataclass(frozen=True)
class PoolAdminResultado:
    """El pool de una inscripción, con los impedimentos del dueño."""

    cupos_pagados: int
    cupos_asignados: int
    cupos_disponibles: int
    participaciones: List[ParticipacionPoolAdminResultado] = field(default_factory=list)
    impedimentos: List[CausaAdminResultado] = field(default_factory=list)


@dataclass(frozen=True)
class CompraDeCuposAdminResultado:
    """Una compra que financia la inscripción.

    **El objetivo no publica una relación que acote una compra a una
    inscripción**: el vínculo es la referencia de la intención y el módulo
    dueño no lo expone como consulta. Por eso la lista viaja VACÍA y el
    detalle lo declara (`A0-XCT02-08`).
    """

    compra_id: str
    orden_pago_id: Optional[str]
    estado: str
    total: str
    moneda: str
    estado_operativo: EstadoOperativoAdminResultado


@dataclass(frozen=True)
class EventoHistorialAdminResultado:
    """Un evento del historial del registro."""

    occurred_at: datetime
    tipo: str
    descripcion: str
    actor: str = ""


@dataclass(frozen=True)
class AdminInscripcionListItemAdminResultado:
    """Una fila de la lista administrativa de las inscripciones (`RT-IN-07`)."""

    id: str
    responsable: PersonaAdminResultado
    paquete: ReferenciaAdminResultado
    edicion: ReferenciaAdminResultado
    equipos: int
    personas: int
    estado: EstadoOperativoAdminResultado
    cupos: CuposOperativosAdminResultado
    pago: Optional[EstadoOperativoAdminResultado]
    alerta: Optional[CausaAdminResultado]
    siguiente_accion: Optional[AccionOperativaAdminResultado]


@dataclass(frozen=True)
class AdminInscripcionDetalleAdminResultado:
    """El detalle administrativo de una inscripción (`RT-IN-08`)."""

    item: AdminInscripcionListItemAdminResultado
    equipos_detalle: List[EquipoDeInscripcionAdminResultado] = field(default_factory=list)
    pool: Optional[PoolAdminResultado] = None
    compras: List[CompraDeCuposAdminResultado] = field(default_factory=list)
    historial: List[EventoHistorialAdminResultado] = field(default_factory=list)


# ── Superficie de los equipos (RT-IN-09 · RT-IN-10) ─────────────────────────


@dataclass(frozen=True)
class PlantillaEquipoAdminResultado:
    """Los TRES números de la plantilla de un equipo.

    Son tres hechos DISTINTOS: el navegador los imprime y nunca los compara
    (`contratos/01` §7). `minimo` y `maximo` son los que publica la
    disciplina del dueño.
    """

    registrados: int
    minimo: int
    maximo: int


@dataclass(frozen=True)
class CandidatoAEquipoAdminResultado:
    """Un candidato a entrar en un equipo.

    El veredicto del candidato es del BACKEND. El objetivo no publica un
    selector de candidatos, así que la lista viaja VACÍA (`A0-XCT02-11`).
    """

    id: str
    persona_id: str
    nombre: str
    documento: str
    estado_operativo: EstadoOperativoAdminResultado


@dataclass(frozen=True)
class AdminEquipoListItemAdminResultado:
    """Una fila de la lista administrativa de los equipos (`RT-IN-09`)."""

    id: str
    nombre: str
    disciplina: ReferenciaAdminResultado
    categoria: Optional[ReferenciaAdminResultado]
    plantilla: PlantillaEquipoAdminResultado
    estado_operativo: EstadoOperativoAdminResultado
    responsable: ReferenciaAdminResultado
    inscripcion: ReferenciaAdminResultado
    acciones_disponibles: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AdminEquipoDetalleAdminResultado:
    """El detalle administrativo de un equipo (`RT-IN-10`)."""

    item: AdminEquipoListItemAdminResultado
    participantes: List[ParticipanteDeEquipoAdminResultado] = field(default_factory=list)
    cupos: Optional[CuposOperativosAdminResultado] = None
    inscripcion_detalle: Optional[ReferenciaAdminResultado] = None
    elegibilidad: List[CandidatoAEquipoAdminResultado] = field(default_factory=list)


# ── Superficie de los participantes (RT-IN-11) ───────────────────────────────


@dataclass(frozen=True)
class ParticipacionAdminResultado:
    """Una participación de una persona, con su edición, equipo y disciplina."""

    id: str
    edicion: ReferenciaAdminResultado
    equipo: ReferenciaAdminResultado
    disciplina: ReferenciaAdminResultado
    rol: str
    estado: str
    conflicto: Optional[CausaAdminResultado]


@dataclass(frozen=True)
class ParticipanteAdminResultado:
    """Una persona de la búsqueda administrativa, con sus participaciones."""

    id: str
    nombre: str
    documento: str
    participaciones: List[ParticipacionAdminResultado] = field(default_factory=list)
    historial: List[EventoHistorialAdminResultado] = field(default_factory=list)


# ── Superficie de los pagos (RT-PG-04 · RT-PG-07) ───────────────────────────


@dataclass(frozen=True)
class CompradorAdminResultado:
    """El comprador de una compra."""

    persona_id: str
    nombre: str


@dataclass(frozen=True)
class EntregaDerechosAdminResultado:
    """Qué habilita la compra: el código y la etiqueta, nada más."""

    codigo: str
    etiqueta: str


@dataclass(frozen=True)
class CompraAdminResultado:
    """La compra que financia el pago.

    `reutilizada` NO se publica: el objetivo no lo persiste (es un hecho del
    flujo de creación) y publicarlo como `false` sería mentir.
    """

    id: str
    estado: str
    total: str
    moneda: str


@dataclass(frozen=True)
class IntentoPagoAdminResultado:
    """Un intento del proveedor, con su posición y su verificación."""

    id: str
    intento: int
    estado: str
    verificada: bool
    codigo_respuesta: str
    metodo_pago: str
    creada_en: datetime


@dataclass(frozen=True)
class OperacionManualAdminResultado:
    """Una operación manual de un administrador sobre un pago.

    El objetivo no tiene una aprobación manual persistida (`A0-XCT02-10`),
    así que la lista viaja VACÍA.
    """

    id: str
    canal: str
    monto: str
    moneda: str
    motivo: str
    registrada_en: datetime
    actor: str


@dataclass(frozen=True)
class AdminPagoListItemAdminResultado:
    """Una fila de la lista operativa de los pagos (`RT-PG-04`)."""

    compra_id: str
    orden_pago_id: Optional[str]
    tipo_compra: str
    resumen_concepto: str
    comprador: CompradorAdminResultado
    monto: str
    moneda: str
    estado_operativo: EstadoOperativoAdminResultado
    entrega_derechos: EntregaDerechosAdminResultado
    fecha: datetime
    acciones_disponibles: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AdminPagoDetalleAdminResultado:
    """El detalle comercial de un pago (`RT-PG-07`)."""

    item: AdminPagoListItemAdminResultado
    compra: Optional[CompraAdminResultado] = None
    origen_pago: str = ""
    intentos: List[IntentoPagoAdminResultado] = field(default_factory=list)
    operaciones_manuales: List[OperacionManualAdminResultado] = field(default_factory=list)
    siguiente_accion: Optional[AccionOperativaAdminResultado] = None


# ── Superficie de las personas (RT-ID-07 · RT-ID-08) ─────────────────────────


@dataclass(frozen=True)
class AdminPersonaListItemAdminResultado:
    """Una fila de la búsqueda administrativa de personas (`RT-ID-07`)."""

    id: str
    nombre: str
    documento: str
    participaciones: List[ParticipacionAdminResultado] = field(default_factory=list)
    historial: List[EventoHistorialAdminResultado] = field(default_factory=list)


@dataclass(frozen=True)
class AdminPersonaDetalleAdminResultado:
    """El detalle administrativo de una persona (`RT-ID-08`)."""

    item: AdminPersonaListItemAdminResultado
    telefono: str = ""
    whatsapp: str = ""
    email: str = ""


__all__ = [
    "AccionOperativaAdminResultado",
    "AdminEquipoDetalleAdminResultado",
    "AdminEquipoListItemAdminResultado",
    "AdminInscripcionDetalleAdminResultado",
    "AdminInscripcionListItemAdminResultado",
    "AdminPagoDetalleAdminResultado",
    "AdminPagoListItemAdminResultado",
    "AdminPersonaDetalleAdminResultado",
    "AdminPersonaListItemAdminResultado",
    "CandidatoAEquipoAdminResultado",
    "CausaAdminResultado",
    "CompraAdminResultado",
    "CompraDeCuposAdminResultado",
    "CompradorAdminResultado",
    "CuposOperativosAdminResultado",
    "EntregaDerechosAdminResultado",
    "EquipoDeInscripcionAdminResultado",
    "EventoHistorialAdminResultado",
    "IntentoPagoAdminResultado",
    "OperacionManualAdminResultado",
    "ParticipacionAdminResultado",
    "ParticipacionPoolAdminResultado",
    "ParticipanteAdminResultado",
    "ParticipanteDeEquipoAdminResultado",
    "PersonaAdminResultado",
    "PlantillaEquipoAdminResultado",
    "PoolAdminResultado",
    "ReferenciaAdminResultado",
    "EstadoOperativoAdminResultado",
]
