"""El adaptador de la ELEGIBILIDAD deportiva de un equipo.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.10

`modules.salesianos_fest` es el DUEÑO de la inscripción, del equipo, de su
disciplina y del POOL de participantes (`RN-K01`). Este adaptador CONSUME
esos hechos y los traduce al veredicto del puerto
`IEquipoElegibleService`: **no decide** si un equipo es elegible, sólo
PREPARA la consulta y TRADUCE el resultado.

**La PRECEDENCIA del veredicto es fija y está documentada**, porque el
cliente recibe un único código de motivo y tiene que ser determinista:

| # | Motivo | Qué significa |
|---|---|---|
| 1 | `EQUIPO_NO_ENCONTRADO` | El equipo no existe. |
| 2 | `EDICION_DISTINTA` | El equipo pertenece a otra edición. |
| 3 | `DISCIPLINA_DISTINTA` | El equipo pertenece a otra disciplina. |
| 4 | `DISCIPLINA_INACTIVA` | La disciplina del torneo no está activa. |
| 5 | `INSCRIPCION_CANCELADA` | La inscripción del equipo está cancelada. |
| 6 | `EQUIPO_NO_ACTIVO` | El equipo está retirado. |
| 7 | `SIN_PLANTILLA` | El equipo no tiene participantes activos. |
| 8 | `PLANTILLA_INCOMPLETA` | El equipo no alcanza el mínimo de participantes. |
| 9 | `ELEGIBLE` | El equipo puede competir. |

**El listado NO filtra por elegibilidad**: devuelve un veredicto por cada
equipo CANDIDATO de la edición y la disciplina del torneo, elegible o no,
para que la interfaz pueda explicar POR QUÉ no puede entrar
(`frontend/05` §4).

**El alcance es de EDICIÓN** (`RN-E01`): el listado nunca expone equipos de
otra edición. Los motivos `EDICION_DISTINTA` y `DISCIPLINA_DISTINTA` son los
del VEREDICTO DE UN EQUIPO (`verificar_elegibilidad`), donde el administrador
elige un equipo y un torneo: ahí sí puede equivocarse de edición o de
disciplina, y el backend se lo dice con su propio código.
"""

from modules.competencias.domain.constants import MotivoNoElegibilidad
from modules.competencias.domain.exceptions import DisciplinaNoEncontradaError
from modules.competencias.domain.ports import IEquipoElegibleService
from modules.competencias.domain.schemas.competencias_schemas import (
    EquipoElegibleData,
)


class EquipoElegibleAdapter(IEquipoElegibleService):
    """Puente con el dueño de la inscripción y del pool de participantes."""

    # ── lecturas ───────────────────────────────────────────────────────────

    def listar_equipos_elegibles(
        self,
        edicion_id,
        disciplina_id,
    ) -> list[EquipoElegibleData]:
        """Los veredictos de los equipos CANDIDATOS del torneo.

        Los candidatos son los equipos de la EDICIÓN y de la DISCIPLINA del
        torneo: el listado es de alcance de edición (`RN-E01`).
        """
        disciplina = self._disciplina(disciplina_id)
        from modules.salesianos_fest.domain.models import Equipo

        equipos = (
            Equipo.objects.filter(
                inscripcion__edicion_id=edicion_id,
                disciplina_id=disciplina_id,
            )
            .select_related("inscripcion", "disciplina")
            .order_by("nombre")
        )
        return [
            self._veredicto_de(equipo, disciplina, edicion_id, disciplina_id)
            for equipo in equipos
        ]

    def verificar_elegibilidad(
        self,
        equipo_id,
        edicion_id,
        disciplina_id,
    ) -> EquipoElegibleData:
        """El veredicto de UN equipo frente a un torneo.

        Un equipo que no existe tiene su propio veredicto
        (`EQUIPO_NO_ENCONTRADO`): el puerto NO lanza, decide el dominio.
        """
        disciplina = self._disciplina(disciplina_id)
        from modules.salesianos_fest.domain.models import Equipo

        equipo = (
            Equipo.objects.select_related("inscripcion", "disciplina")
            .filter(id=equipo_id)
            .first()
        )
        if equipo is None:
            return EquipoElegibleData(
                equipo_id=str(equipo_id),
                nombre="",
                edicion_id=str(edicion_id),
                disciplina_id=str(disciplina_id),
                disciplina_nombre=disciplina.nombre,
                estado="",
                es_elegible=False,
                motivo=MotivoNoElegibilidad.EQUIPO_NO_ENCONTRADO,
                participantes_activos=0,
                minimo_requerido=disciplina.minimo_por_equipo,
            )
        return self._veredicto_de(equipo, disciplina, edicion_id, disciplina_id)

    # ── internos ───────────────────────────────────────────────────────────

    @staticmethod
    def _disciplina(disciplina_id):
        """La disciplina del torneo, o el error de no encontrada (404)."""
        from modules.salesianos_fest.domain.models import Disciplina

        disciplina = Disciplina.objects.filter(id=disciplina_id).first()
        if disciplina is None:
            raise DisciplinaNoEncontradaError()
        return disciplina

    @staticmethod
    def _participantes_activos(equipo_id) -> int:
        """Cuántos participantes ACTIVOS tiene el equipo en el pool."""
        from modules.salesianos_fest.domain.constants import EstadoParticipacion
        from modules.salesianos_fest.domain.models import Participacion

        return Participacion.objects.filter(
            equipo_id=equipo_id,
            estado=EstadoParticipacion.ACTIVA,
        ).count()

    def _veredicto_de(self, equipo, disciplina, edicion_id, disciplina_id):
        """El veredicto de un equipo, según la PRECEDENCIA documentada."""
        from modules.salesianos_fest.domain.constants import (
            EstadoDisciplina,
            EstadoEquipo,
            EstadoInscripcion,
        )

        participantes_activos = self._participantes_activos(equipo.id)
        minimo_requerido = disciplina.minimo_por_equipo

        motivo = MotivoNoElegibilidad.ELEGIBLE
        if str(equipo.inscripcion.edicion_id) != str(edicion_id):
            motivo = MotivoNoElegibilidad.EDICION_DISTINTA
        elif str(equipo.disciplina_id) != str(disciplina_id):
            motivo = MotivoNoElegibilidad.DISCIPLINA_DISTINTA
        elif disciplina.estado != EstadoDisciplina.ACTIVA:
            motivo = MotivoNoElegibilidad.DISCIPLINA_INACTIVA
        elif equipo.inscripcion.estado == EstadoInscripcion.CANCELADA:
            motivo = MotivoNoElegibilidad.INSCRIPCION_CANCELADA
        elif equipo.estado != EstadoEquipo.ACTIVO:
            motivo = MotivoNoElegibilidad.EQUIPO_NO_ACTIVO
        elif participantes_activos == 0:
            motivo = MotivoNoElegibilidad.SIN_PLANTILLA
        elif participantes_activos < minimo_requerido:
            motivo = MotivoNoElegibilidad.PLANTILLA_INCOMPLETA

        return EquipoElegibleData(
            equipo_id=str(equipo.id),
            nombre=equipo.nombre,
            edicion_id=str(equipo.inscripcion.edicion_id),
            disciplina_id=str(equipo.disciplina_id),
            disciplina_nombre=equipo.disciplina.nombre,
            estado=equipo.estado,
            es_elegible=motivo == MotivoNoElegibilidad.ELEGIBLE,
            motivo=motivo,
            participantes_activos=participantes_activos,
            minimo_requerido=minimo_requerido,
        )


__all__ = ["EquipoElegibleAdapter"]
