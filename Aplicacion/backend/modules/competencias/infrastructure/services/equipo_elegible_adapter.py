"""El adaptador de la ELEGIBILIDAD deportiva de un equipo.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.10

`modules.salesianos_fest` es el DUEÑO de la inscripción, del equipo, de su
disciplina, de su CATEGORÍA y del POOL de participantes (`RN-K01`). Este
adaptador CONSUME esos hechos y los traduce al veredicto del puerto
`IEquipoElegibleService`: **no decide** si un equipo es elegible, sólo
PREPARA la consulta y TRADUCE el resultado.

**La PRECEDENCIA del veredicto es fija y está documentada**, porque el
cliente recibe un único código de motivo y tiene que ser determinista:

| # | Motivo | Qué significa |
|---|---|---|
| 1 | `EQUIPO_NO_ENCONTRADO` | El equipo no existe. |
| 2 | `EDICION_DISTINTA` | El equipo pertenece a otra edición. |
| 3 | `DISCIPLINA_DISTINTA` | El equipo pertenece a otra disciplina. |
| 4 | `CATEGORIA_DISTINTA` | El equipo es de otra categoría. |
| 5 | `CATEGORIA_NO_ASIGNADA` | El equipo no tiene categoría asignada. |
| 6 | `DISCIPLINA_INACTIVA` | La disciplina del torneo no está activa. |
| 7 | `INSCRIPCION_CANCELADA` | La inscripción del equipo está cancelada. |
| 8 | `EQUIPO_NO_ACTIVO` | El equipo está retirado. |
| 9 | `SIN_PLANTILLA` | El equipo no tiene participantes activos. |
| 10 | `PLANTILLA_INCOMPLETA` | El equipo no alcanza el mínimo de participantes. |
| 11 | `ELEGIBLE` | El equipo puede competir. |

**La CATEGORÍA es la segunda mitad de la elegibilidad**: el equipo compite en
la disciplina Y en la categoría del torneo. Un equipo de otra categoría no
entra, y un equipo SIN categoría asignada tampoco: la categoría NUNCA se
adivina (`CATEGORIA_NO_ASIGNADA`).

**El listado NO filtra por elegibilidad**: devuelve un veredicto por cada
equipo CANDIDATO de la edición y la disciplina del torneo, elegible o no,
para que la interfaz pueda explicar POR QUÉ no puede entrar
(`frontend/05` §4). El filtro por CATEGORÍA tampoco se aplica al LISTADO:
acotarlo dejaría al equipo de otra categoría INVISIBLE y, con él, su motivo
`CATEGORIA_DISTINTA`. La categoría se compara en el VEREDICTO de cada
candidato.

**El alcance es de EDICIÓN** (`RN-E01`): el listado nunca expone equipos de
otra edición. Los motivos `EDICION_DISTINTA`, `DISCIPLINA_DISTINTA`,
`CATEGORIA_DISTINTA` y `CATEGORIA_NO_ASIGNADA` son los del VEREDICTO DE UN
EQUIPO (`verificar_elegibilidad`), donde el administrador elige un equipo y
un torneo: ahí sí puede equivocarse de edición, de disciplina o de
categoría, y el backend se lo dice con su propio código.
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
        categoria_id,
    ) -> list[EquipoElegibleData]:
        """Los veredictos de los equipos CANDIDATOS del torneo.

        Los candidatos son los equipos de la EDICIÓN y de la DISCIPLINA del
        torneo: el listado es de alcance de edición (`RN-E01`). La CATEGORÍA
        del torneo se compara en cada veredicto, pero NO acota la lista: un
        equipo de otra categoría debe SEGUIR apareciendo con su motivo
        (`CATEGORIA_DISTINTA`), porque de lo contrario la interfaz no puede
        explicar por qué no entra.
        """
        disciplina = self._disciplina(disciplina_id)
        from modules.salesianos_fest.domain.models import Equipo

        equipos = (
            Equipo.objects.filter(
                inscripcion__edicion_id=edicion_id,
                disciplina_id=disciplina_id,
            )
            .select_related("inscripcion", "disciplina", "categoria")
            .order_by("nombre")
        )
        return [
            self._veredicto_de(
                equipo,
                disciplina,
                edicion_id,
                disciplina_id,
                categoria_id,
            )
            for equipo in equipos
        ]

    def verificar_elegibilidad(
        self,
        equipo_id,
        edicion_id,
        disciplina_id,
        categoria_id,
    ) -> EquipoElegibleData:
        """El veredicto de UN equipo frente a un torneo.

        Un equipo que no existe tiene su propio veredicto
        (`EQUIPO_NO_ENCONTRADO`): el puerto NO lanza, decide el dominio.
        """
        disciplina = self._disciplina(disciplina_id)
        from modules.salesianos_fest.domain.models import Equipo

        equipo = (
            Equipo.objects.select_related("inscripcion", "disciplina", "categoria")
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
                categoria_id=None,
                categoria_nombre="",
                estado="",
                es_elegible=False,
                motivo=MotivoNoElegibilidad.EQUIPO_NO_ENCONTRADO,
                participantes_activos=0,
                minimo_requerido=disciplina.minimo_por_equipo,
            )
        return self._veredicto_de(
            equipo,
            disciplina,
            edicion_id,
            disciplina_id,
            categoria_id,
        )

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

    def _veredicto_de(self, equipo, disciplina, edicion_id, disciplina_id, categoria_id):
        """El veredicto de un equipo, según la PRECEDENCIA documentada."""
        from modules.salesianos_fest.domain.constants import (
            EstadoDisciplina,
            EstadoEquipo,
            EstadoInscripcion,
        )

        participantes_activos = self._participantes_activos(equipo.id)
        minimo_requerido = disciplina.minimo_por_equipo
        categoria_del_torneo = str(categoria_id) if categoria_id else None
        categoria_del_equipo = str(equipo.categoria_id) if equipo.categoria_id else None

        motivo = MotivoNoElegibilidad.ELEGIBLE
        if str(equipo.inscripcion.edicion_id) != str(edicion_id):
            motivo = MotivoNoElegibilidad.EDICION_DISTINTA
        elif str(equipo.disciplina_id) != str(disciplina_id):
            motivo = MotivoNoElegibilidad.DISCIPLINA_DISTINTA
        elif (
            categoria_del_equipo is not None
            and categoria_del_torneo is not None
            and categoria_del_equipo != categoria_del_torneo
        ):
            motivo = MotivoNoElegibilidad.CATEGORIA_DISTINTA
        elif categoria_del_equipo is None or categoria_del_torneo is None:
            motivo = MotivoNoElegibilidad.CATEGORIA_NO_ASIGNADA
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
            categoria_id=categoria_del_equipo,
            categoria_nombre=(
                equipo.categoria.nombre if equipo.categoria is not None else ""
            ),
            estado=equipo.estado,
            es_elegible=motivo == MotivoNoElegibilidad.ELEGIBLE,
            motivo=motivo,
            participantes_activos=participantes_activos,
            minimo_requerido=minimo_requerido,
        )


__all__ = ["EquipoElegibleAdapter"]
