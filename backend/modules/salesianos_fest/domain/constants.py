"""
Constants — choices for domain models in salesianos_fest module.
"""
from django.db import models


class ModalidadChoices(models.TextChoices):
    """Modalidad de una disciplina."""

    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"
    MIXTO = "X", "Mixto"


class TipoPaqueteChoices(models.TextChoices):
    """Tipo de paquete comercial."""

    PACK = "PACK", "Pack (con beneficios)"
    DISCIPLINA = "DISCIPLINA", "Disciplina individual"


class ModoDisciplinasChoices(models.TextChoices):
    """Modo de selección de disciplinas en un paquete."""

    FIJO = "FIJO", "Fijo"
    ELEGIBLE = "ELEGIBLE", "Elegible por el participante"


class EtapaChoices(models.TextChoices):
    """Etapa de precio de un paquete."""

    PREVENTA = "PREVENTA", "Preventa"
    REGULAR = "REGULAR", "Regular"


class TipoBeneficioChoices(models.TextChoices):
    """Tipo de beneficio incluido en un paquete."""

    FIESTA = "FIESTA", "Fiesta"
    BOX = "BOX", "Box de bebidas"
    CERVEZA = "CERVEZA", "Cerveza"


class AlcanceBeneficioChoices(models.TextChoices):
    """Alcance de un beneficio."""

    INDIVIDUAL = "INDIVIDUAL", "Individual"
    GRUPAL = "GRUPAL", "Grupal"


class ModoCalculoBeneficioChoices(models.TextChoices):
    """Modo de cálculo de cantidad de beneficio."""

    POR_CUPO = "POR_CUPO", "Por cupo"
    FIJO_INICIAL = "FIJO_INICIAL", "Fijo (compra inicial)"


# ─── Inscripción / Equipo / Participación ─────────────────────────────────────


class EstadoInscripcionChoices(models.TextChoices):
    """Estado deportivo/administrativo de una inscripción.

    No incluye estados comerciales (PAGADA, etc.) — el pago es gestionado
    por un módulo externo en Fase 4+.

    Las transiciones exactas y roles autorizados están pendientes
    de confirmación de producto (sección 5 de la spec).
    """

    BORRADOR = "BORRADOR", "Borrador"
    RECIBIDA = "RECIBIDA", "Recibida"
    EN_REVISION = "EN_REVISION", "En revisión"
    OBSERVADA = "OBSERVADA", "Observada"
    VALIDADA = "VALIDADA", "Validada"
    CONFIRMADA = "CONFIRMADA", "Confirmada"
    RECHAZADA = "RECHAZADA", "Rechazada"
    CANCELADA = "CANCELADA", "Cancelada"


class EstadoEquipoChoices(models.TextChoices):
    """Estado de un equipo dentro de una inscripción."""

    EQUIPO_ACTIVO = "EQUIPO_ACTIVO", "Activo"
    EQUIPO_CANCELADO = "EQUIPO_CANCELADO", "Cancelado"


class EstadoInscripcionPersonaChoices(models.TextChoices):
    """Estado del vínculo entre persona e inscripción."""

    ACTIVO = "A", "Activo"
    RETIRADO = "R", "Retirado"


class RolParticipanteChoices(models.TextChoices):
    """Rol de una persona dentro de un equipo."""

    JUGADOR = "J", "Jugador"
    CAPITAN = "C", "Capitán"
    DELEGADO = "D", "Delegado"


class EstadoParticipacionChoices(models.TextChoices):
    """Estado de una participación dentro de un equipo."""

    ACTIVA = "A", "Activa"
    RETIRADA = "R", "Retirada"


# ─── Compra / Pago ──────────────────────────────────────────────────────────────


class TipoCompraChoices(models.TextChoices):
    """Tipo de compra comercial."""

    INICIAL = "INICIAL", "Inicial"
    AMPLIACION = "AMPLIACION", "Ampliacion"


class EstadoCompraChoices(models.TextChoices):
    """Estado comercial de una compra.

    El estado es exclusivamente comercial — NO representa el estado
    deportivo/administrativo de la Inscripcion. Una compra PAGADA
    no implica confirmacion deportiva.
    """

    PENDIENTE = "PENDIENTE", "Pendiente"
    PAGADA = "PAGADA", "Pagada"
    CANCELADA = "CANCELADA", "Cancelada"


