"""Puertos (interfaces) del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

El módulo cruza al DOMINIO en un solo punto, y ese cruce es por PUERTO:

1. **La elegibilidad deportiva de un equipo** — la resuelve
   `modules.salesianos_fest` (DOM-01 + DOM-02), que es su DUEÑO: la
   inscripción, la disciplina, la categoría, el estado del equipo y el pool de
   participantes son hechos suyos. Este módulo NO reimplementa ninguna de esas
   reglas: las CONSUME por el puerto `IEquipoElegibleService` (`RN-K01`,
   `QA-K01`).

La razón es ESTABLE y la publica el backend: el veredicto del puerto trae un
código de `MotivoNoElegibilidad`, y el dominio lo traduce a una excepción con
código público. El cliente nunca deduce la razón.

`eventos.EdicionScopeService` (FND-02) también se cruza por puerto, con
`IAlcanceEdicionService`, cuyo adaptador ya existe en `salesianos_fest`: este
módulo lo reutiliza a través del mismo binding para no duplicar el orden
congelado de resolución de edición (`FR-02` §2.2).
"""

from abc import ABC, abstractmethod

from modules.competencias.domain.schemas.competencias_schemas import (
    EquipoElegibleData,
)


class IAlcanceEdicion(ABC):
    """Resuelve el ALCANCE de edición de la operación.

    `modules.eventos` es el DUEÑO del orden congelado de resolución
    (`FREEZE-ED-1.0.0` · `FR-02` §2.2). Este puerto NO reimplementa ese orden:
    lo CONSUME a través del adaptador de `infrastructure/`, igual que hacen
    `salesianos_fest` y `marketplace`.

    El módulo lo necesita para las operaciones que NO llevan la edición en el
    camino — la agenda transversal del día — y para comprobar que la edición
    de una competencia pertenece al alcance pedido. Toda competencia, ronda y
    encuentro lleva su edición EXPLÍCITA (`RN-E01`): el alcance sólo aparece
    donde la ruta no lo declara.
    """

    @abstractmethod
    def resolver_explicita(self, edicion_id, *, exigir_publicada: bool = False):
        """Nivel 1 del orden congelado: el `edicion_id` explícito.

        Raises:
            `EdicionNoEncontradaError`: el identificador no existe.
            `EdicionNoPublicadaError`: existe pero no está `PUBLICADA`.
        """
        ...

    @abstractmethod
    def resolver_actual(
        self,
        *,
        ediciones_activas_actor=None,
        exigir_publicada: bool = False,
        permitir_publicada_por_defecto: bool = True,
    ):
        """Niveles 2, 3 y 4 del orden congelado.

        Se usa cuando la operación NO lleva la edición en el camino (la agenda
        del día): nunca hay un fallback informal al evento activo.
        """
        ...


class IEquipoElegibleService(ABC):
    """Resuelve la ELEGIBILIDAD deportiva de un equipo para competir.

    Es una consulta de SOLO LECTURA sobre el módulo dueño de la inscripción.
    No crea equipos, no cambia inscripciones y no toca el pool: sólo responde
    si un equipo puede competir en una edición, disciplina y categoría
    concretas, y POR QUÉ no puede si no puede.

    **La CATEGORÍA es obligatoria en las dos operaciones**: la elegibilidad
    deportiva es la coincidencia de EDICIÓN + DISCIPLINA + CATEGORÍA
    (`RN-K01`). Un equipo de otra categoría no compite en este cuadro, y un
    equipo sin categoría asignada tampoco: la categoría NUNCA se adivina.
    """

    @abstractmethod
    def listar_equipos_elegibles(
        self,
        edicion_id,
        disciplina_id,
        categoria_id,
    ) -> list[EquipoElegibleData]:
        """Los equipos de la edición y disciplina que PUEDEN competir.

        Args:
            edicion_id: edición del torneo.
            disciplina_id: disciplina del torneo.
            categoria_id: categoría del torneo. Es OBLIGATORIA: cada
                veredicto se calcula contra ella.

        Returns:
            Un veredicto por cada equipo CANDIDATO de esa edición y
            disciplina, elegibles o no: el veredicto lleva el motivo del
            rechazo para que la interfaz pueda explicarlo (`frontend/05` §4).
        """
        ...

    @abstractmethod
    def verificar_elegibilidad(
        self,
        equipo_id,
        edicion_id,
        disciplina_id,
        categoria_id,
    ) -> EquipoElegibleData:
        """El veredicto de elegibilidad de UN equipo.

        Un equipo que no existe tiene su propio veredicto
        (`EQUIPO_NO_ENCONTRADO`): el puerto no lanza, decide el dominio.
        """
        ...


__all__ = ["IAlcanceEdicion", "IEquipoElegibleService"]
