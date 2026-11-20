"""Servicios core de `Competencia`, `CompetenciaEquipo` y `Ronda`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3

Son SYNC, NO abren `transaction.atomic()` (la atomicidad la posee el flujo) y
NO contienen reglas que el dueño de otro módulo ya decide: la elegibilidad
del equipo se CONSUME por el puerto `IEquipoElegibleService`
(`modules.competencias.domain.ports`).

**El modelo de `Disciplina`, el de `Categoria` y el de `Equipo` se resuelven
por METADATOS del propio campo `Competencia.disciplina` /
`Competencia.categoria` / `CompetenciaEquipo.equipo`**: este módulo ya declara
esa dependencia en sus propios modelos, así que la resuelve explícitamente en
vez de importar el dominio de otro módulo.
"""

from modules.competencias.domain.constants import (
    MAXIMO_ORDEN,
    MINIMO_ORDEN,
    EstadoCompetencia,
    EstadoCompetenciaEquipo,
    EstadoRonda,
)
from modules.competencias.domain.exceptions import (
    CategoriaNoEncontradaError,
    CompetenciaDuplicadaError,
    CompetenciaEquipoDuplicadoError,
    DisciplinaNoEncontradaError,
    EquipoNoElegibleError,
    OrdenDuplicadoError,
    RondaDuplicadaError,
    TransicionInvalidaError,
)
from modules.competencias.domain.models import (
    Competencia,
    CompetenciaEquipo,
    Ronda,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    CompetenciaCreateData,
    EquipoCompetenciaCreateData,
    EquipoCompetenciaEditData,
    RondaCreateData,
)
from modules.competencias.domain.services.core.base_service import BaseCoreService

#: Modelo `Disciplina`, resuelto desde el PROPIO campo de este módulo.
MODELO_DISCIPLINA = Competencia._meta.get_field("disciplina").related_model

#: Modelo `Categoria`, resuelto desde el PROPIO campo de este módulo.
MODELO_CATEGORIA = Competencia._meta.get_field("categoria").related_model

#: Estados en los que una competencia ya no admite cambios.
ESTADOS_TERMINALES_COMPETENCIA = {
    EstadoCompetencia.FINALIZADA,
    EstadoCompetencia.CANCELADA,
}


class CompetenciaCoreService(BaseCoreService):
    """Operaciones sync sobre `Competencia` — el llamador posee la transacción."""

    def crear(self, edicion, data: CompetenciaCreateData) -> Competencia:
        """Crea la competencia con su identidad y su día.

        La identidad es (edición, disciplina, categoría, nombre) comparada SIN
        distinguir mayúsculas: "Final" y "final" son la MISMA competencia.

        La disciplina tiene que ser de la MISMA edición que la competencia: la
        disciplina es del catálogo por edición (`RN-E01`). La CATEGORÍA
        también: es del mismo catálogo y es la que discrimina el cuadro.
        """
        self._validar_disciplina(edicion, data.disciplina_id)
        self._validar_categoria(edicion, data.categoria_id)
        self._validar_identidad(
            edicion_id=edicion.id,
            disciplina_id=data.disciplina_id,
            categoria_id=data.categoria_id,
            nombre=data.nombre,
        )
        competencia = Competencia(
            edicion=edicion,
            disciplina_id=data.disciplina_id,
            categoria_id=data.categoria_id,
            nombre=data.nombre.strip(),
            estado=EstadoCompetencia.PLANIFICADA,
            fecha=data.fecha,
        )
        return self.persistir_nuevo(competencia)

    # ── validaciones ───────────────────────────────────────────────────────

    @staticmethod
    def _validar_disciplina(edicion, disciplina_id) -> None:
        """La disciplina existe y es de la MISMA edición que la competencia."""
        disciplina = MODELO_DISCIPLINA.objects.filter(id=disciplina_id).first()
        if disciplina is None:
            raise DisciplinaNoEncontradaError()
        if str(disciplina.edicion_id) != str(edicion.id):
            raise DisciplinaNoEncontradaError()

    @staticmethod
    def _validar_categoria(edicion, categoria_id) -> None:
        """La categoría existe y es de la MISMA edición que la competencia.

        La CATEGORÍA es un hecho del DUEÑO (`modules.salesianos_fest`): este
        módulo sólo la REFERENCIA. Una categoría de otra edición NO sirve:
        el cuadro es de UNA edición (`RN-E01`).
        """
        categoria = MODELO_CATEGORIA.objects.filter(id=categoria_id).first()
        if categoria is None:
            raise CategoriaNoEncontradaError()
        if str(categoria.edicion_id) != str(edicion.id):
            raise CategoriaNoEncontradaError()

    @staticmethod
    def _validar_identidad(
        *,
        edicion_id,
        disciplina_id,
        categoria_id,
        nombre,
        excluir_id=None,
    ) -> None:
        """No hay dos competencias con la misma identidad en el alcance."""
        consulta = Competencia.objects.filter(
            edicion_id=edicion_id,
            disciplina_id=disciplina_id,
            categoria_id=categoria_id,
            nombre__iexact=nombre.strip(),
        )
        if excluir_id is not None:
            consulta = consulta.exclude(id=excluir_id)
        if consulta.exists():
            raise CompetenciaDuplicadaError()