# ─── Reconciliación de pagos ──────────────────────────────────────────────────


class EstadoReconciliacionPagoChoices(models.TextChoices):
    """Estado de una orden de pago revisada por la reconciliación.

    RECONCILIADA  — la compra pendiente fue liquidada en esta ejecución.
    YA_LIQUIDADA  — la compra ya estaba liquidada (ejecución idempotente).
    OMITIDA       — la orden no se liquidó; `motivo` explica por qué.
    ERROR         — la liquidación falló; se puede reintentar.
    """

    RECONCILIADA = "RECONCILIADA", "Reconciliada"
    YA_LIQUIDADA = "YA_LIQUIDADA", "Ya liquidada"
    OMITIDA = "OMITIDA", "Omitida"
    ERROR = "ERROR", "Error"


class MotivoReconciliacionPagoChoices(models.TextChoices):
    """Motivo estable por el que una orden no se liquidó en la reconciliación."""

    SIN_PAGO_VERIFICADO = "SIN_PAGO_VERIFICADO", "Sin pago verificado"
    PAGO_NO_CORRELACIONADO = "PAGO_NO_CORRELACIONADO", "Pago no correlacionado"
    SIN_COMPRA_PENDIENTE = "SIN_COMPRA_PENDIENTE", "Sin compra pendiente"
    ORDEN_NO_PAGADA = "ORDEN_NO_PAGADA", "Orden no pagada"
    SIMULACION = "SIMULACION", "Simulación"


# ─── Reparación de cupos pagados ──────────────────────────────────────────────


class EstadoReparacionCupoChoices(models.TextChoices):
    """Estado de una inscripción revisada por la reparación de cupos.

    REPARADA      — se materializaron los cupos pagados pendientes.
    SIN_PENDIENTES — no había participantes esperando un cupo pagado.
    OMITIDA       — la inscripción no se revisó (sin capacidad pagada).
    ERROR         — la reparación falló; se puede reintentar.
    """

    REPARADA = "REPARADA", "Reparada"
    SIN_PENDIENTES = "SIN_PENDIENTES", "Sin participantes pendientes"
    OMITIDA = "OMITIDA", "Omitida"
    ERROR = "ERROR", "Error"


# ─── Phase 5: AsignacionCupo / Acreditacion / ControlAcceso ─────────────────


class EstadoAsignacionCupoChoices(models.TextChoices):
    """Estado de una asignacion de cupo."""

    ACTIVA = "ACTIVA", "Activa"
    LIBERADA = "LIBERADA", "Liberada"
    REVOCADA = "REVOCADA", "Revocada"


class EstadoPoolChoices(models.TextChoices):
    """Estado de elegibilidad de un participante del pool de pre-registro.

    Es un discriminador de UI, no un estado persistido: no se guarda en la
    base de datos y no modifica `InscripcionPersona.estado`. El backend lo
    deriva del cupo pagado y de la capacidad pagada de la inscripcion.

    LISTO            — la persona tiene un cupo pagado activo: puede asignarse
                       a un equipo.
    ESPERANDO_PAGO   — la inscripcion todavia no tiene capacidad pagada: la
                       persona espera el pago de su cupo.
    SIN_CAPACIDAD    — la capacidad pagada esta agotada: la persona necesita
                       una ampliacion de cupos.
    CUPO_POR_ASIGNAR — la inscripcion tiene cupo pagado disponible pero la
                       persona todavia no lo tiene asignado (situacion a
                       repairing, nunca la causa de "esperando pago").
    """

    LISTO = "LISTO", "Listo para equipo"
    ESPERANDO_PAGO = "ESPERANDO_PAGO", "Esperando pago"
    SIN_CAPACIDAD = "SIN_CAPACIDAD", "Sin capacidad pagada"
    CUPO_POR_ASIGNAR = "CUPO_POR_ASIGNAR", "Cupo por asignar"


# ─── Pool de participantes: motivos de bloqueo (UI-safe) ─────────────────────
#
# Son mensajes para la persona responsable, no codigos internos. El frontend
# los replica 1:1 (contrato API §7) y los usa SOLO como fallback cuando el
# backend no devuelve el discriminador `estado_pool`.

