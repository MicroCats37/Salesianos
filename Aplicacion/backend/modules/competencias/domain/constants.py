"""Vocabulario cerrado del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Regla: `contract/django-app-architecture-contract.md` §5 y §10 — los
vocabularios son `TextChoices` cerrados y sus valores son IDENTIFICADORES
ESTABLES: se persisten, se filtran y se indexan, así que no se renombran sin
migración.

Este archivo NO declara:

- las reglas de elegibilidad de `salesianos_fest` (son de su dueño): sólo
  declara el vocabulario de los MOTIVOS por los que este módulo rechaza un
  equipo;
- la duración de un encuentro, el número de rondas ni el formato del cuadro:
  ningún contrato los congela y aquí no se inventan;
- la regla de solapamiento por disciplina: se aplica la regla GLOBAL de la
  edición (`RN-K03`) porque ninguna regla por disciplina está congelada.
"""

from django.db import models


class EstadoCompetencia(models.TextChoices):
    """Ciclo de vida de una competencia.

    `PLANIFICADA` → `EN_CURSO` → `FINALIZADA`, con `CANCELADA` como salida
    terminal. La cancelación NO borra nada: la historia auditada se conserva.
    """

    PLANIFICADA = "PLANIFICADA", "Planificada"
    EN_CURSO = "EN_CURSO", "En curso"
    FINALIZADA = "FINALIZADA", "Finalizada"
    CANCELADA = "CANCELADA", "Cancelada"


class EstadoCompetenciaEquipo(models.TextChoices):
    """Estado de un equipo dentro del cuadro de una competencia.

    Un equipo `RETIRADO` conserva su historia: nunca se borra (`RN-K02`).
    """

    ACTIVO = "ACTIVO", "Activo"
    RETIRADO = "RETIRADO", "Retirado"


class EstadoRonda(models.TextChoices):
    """Estado de una ronda del cuadro.

    Una ronda `INVALIDADA` se conserva: el cuadro que se dibujó con ella sigue
    en la historia.
    """

    ACTIVA = "ACTIVA", "Activa"
    INVALIDADA = "INVALIDADA", "Invalidada"


class EstadoEncuentro(models.TextChoices):
    """Ciclo de vida de un encuentro.

    `BORRADOR` — sin participantes ni horario (el cuadro puede estar vacío o
    parcial: `frontend/05` §1.3).
    `PROGRAMADO` — con horario, listo para jugar.
    `EN_CURSO` — en juego; es el único estado que acepta un resultado.
    `FINALIZADO` — con ganador autoritativo.
    `CANCELADO` — libera el horario del equipo: no reserva la franja.
    """

    BORRADOR = "BORRADOR", "Borrador"
    PROGRAMADO = "PROGRAMADO", "Programado"
    EN_CURSO = "EN_CURSO", "En curso"
    FINALIZADO = "FINALIZADO", "Finalizado"
    CANCELADO = "CANCELADO", "Cancelado"


class SlotDestino(models.TextChoices):
    """Slot del encuentro enlazado que recibe al ganador propagado."""

    PARTICIPANTE_1 = "PARTICIPANTE_1", "Participante 1"
    PARTICIPANTE_2 = "PARTICIPANTE_2", "Participante 2"


class MotivoNoElegibilidad(models.TextChoices):
    """MOTIVOS por los que un equipo NO es elegible para competir.

    El vocabulario es CERRADO y cada motivo tiene su propio código de máquina:
    el backend publica la razón y el cliente nunca la adivina (`QA-K01`).

    Los motivos que describen el estado de la INSCRIPCIÓN (edición,
    disciplina, inscripción viva, equipo activo, plantilla) los decide
    `modules.salesianos_fest`; este módulo los consume por PUERTO y sólo los
    traduce a su vocabulario público.
    """

    ELEGIBLE = "ELEGIBLE", "Elegible"
    EQUIPO_NO_ENCONTRADO = "EQUIPO_NO_ENCONTRADO", "El equipo no existe"
    EDICION_DISTINTA = "EDICION_DISTINTA", "El equipo pertenece a otra edición"
    DISCIPLINA_DISTINTA = "DISCIPLINA_DISTINTA", "El equipo pertenece a otra disciplina"
    DISCIPLINA_INACTIVA = "DISCIPLINA_INACTIVA", "La disciplina no está activa"
    INSCRIPCION_CANCELADA = "INSCRIPCION_CANCELADA", "La inscripción está cancelada"
    EQUIPO_NO_ACTIVO = "EQUIPO_NO_ACTIVO", "El equipo está retirado"
    SIN_PLANTILLA = "SIN_PLANTILLA", "El equipo no tiene participantes activos"
    PLANTILLA_INCOMPLETA = "PLANTILLA_INCOMPLETA", "El equipo no alcanza el mínimo de participantes"


#: Campo de `Encuentro` que guarda cada slot de destino. El avance y la
#: corrección leen y escriben el slot por esta tabla, así que las dos
#: operaciones nunca discuten sobre qué campo están hablando.
CAMPOS_DE_SLOT: dict[str, str] = {
    SlotDestino.PARTICIPANTE_1: "participante_1",
    SlotDestino.PARTICIPANTE_2: "participante_2",
}

#: Longitud mínima del motivo auditado de una operación protegida.
MINIMO_MOTIVO = 5

#: Longitud máxima del motivo auditado de una operación protegida.
MAXIMO_MOTIVO = 500

#: Orden mínimo de una ronda, de un equipo o de un encuentro.
MINIMO_ORDEN = 1

#: Orden máximo de una ronda, de un equipo o de un encuentro.
MAXIMO_ORDEN = 999

#: Longitud máxima del nombre de una competencia.
MAXIMO_NOMBRE = 200

#: Longitud máxima de la etiqueta de una ronda.
MAXIMO_ETIQUETA = 80

#: Longitud máxima del detalle del marcador de un encuentro.
MAXIMO_DETALLE_MARCADOR = 500


__all__ = [
    "CAMPOS_DE_SLOT",
    "MAXIMO_DETALLE_MARCADOR",
    "MAXIMO_ETIQUETA",
    "MAXIMO_MOTIVO",
    "MAXIMO_NOMBRE",
    "MAXIMO_ORDEN",
    "MINIMO_MOTIVO",
    "MINIMO_ORDEN",
    "EstadoCompetencia",
    "EstadoCompetenciaEquipo",
    "EstadoEncuentro",
    "EstadoRonda",
    "MotivoNoElegibilidad",
    "SlotDestino",
]
