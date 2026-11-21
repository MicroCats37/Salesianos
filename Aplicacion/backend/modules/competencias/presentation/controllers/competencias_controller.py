"""`CompetenciasController` — la superficie HTTP del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.8 ·
          `contract/api-wrapper-presenter-contract.md` §8

Controller DELGADO: hidrata la entrada, llama al orquestador y devuelve el
éxito formateado por EL PRESENTER OPERATIVO ÚNICO. Cero `if` de negocio,
cero ORM, cero respuestas de error manuales: los errores los construye el
catálogo global `core/exceptions.py` a partir del código estable de la
excepción de dominio.

**Rutas (16).** La lista y la agenda son de alcance de EDICIÓN (la resuelve
el servidor); el resto cuelga de una competencia, que es su alcance
(`RN-E01`).

| Ruta | Método | Permiso |
|---|---|---|
| `/competencias` | GET | lectura del área |
| `/competencias/agenda` | GET | lectura del área |
| `/competencias/{id}` | GET | lectura del área |
| `/competencias/{id}/cuadro` | GET | lectura del área |
| `/competencias/{id}/equipos-elegibles` | GET | lectura del área |
| `/competencias` | POST | escribir competencias |
| `/competencias/{id}/equipos` | POST | escribir competencias |
| `/competencias/{id}/equipos/{participacion_id}` | PATCH | escribir competencias |
| `/competencias/{id}/rondas` | POST | escribir competencias |
| `/competencias/{id}/encuentros` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}` | PATCH | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/resultado` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/avance/preview` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/avance` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/correccion/preview` | POST | escribir competencias |
| `/competencias/{id}/encuentros/{encuentro_id}/correccion` | POST | escribir competencias |

**Las dos rutas `preview` NO ESCRIBEN NADA** (`QA-K03`, `QA-K04`): son
simulaciones del efecto de la operación.

**Los mensajes de éxito son FIJOS**: no interpolan identificadores, UUIDs ni
montos. La consecuencia concreta de cada acción viaja en los DATOS
(`total_afectados`, `ocupante_actual_equipo_id`, `acciones`), que es lo que
`RN-A02` pide exponer.

**NOTA DE REGISTRO:** una ruta no existe hasta que su controller está
registrado en `config/api.py`. Ese registro es de A0 y este paquete NO edita
`config/api.py`: lo pide como evidencia.
"""

from datetime import date

from asgiref.sync import sync_to_async
from injector import inject
from ninja_extra import api_controller, route

from core.permissions import (
    RequireAdminVer,
    RequireCompetenciasEscribir,
)
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.competencias.domain.schemas.competencias_schemas import (
    AvanceData,
    CompetenciaCreateData,
    CorreccionData,
    EncuentroActualizarData,
    EncuentroCreateData,
    EquipoCompetenciaCreateData,
    EquipoCompetenciaEditData,
    ResultadoEncuentroData,
    RondaCreateData,
)
from modules.competencias.domain.services.orchestrators.competencias_orchestrator import (
    CompetenciasOrchestrator,
)
from modules.competencias.infrastructure.services.alcance_edicion_eventos import (
    AlcanceEdicionEventos,
)
from modules.competencias.presentation.presenters.competencias_presenter import (
    CompetenciasPresenter,
)
from modules.competencias.realtime.publisher import publicar_encuentro_actualizado
from modules.competencias.presentation.schemas.competencias_schemas import (
    AgendaOut,
    AvanceConfirmarIn,
    AvanceOut,
    AvancePreviewOut,
    CompetenciaCrearIn,
    CompetenciaDetalleOut,
    CompetenciaEquipoOut,
    CompetenciaListadoOut,
    CorreccionAplicarIn,
    CorreccionOut,
    CorreccionPrevisualizarIn,
    CorreccionPreviewOut,
    EncuentroActualizarIn,
    EncuentroCrearIn,
    EncuentroOut,
    EquipoEditarIn,
    EquipoElegibleOut,
    EquipoIncorporarIn,
    ResultadoRegistrarIn,
    ResultadoRegistradoOut,
    RondaCrearIn,
    RondaOut,
)


