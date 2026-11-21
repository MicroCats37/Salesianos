"""EL presenter de "MIS PARTIDOS".

Change: `partidos-marcadores-competencias` · Batch 3B

Contract: `contract/api-wrapper-presenter-contract.md` §2, §3

Es un TRANSFORMADOR PURO: recibe el resultado del dominio y devuelve el
wrapper HTTP. NO consulta la base de datos, NO decide nada y NO construye
mensajes de error.

**El encuentro de la cuenta es el MISMO que el de la superficie pública**: la
cuenta necesita los equipos, el marcador, el ganador explícito y la versión, y
ninguna de las afordancias de administración. Reutilizar el espejo evita una
TERCERA forma de encuentro que pudiera divergir de las otras dos.
"""

from modules.competencias.domain.results.competencias_results import (
    MisPartidosResult,
)
from modules.competencias.presentation.presenters.competencias_presenter import (
    CompetenciasPresenter,
)
from modules.competencias.presentation.presenters.competencias_publico_presenter import (
    CompetenciasPublicoPresenter,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    MisPartidosOut,
)


class MisPartidosPresenter:
    """La proyección de los partidos de la cuenta."""

    @staticmethod
    def present(result: MisPartidosResult) -> MisPartidosOut:
        """Proyecta los partidos de la cuenta y sus tres cubos."""
        return MisPartidosOut(
            edicion_id=result.edicion_id,
            edicion_nombre=result.edicion_nombre,
            total=result.total,
            equipos=[
                CompetenciasPresenter.present_equipo(equipo)
                for equipo in result.equipos
            ],
            en_vivo=[
                CompetenciasPublicoPresenter.present_encuentro(encuentro)
                for encuentro in result.en_vivo
            ],
            proximos=[
                CompetenciasPublicoPresenter.present_encuentro(encuentro)
                for encuentro in result.proximos
            ],
            finalizados=[
                CompetenciasPublicoPresenter.present_encuentro(encuentro)
                for encuentro in result.finalizados
            ],
        )


__all__ = ["MisPartidosPresenter"]