class CompetenciaEquipoCoreService(BaseCoreService):
    """Operaciones sync sobre `CompetenciaEquipo` — la participación en el cuadro."""

    def incorporar(
        self,
        competencia: Competencia,
        data: EquipoCompetenciaCreateData,
        *,
        elegible: bool,
        motivo_no_elegibilidad: str | None = None,
    ) -> CompetenciaEquipo:
        """Incorpora un equipo al cuadro con su semilla MANUAL.

        La ELEGIBILIDAD no se decide aquí: la resuelve el dueño de la
        inscripción y este módulo la CONSUME por el puerto
        (`RN-K01`). El servicio recibe el veredicto.
        """
        self.exigir_no_terminal(competencia, ESTADOS_TERMINALES_COMPETENCIA)
        if not elegible:
            raise EquipoNoElegibleError(motivo_no_elegibilidad or "NO_ELEGIBLE")
        self._validar_orden(competencia, data.orden)
        if CompetenciaEquipo.objects.filter(
            competencia=competencia,
            equipo_id=data.equipo_id,
        ).exists():
            raise CompetenciaEquipoDuplicadoError()

        participacion = CompetenciaEquipo(
            competencia=competencia,
            equipo_id=data.equipo_id,
            orden=data.orden,
            estado=EstadoCompetenciaEquipo.ACTIVO,
        )
        return self.persistir_nuevo(participacion)

    def editar(
        self,
        participacion: CompetenciaEquipo,
        data: EquipoCompetenciaEditData,
        *,
        expected_version: int | None,
        motivo: str | None,
    ) -> CompetenciaEquipo:
        """Edita la semilla o el estado de la participación.

        Retirar NO es borrar: la participación conserva su historia y el
        cuadro conserva su posición en la historia (`RN-K02`).
        """
        cambios = data.model_dump(exclude_none=True)
        if not cambios:
            return participacion
        ya_aplicado = all(
            getattr(participacion, campo) == valor for campo, valor in cambios.items()
        )
        self.aplicar_cas(participacion, expected_version, ya_aplicado)
        if ya_aplicado:
            return participacion

        if "orden" in cambios or "estado" in cambios:
            # Mover la semilla y retirar a un equipo son decisiones MANUALES y
            # AUDITADAS del administrador: exigen motivo (`RN-K02`).
            self.exigir_motivo(motivo)
        if "orden" in cambios:
            self._validar_orden(
                participacion.competencia,
                cambios["orden"],
                excluir_id=participacion.id,
            )
        if "estado" in cambios:
            self._validar_estado(participacion, cambios["estado"])

        for campo, valor in cambios.items():
            setattr(participacion, campo, valor)
        return self.persistir_cambio(participacion)

    # ── validaciones ───────────────────────────────────────────────────────

    @staticmethod
    def _validar_orden(competencia, orden: int, *, excluir_id=None) -> None:
        """El orden está en rango y libre entre las entradas ACTIVAS."""
        if orden < MINIMO_ORDEN or orden > MAXIMO_ORDEN:
            raise OrdenDuplicadoError()
        consulta = CompetenciaEquipo.objects.filter(
            competencia=competencia,
            orden=orden,
            estado=EstadoCompetenciaEquipo.ACTIVO,
        )
        if excluir_id is not None:
            consulta = consulta.exclude(id=excluir_id)
        if consulta.exists():
            raise OrdenDuplicadoError()

    @staticmethod
    def _validar_estado(participacion: CompetenciaEquipo, nuevo_estado: str) -> None:
        """El estado nuevo es uno de los dos del vocabulario."""
        if nuevo_estado not in (
            EstadoCompetenciaEquipo.ACTIVO,
            EstadoCompetenciaEquipo.RETIRADO,
        ):
            raise TransicionInvalidaError()


class RondaCoreService(BaseCoreService):
    """Operaciones sync sobre `Ronda` — las columnas del cuadro."""

    def crear(self, competencia: Competencia, data: RondaCreateData) -> Ronda:
        """Crea la ronda con su etiqueta y su orden, únicos en el cuadro."""
        self.exigir_no_terminal(competencia, ESTADOS_TERMINALES_COMPETENCIA)
        self._validar_unicidad(
            competencia=competencia,
            etiqueta=data.etiqueta,
            orden=data.orden,
        )
        ronda = Ronda(
            competencia=competencia,
            etiqueta=data.etiqueta.strip(),
            orden=data.orden,
            estado=EstadoRonda.ACTIVA,
        )
        return self.persistir_nuevo(ronda)

    # ── validaciones ───────────────────────────────────────────────────────

    @staticmethod
    def _validar_unicidad(*, competencia, etiqueta: str, orden: int) -> None:
        """La etiqueta y el orden son únicos dentro de la competencia."""
        if orden < MINIMO_ORDEN or orden > MAXIMO_ORDEN:
            raise RondaDuplicadaError()
        existe = Ronda.objects.filter(
            competencia=competencia,
            etiqueta__iexact=etiqueta.strip(),
        )
        if existe.exists():
            raise RondaDuplicadaError()
        if Ronda.objects.filter(competencia=competencia, orden=orden).exists():
            raise RondaDuplicadaError()


__all__ = [
    "ESTADOS_TERMINALES_COMPETENCIA",
    "MODELO_CATEGORIA",
    "MODELO_DISCIPLINA",
    "CompetenciaCoreService",
    "CompetenciaEquipoCoreService",
    "RondaCoreService",
]