@api_controller("/competencias", tags=["Competencias"])
class CompetenciasController:
    """Superficie HTTP de las competencias, el cuadro y la agenda."""

    @inject
    def __init__(
        self,
        orchestrator: CompetenciasOrchestrator,
        alcance_edicion: AlcanceEdicionEventos,
    ):
        self.orchestrator = orchestrator
        self.alcance_edicion = alcance_edicion

    # ── lecturas ───────────────────────────────────────────────────────────

    @route.get(
        "",
        response={200: ApiResponse[list[CompetenciaListadoOut]]},
        summary="Lista de competencias de la edición vigente",
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
    )
    async def listar_competencias(
        self,
        request,
        disciplina_id: str | None = None,
        categoria_id: str | None = None,
        estado: str | None = None,
    ):
        """Las competencias de la edición vigente, con sus contadores.

        Route: GET /api/competencias

        La EDICIÓN la resuelve el servidor por el orden congelado
        (`FR-02` §2.2): el cliente no la elige. Los filtros de DISCIPLINA y de
        CATEGORÍA se combinan con AND.
        """
        resultados = await self.orchestrator.listar_competencias(
            disciplina_id=disciplina_id,
            categoria_id=categoria_id,
            estado=estado,
        )
        return success_response(
            [
                CompetenciasPresenter.present_listado(resultado)
                for resultado in resultados
            ]
        )

    @route.get(
        "/agenda",
        response={200: ApiResponse[AgendaOut]},
        summary="Agenda transversal del día",
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
    )
    async def obtener_agenda(self, request, fecha: date | None = None):
        """Los encuentros programados del día, en el alcance de la edición.

        Route: GET /api/competencias/agenda

        Los encuentros cancelados NO aparecen: no reservan la franja. Los
        encuentros sin horario tampoco: la agenda es el horario.
        """
        resultado = await self.orchestrator.obtener_agenda(fecha or date.today())
        return success_response(CompetenciasPresenter.present_agenda(resultado))

    @route.get(
        "/{competencia_id}",
        response={200: ApiResponse[CompetenciaDetalleOut]},
        summary="Detalle operativo de una competencia",
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
    )
    async def obtener_competencia(self, request, competencia_id: str):
        """El detalle de la competencia: equipos y cuadro.

        Route: GET /api/competencias/{competencia_id}

        Es la MISMA fuente que la agenda y el cuadro (`FL-11` paso 6).
        """
        resultado = await self.orchestrator.obtener_competencia(competencia_id)
        return success_response(CompetenciasPresenter.present_detalle(resultado))

    @route.get(
        "/{competencia_id}/cuadro",
        response={200: ApiResponse[list[RondaOut]]},
        summary="Cuadro de una competencia",
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
    )
    async def obtener_cuadro(self, request, competencia_id: str):
        """Las rondas y los encuentros del cuadro.

        Route: GET /api/competencias/{competencia_id}/cuadro
        """
        resultados = await self.orchestrator.obtener_cuadro(competencia_id)
        return success_response(CompetenciasPresenter.present_cuadro(resultados))

    @route.get(
        "/{competencia_id}/equipos-elegibles",
        response={200: ApiResponse[list[EquipoElegibleOut]]},
        summary="Equipos candidatos y su veredicto de elegibilidad",
        auth=JWTAuth(),
        permissions=[RequireAdminVer],
    )
    async def listar_equipos_elegibles(self, request, competencia_id: str):
        """Los equipos candidatos del torneo y POR QUÉ pueden o no competir.

        Route: GET /api/competencias/{competencia_id}/equipos-elegibles

        El veredicto lo produce el DUEÑO de la inscripción: este módulo
        publica su código de motivo y nunca lo adivina (`QA-K01`).
        """
        veredictos = await self.orchestrator.listar_equipos_elegibles(competencia_id)
        return success_response(
            CompetenciasPresenter.present_equipos_elegibles(veredictos)
        )

    # ── escrituras ─────────────────────────────────────────────────────────

    @route.post(
        "",
        response={201: ApiResponse[CompetenciaDetalleOut]},
        summary="Alta de una competencia",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def crear_competencia(self, request, payload: CompetenciaCrearIn):
        """Crea la competencia en la edición vigente.

        Route: POST /api/competencias

        La edición se resuelve en el servidor; el navegador no elige el
        evento ni la edición. La identidad es (edición, disciplina, categoría, nombre) y el backend
        la comprueba: dos competencias con el mismo nombre en el mismo alcance
        y la MISMA categoría no pueden existir; con categorías DISTINTAS sí.
        """
        edicion = await sync_to_async(self.alcance_edicion.resolver_actual)(
            exigir_publicada=True,
        )
        resultado = await self.orchestrator.crear_competencia(
            CompetenciaCreateData(
                edicion_id=str(edicion.id),
                disciplina_id=payload.disciplina_id,
                categoria_id=payload.categoria_id,
                nombre=payload.nombre,
                fecha=payload.fecha,
            ),
            actor=request.auth,
        )
        return success_response(
            CompetenciasPresenter.present_detalle(resultado),
            message="La competencia se registró correctamente.",
        )

    @route.post(
        "/{competencia_id}/equipos",
        response={201: ApiResponse[CompetenciaEquipoOut]},
        summary="Incorpora un equipo elegible al cuadro",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def incorporar_equipo(self, request, competencia_id: str, payload: EquipoIncorporarIn):
        """Incorpora un equipo al cuadro con su semilla manual.

        Route: POST /api/competencias/{competencia_id}/equipos

        Un equipo que NO cumple la elegibilidad es rechazado con el motivo
        del dueño de la inscripción (`QA-K01`). La semilla la elige el
        administrador: el sistema nunca.
        """
        resultado = await self.orchestrator.incorporar_equipo(
            competencia_id,
            EquipoCompetenciaCreateData(
                competencia_id=competencia_id,
                equipo_id=payload.equipo_id,
                orden=payload.orden,
            ),
            actor=request.auth,
        )
        return success_response(
            CompetenciasPresenter.present_equipo(resultado),
            message="El equipo se incorporó a la competencia.",
        )

    @route.patch(
        "/{competencia_id}/equipos/{participacion_id}",
        response={200: ApiResponse[CompetenciaEquipoOut]},
        summary="Edita la semilla o el estado de un equipo del cuadro",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def editar_equipo(
        self,
        request,
        competencia_id: str,
        participacion_id: str,
        payload: EquipoEditarIn,
    ):
        """Edita la semilla o retira al equipo del cuadro.

        Route: PATCH /api/competencias/{competencia_id}/equipos/{participacion_id}

        Retirar NO es borrar: la participación conserva su historia
        (`RN-K02`). Si la versión que el cliente conoce ya no es la actual,
        el backend responde `RESOURCE_CHANGED` y NO aplica el cambio.
        """
        resultado = await self.orchestrator.editar_equipo(
            competencia_id,
            participacion_id,
            EquipoCompetenciaEditData(
                orden=payload.orden,
                estado=payload.estado,
            ),
            expected_version=payload.expected_version,
            motivo=payload.motivo,
            actor=request.auth,
        )
        return success_response(
            CompetenciasPresenter.present_equipo(resultado),
            message="El equipo de la competencia se actualizó correctamente.",
        )

    @route.post(
        "/{competencia_id}/cuadro/generar",
        response={201: ApiResponse[CompetenciaDetalleOut]},
        summary="Genera la llave inicial de eliminación simple",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def generar_cuadro(self, request, competencia_id: str):
        """Crea rondas, encuentros, byes y enlaces desde las semillas activas."""
        resultado = await self.orchestrator.generar_cuadro(
            competencia_id,
            actor=request.auth,
        )
        return success_response(
            CompetenciasPresenter.present_detalle(resultado),
            message="El cuadro inicial se generó correctamente.",
        )

    @route.post(
        "/{competencia_id}/rondas",
        response={201: ApiResponse[RondaOut]},
        summary="Alta de una ronda del cuadro",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def crear_ronda(self, request, competencia_id: str, payload: RondaCrearIn):
        """Crea una ronda con su etiqueta y su orden.

        Route: POST /api/competencias/{competencia_id}/rondas

        La etiqueta y el orden son únicos dentro de la competencia: el cuadro
        tiene una lectura única.
        """
        resultado = await self.orchestrator.crear_ronda(
            competencia_id,
            RondaCreateData(
                competencia_id=competencia_id,
                etiqueta=payload.etiqueta,
                orden=payload.orden,
            ),
            actor=request.auth,
        )
        return success_response(
            CompetenciasPresenter.present_ronda(resultado),
            message="La ronda se registró correctamente.",
        )

    @route.post(
        "/{competencia_id}/encuentros",
        response={201: ApiResponse[EncuentroOut]},
        summary="Alta de un encuentro",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def crear_encuentro(
        self,
        request,
        competencia_id: str,
        payload: EncuentroCrearIn,
    ):
        """Crea un encuentro en la ronda, posiblemente vacío.

        Route: POST /api/competencias/{competencia_id}/encuentros

        Un encuentro sin participantes y sin horario es un borrador
        LEGÍTIMO: el cuadro puede estar vacío o parcial.
        """
        resultado = await self.orchestrator.crear_encuentro(
            competencia_id,
            payload.ronda_id,
            EncuentroCreateData(
                ronda_id=payload.ronda_id,
                orden=payload.orden,
            ),
            actor=request.auth,
        )
        return success_response(
            CompetenciasPresenter.present_encuentro(resultado),
            message="El encuentro se registró correctamente.",
        )

    @route.patch(
        "/{competencia_id}/encuentros/{encuentro_id}",
        response={200: ApiResponse[EncuentroOut]},
        summary="Edita un encuentro del cuadro",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def actualizar_encuentro(
        self,
        request,
        competencia_id: str,
        encuentro_id: str,
        payload: EncuentroActualizarIn,
    ):
        """Aplica los cambios declarados en el encuentro.

        Route: PATCH /api/competencias/{competencia_id}/encuentros/{encuentro_id}

        Un campo ausente significa "no tocar". La programación rechaza el
        solapamiento de un equipo (`RN-K03`) y NO cambia la agenda. El bye
        manual exige exactamente un equipo. La versión obsoleta se rechaza
        con `RESOURCE_CHANGED` y no se aplica nada.
        """
        cambios = payload.model_dump(exclude_unset=True)
        cambios.pop("expected_version", None)
        data = EncuentroActualizarData(**cambios)
        resultado = await self.orchestrator.actualizar_encuentro(
            competencia_id,
            encuentro_id,
            data,
            expected_version=payload.expected_version,
            actor=request.auth,
        )
        publicar_encuentro_actualizado(str(resultado.id))
        return success_response(
            CompetenciasPresenter.present_encuentro(resultado),
            message="El encuentro se actualizó correctamente.",
        )

    @route.post(
        "/{competencia_id}/encuentros/{encuentro_id}/resultado",
        response={200: ApiResponse[ResultadoRegistradoOut]},
        summary="Registra el resultado autoritativo del encuentro",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def registrar_resultado(
        self,
        request,
        competencia_id: str,
        encuentro_id: str,
        payload: ResultadoRegistrarIn,
    ):
        """Fija el ganador del encuentro y lo finaliza.

        Route: POST /api/competencias/{competencia_id}/encuentros/{encuentro_id}/resultado

        El ganador lo declara el administrador: NUNCA se deduce del
        marcador. Un reintento con el mismo resultado no escribe nada.
        """
        resultado = await self.orchestrator.registrar_resultado(
            competencia_id,
            encuentro_id,
            ResultadoEncuentroData(
                ganador_id=payload.ganador_id,
                puntaje_1=payload.puntaje_1,
                puntaje_2=payload.puntaje_2,
                marcador_detalle=payload.marcador_detalle,
                motivo=payload.motivo,
            ),
            expected_version=payload.expected_version,
            actor=request.auth,
        )
        publicar_encuentro_actualizado(str(resultado.encuentro.id))
        return success_response(
            CompetenciasPresenter.present_resultado(resultado),
            message="El resultado se registró correctamente.",
        )

    @route.post(
        "/{competencia_id}/encuentros/{encuentro_id}/avance/preview",
        response={200: ApiResponse[AvancePreviewOut]},
        summary="Vista previa del avance del ganador",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def previsualizar_avance(
        self,
        request,
        competencia_id: str,
        encuentro_id: str,
    ):
        """La simulación del avance. NO ESCRIBE NADA.

        Route: POST /api/competencias/{competencia_id}/encuentros/{encuentro_id}/avance/preview

        Informa a dónde llegaría el ganador, qué slot ocupa hoy ese destino
        y si la cascada está bloqueada (`QA-K04`).
        """
        resultado = await self.orchestrator.previsualizar_avance(
            competencia_id,
            encuentro_id,
        )
        return success_response(CompetenciasPresenter.present_avance_preview(resultado))

    @route.post(
        "/{competencia_id}/encuentros/{encuentro_id}/avance",
        response={200: ApiResponse[AvanceOut]},
        summary="Confirma el avance del ganador",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def confirmar_avance(
        self,
        request,
        competencia_id: str,
        encuentro_id: str,
        payload: AvanceConfirmarIn,
    ):
        """Coloca al ganador en el slot de destino y registra la propagación.

        Route: POST /api/competencias/{competencia_id}/encuentros/{encuentro_id}/avance

        Un destino que YA transcurrió bloquea la cascada: el backend no
        propaga en silencio.
        """
        resultado = await self.orchestrator.confirmar_avance(
            competencia_id,
            encuentro_id,
            AvanceData(motivo=payload.motivo),
            expected_version=payload.expected_version,
            actor=request.auth,
        )
        publicar_encuentro_actualizado(str(resultado.encuentro_origen_id))
        publicar_encuentro_actualizado(str(resultado.destino.id))
        return success_response(
            CompetenciasPresenter.present_avance(resultado),
            message="El avance se confirmó correctamente.",
        )

    @route.post(
        "/{competencia_id}/encuentros/{encuentro_id}/correccion/preview",
        response={200: ApiResponse[CorreccionPreviewOut]},
        summary="Vista previa del impacto de una corrección",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def previsualizar_correccion(
        self,
        request,
        competencia_id: str,
        encuentro_id: str,
        payload: CorreccionPrevisualizarIn,
    ):
        """El impacto de la corrección. NO ESCRIBE NADA.

        Route: POST /api/competencias/{competencia_id}/encuentros/{encuentro_id}/correccion/preview

        Publica cuántos encuentros posteriores cambian y si la cascada exige
        una autorización explícita (`QA-K03`).
        """
        resultado = await self.orchestrator.previsualizar_correccion(
            competencia_id,
            encuentro_id,
            payload.ganador_id,
        )
        return success_response(
            CompetenciasPresenter.present_correccion_preview(resultado)
        )

    @route.post(
        "/{competencia_id}/encuentros/{encuentro_id}/correccion",
        response={200: ApiResponse[CorreccionOut]},
        summary="Aplica la corrección del resultado",
        auth=JWTAuth(),
        permissions=[RequireCompetenciasEscribir],
    )
    async def corregir(
        self,
        request,
        competencia_id: str,
        encuentro_id: str,
        payload: CorreccionAplicarIn,
    ):
        """Corrige el ganador y propaga el cambio por la cadena.

        Route: POST /api/competencias/{competencia_id}/encuentros/{encuentro_id}/correccion

        El motivo es obligatorio. Si un descendiente ya transcurrió, la
        cascada exige `override` Y la aceptación del impacto: sin las dos
        cosas, NADA se escribe.
        """
        resultado = await self.orchestrator.corregir(
            competencia_id,
            encuentro_id,
            CorreccionData(
                ganador_id=payload.ganador_id,
                motivo=payload.motivo,
                override=payload.override,
                acepta_impacto=payload.acepta_impacto,
            ),
            expected_version=payload.expected_version,
            actor=request.auth,
        )
        publicar_encuentro_actualizado(str(resultado.encuentro.id))
        return success_response(
            CompetenciasPresenter.present_correccion(resultado),
            message="La corrección se aplicó correctamente.",
        )


__all__ = ["CompetenciasController"]
