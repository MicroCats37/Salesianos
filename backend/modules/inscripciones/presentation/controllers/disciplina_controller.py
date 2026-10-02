"""DisciplinaController — catalog endpoints for disciplinas."""

from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny
from injector import inject

from core.responses import ApiResponse, success_response
from modules.inscripciones.presentation.schemas.disciplina_schemas import DisciplinaOut, CategoriaOut
from modules.inscripciones.domain.services.core.disciplina_service import DisciplinaService
from modules.inscripciones.domain.selectors.inscripcion_selector import InscripcionSelector


@api_controller("/inscripciones/disciplinas", tags=["Catálogos"], permissions=[AllowAny])
class DisciplinaController:
    """
    Controlador para listar disciplinas y categorías disponibles.

    Endpoints públicos de solo lectura.

    Rutas:
      GET /inscripciones/disciplinas/                         -> listar_disciplinas
      GET /inscripciones/disciplinas/{disciplina_id}/categorias -> listar_categorias
    """

    @inject
    def __init__(self, disciplina_svc: DisciplinaService, selector: InscripcionSelector):
        self.disciplina_svc = disciplina_svc
        self.selector = selector

    @route.get("/", response={200: ApiResponse[list[DisciplinaOut]]}, auth=None)
    def listar_disciplinas(self):
        """
        Listar todas las disciplinas activas.

        Route: GET /api/inscripciones/disciplinas/
        Auth: public (no JWT).
        Returns: lista de disciplinas disponibles para inscripción.
        """
        disciplinas = self.disciplina_svc.listar_activas()
        data = [
            DisciplinaOut(
                id=str(d.id),
                nombre=d.nombre,
                sigla=d.sigla,
                modalidad=d.modalidad,
                min_jugadores=d.min_jugadores,
                max_jugadores=d.max_jugadores,
                esta_activa=d.esta_activa,
            )
            for d in disciplinas
        ]
        return success_response(data)

    @route.get("/{disciplina_id}/categorias", response={200: ApiResponse[list[CategoriaOut]]}, auth=None)
    def listar_categorias(self, disciplina_id: str):
        """
        Listar categorías activas de una disciplina.

        Route: GET /api/inscripciones/disciplinas/{disciplina_id}/categorias
        Auth: public (no JWT).
        Returns: lista de categorías (Junior, Senior, etc.) disponibles para la disciplina.
        """
        categorias = self.disciplina_svc.listar_categorias_por_disciplina(disciplina_id)
        data = [
            CategoriaOut(
                id=str(c.id),
                disciplina_id=str(c.disciplina_id),
                nombre=c.nombre,
                anio_minimo=c.anio_minimo,
                anio_maximo=c.anio_maximo,
                esta_activa=c.esta_activa,
            )
            for c in categorias
        ]
        return success_response(data)