MOTIVO_ESPERANDO_PAGO = "Esperando el pago del cupo"
MOTIVO_SIN_CAPACIDAD = "No hay cupos pagados disponibles"
MOTIVO_CUPO_POR_ASIGNAR = "Cupo pagado disponible sin asignar"

# Razon UI-safe cuando la persona ya juega activamente en la disciplina del
# equipo destino. Un solo cupo comercial habilita a la persona en TODAS las
# disciplinas contratadas, pero nunca dos veces en la misma (regla R11).
MOTIVO_YA_EN_DISIPLINA = "Ya participa en esta disciplina"

# Razon UI-safe cuando la modalidad de la disciplina destino no acepta el
# genero PERSISTIDO de la persona. El texto solo explica la regla: no expone
# identificadores, generos crudos ni modalidades (contrato de API, mensajes
# publicos seguros). La matriz la decide el predicado compartido
# `domain/validators/participacion.py` — este texto solo la traduce.
MOTIVO_GENERO_NO_COMPATIBLE = (
    "La modalidad de la disciplina no es compatible con el género de la persona"
)


class EstadoAcreditacionChoices(models.TextChoices):
    """Estado de una acreditacion de evento."""

    PENDIENTE = "PENDIENTE", "Pendiente"
    ACTIVA = "ACTIVA", "Activa"
    SUSPENDIDA = "SUSPENDIDA", "Suspendida"
    REVOCADA = "REVOCADA", "Revocada"


class AutorizacionFiestaChoices(models.TextChoices):
    """Origen de la autorizacion de acceso a fiesta."""

    AUTOMATICA = "AUTOMATICA", "Automatica"
    AUTORIZADA = "AUTORIZADA", "Autorizada por admin"
    BLOQUEADA = "BLOQUEADA", "Bloqueada por admin"


class ResultadoAccesoChoices(models.TextChoices):
    """Resultado de un intento de acceso QR."""

    PERMITIDO = "PERMITIDO", "Permitido"
    DENEGADO = "DENEGADO", "Denegado"


# ─── Phase 6: Consentimientos ───────────────────────────────────────────────────


class TipoAceptacionChoices(models.TextChoices):
    """Tipo de aceptacion de documento legal."""

    BASES = "BASES", "Bases del evento"
    APTITUD_FISICA = "APTITUD_FISICA", "Certificado de aptitud fisica"
    IMAGEN = "IMAGEN", "Uso de imagen"


class MedioAceptacionChoices(models.TextChoices):
    """Medio por el cual se declaro la aceptacion."""

    WEB = "WEB", "Formulario web"
    MOBILE = "MOBILE", "Aplicacion movil"
    PAPER = "PAPER", "Papel"


# ─── Pases de fiesta (catálogo independiente) ───────────────────────────────
#
# Los pases de fiesta son un catálogo PARALELO al de paquetes deportivos.
# Nunca se modelan como `Paquete.tipo=PASE`: el contrato público del paquete
# (`tipo`, `modo_disciplinas`, `cantidad_disciplinas`, `minimo_compra_inicial`)
# es deportivo y un pase no tiene disciplinas, equipos ni beneficios de
# paquete. El pase reutiliza las mismas etapas de precio (`EtapaChoices`).


CANTIDAD_MAXIMA_SIN_LIMITE = 0
"""`Pase.cantidad_maxima == 0` significa inventario ILIMITADO.

Centinela compartido por el modelo, el selector y el seed: un pase sin
límite no debe interpretarse como "no se pueden vender pases".
"""

CANTIDAD_MAXIMA_POR_COMPRA = 50
"""Tope de pases que un comprador puede pedir en una sola compra.

Protege el lote de una compra (y, más adelante, el número de beneficiarios
que habrá que asignar). Es un límite COMERCIAL, no de inventario: el tope real
de unidades lo fija `Pase.cantidad_maxima`.
"""


# ─── Pases de fiesta: derechos nominativos ──────────────────────────────────


class EstadoPaseBeneficiarioChoices(models.TextChoices):
    """Estado de un derecho nominativo de pase.

    ACTIVA   — el derecho concede acceso a la fiesta.
    REVOCADA — el derecho se revocó con motivo: el SLOT queda CONSUMIDO de
               forma permanente (un pase pagado no se transfiere en v1).
    """

    ACTIVA = "ACTIVA", "Activa"
    REVOCADA = "REVOCADA", "Revocada"
