"""
Fixtures of the competencias module.

The fixture library is self-contained: it builds the catalog it needs
(event, discipline, category, package, enrollment and team) so the tests of
the bracket do not depend on the scenario fixtures of other modules.
"""
from datetime import date

import pytest

from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.constants import (
    EstadoEquipoChoices,
    EstadoInscripcionChoices,
    ModalidadChoices,
    ModoDisciplinasChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.models import (
    Categoria,
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    Promocion,
)
from modules.usuarios.domain.constants import (
    GeneroChoices,
    TipoDocumentoChoices,
)
from modules.usuarios.domain.models.persona import Persona
from modules.usuarios.domain.models.usuario import Usuario

from modules.competencias.domain.models import (
    Competencia,
    CompetenciaEquipo,
    Encuentro,
    Ronda,
)
from modules.competencias.domain.services.core.avance_service import (
    AvanceCoreService,
)
from modules.competencias.domain.services.core.competencia_equipo_service import (
    CompetenciaEquipoCoreService,
)
from modules.competencias.domain.services.core.competencia_service import (
    CompetenciaCoreService,
)
from modules.competencias.domain.services.core.correccion_service import (
    CorreccionCoreService,
)
from modules.competencias.domain.services.core.encuentro_service import (
    EncuentroCoreService,
)
from modules.competencias.domain.services.core.programacion_service import (
    ProgramacionCoreService,
)
from modules.competencias.domain.services.core.resultado_service import (
    ResultadoCoreService,
)
from modules.competencias.domain.services.core.ronda_service import RondaCoreService
from modules.competencias.domain.services.orchestrators.avance_orchestrator import (
    AvanceOrchestrator,
)
from modules.competencias.domain.services.orchestrators.competencia_equipo_orchestrator import (  # noqa: E501
    CompetenciaEquipoOrchestrator,
)
from modules.competencias.domain.services.orchestrators.competencia_orchestrator import (
    CompetenciaOrchestrator,
)
from modules.competencias.domain.services.orchestrators.correccion_orchestrator import (
    CorreccionOrchestrator,
)
from modules.competencias.domain.services.orchestrators.encuentro_orchestrator import (
    EncuentroOrchestrator,
)
from modules.competencias.domain.services.orchestrators.resultado_orchestrator import (
    ResultadoOrchestrator,
)
from modules.competencias.domain.services.orchestrators.ronda_orchestrator import (
    RondaOrchestrator,
)

FECHA_EVENTO_INICIO = date(2026, 11, 15)
FECHA_EVENTO_FIN = date(2026, 11, 20)


@pytest.fixture
def evento_competencia(db):
    """Event of the competition."""
    return Evento.objects.create(
        nombre="Salesianos FEST Test 2026",
        fecha_inicio=FECHA_EVENTO_INICIO,
        fecha_fin=FECHA_EVENTO_FIN,
        esta_activo=True,
    )


@pytest.fixture
def disciplina_competencia(db):
    """Discipline of the competition."""
    return Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def disciplina_competencia_2(db):
    """Second discipline — used to prove the identity of a competition."""
    return Disciplina.objects.create(
        nombre="Vóley Mixto",
        sigla="VOL",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=6,
        max_jugadores=8,
        esta_activa=True,
    )


@pytest.fixture
def promocion_competencia(db):
    """Promotion of the enrollment."""
    return Promocion.objects.create(
        anio=2012,
        nombre="Junior",
        activa=True,
    )


@pytest.fixture
def categoria_competencia(db, evento_competencia, promocion_competencia):
    """Category of the competition."""
    return Categoria.objects.create(
        evento=evento_competencia,
        nombre="Sub-14",
        promocion_desde=2012,
        promocion_hasta=2013,
        esta_activa=True,
    )


@pytest.fixture
def persona_competencia(db):
    """Responsible of the enrollment."""
    return Persona.objects.create(
        nombres="Responsable",
        apellidos="Competencias",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="45678912",
        genero=GeneroChoices.MASCULINO,
    )


@pytest.fixture
def persona_competencia_2(db):
    """Second responsible — the enrollment domain forbids two enrollments of
    the same event + responsible + package."""
    return Persona.objects.create(
        nombres="Responsable",
        apellidos="Competencias II",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="45678913",
        genero=GeneroChoices.MASCULINO,
    )


@pytest.fixture
def persona_competencia_3(db):
    """Third responsible — the enrollment domain forbids two enrollments of
    the same event + responsible + package."""
    return Persona.objects.create(
        nombres="Responsable",
        apellidos="Competencias III",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="45678914",
        genero=GeneroChoices.MASCULINO,
    )


@pytest.fixture
def usuario_admin_competencias(db, persona_competencia):
    """Administrator used as the actor of the audit trail."""
    return Usuario.objects.create_user(
        username="admin.competencias",
        password="test-password-123",
        persona_fk=persona_competencia,
        email="admin.competencias@example.test",
    )


# ── Actores of the HTTP surface (Phase 3) ───────────────────────────────────


@pytest.fixture
def persona_competencia_admin(db):
    """Persona of the administrator of the HTTP surface.

    `Usuario.persona_fk` is a OneToOne: every user needs its own persona.
    """
    return Persona.objects.create(
        nombres="Admin",
        apellidos="Competencias HTTP",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="45678999",
        genero=GeneroChoices.MASCULINO,
    )


@pytest.fixture
def usuario_admin_staff_competencias(db, persona_competencia_admin):
    """Administrator of the HTTP surface (`is_staff`)."""
    usuario = Usuario.objects.create_user(
        username="admin.staff.competencias",
        password="test-password-123",
        persona_fk=persona_competencia_admin,
        email="admin.staff.competencias@example.test",
    )
    usuario.is_staff = True
    usuario.save(update_fields=["is_staff"])
    return usuario


@pytest.fixture
def usuario_no_admin_competencias(db, persona_competencia_admin):
    """Authenticated user that is NOT an administrator."""
    return Usuario.objects.create_user(
        username="usuario.competencias",
        password="test-password-123",
        persona_fk=persona_competencia_admin,
        email="usuario.competencias@example.test",
    )


@pytest.fixture
def paquete_competencia(db, evento_competencia):
    """Commercial package of the enrollment."""
    return Paquete.objects.create(
        evento=evento_competencia,
        nombre="Pack Competencias",
        descripcion="Paquete de pruebas del módulo de competencias",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )


@pytest.fixture
def inscripcion_competencia(
    db,
    evento_competencia,
    persona_competencia,
    paquete_competencia,
    promocion_competencia,
):
    """Enrollment that owns the teams."""
    return _crear_inscripcion(
        evento_competencia,
        persona_competencia,
        paquete_competencia,
        promocion_competencia,
    )


def _crear_inscripcion(evento, responsable, paquete, promocion):
    """Create an enrollment (a team needs its own enrollment: the enrollment
    domain forbids two active teams of the same discipline)."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=responsable,
        paquete=paquete,
        promocion=promocion,
        estado=EstadoInscripcionChoices.CONFIRMADA,
    )


@pytest.fixture
def equipo_competencia(
    db,
    inscripcion_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """First team of the bracket."""
    return Equipo.objects.create(
        inscripcion=inscripcion_competencia,
        disciplina=disciplina_competencia,
        categoria=categoria_competencia,
        nombre="Equipo Alfa",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )


@pytest.fixture
def equipo_competencia_2(
    db,
    evento_competencia,
    persona_competencia_2,
    paquete_competencia,
    promocion_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """Second team of the bracket — with its own enrollment."""
    inscripcion = _crear_inscripcion(
        evento_competencia,
        persona_competencia_2,
        paquete_competencia,
        promocion_competencia,
    )

    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_competencia,
        categoria=categoria_competencia,
        nombre="Equipo Beta",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )


@pytest.fixture
def competencia(
    db,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """Competition of the bracket."""
    return Competencia.objects.create(
        evento=evento_competencia,
        disciplina=disciplina_competencia,
        categoria=categoria_competencia,
        nombre="Eliminatoria F7",
        fecha=date(2026, 11, 16),
        estado="PLANIFICADA",
    )


@pytest.fixture
def ronda(db, competencia):
    """First round of the bracket."""
    return Ronda.objects.create(
        competencia=competencia,
        etiqueta="Cuartos de final",
        orden=1,
        estado="ACTIVA",
    )


@pytest.fixture
def ronda_2(db, competencia):
    """Second round of the bracket — the destination of the links."""
    return Ronda.objects.create(
        competencia=competencia,
        etiqueta="Semifinal",
        orden=2,
        estado="ACTIVA",
    )


@pytest.fixture
def ronda_3(db, competencia):
    """Third round of the bracket — the descendant of a descendant."""
    return Ronda.objects.create(
        competencia=competencia,
        etiqueta="Final",
        orden=3,
        estado="ACTIVA",
    )


@pytest.fixture
def competencia_equipo(db, competencia, equipo_competencia):
    """First entry of the bracket."""
    return CompetenciaEquipo.objects.create(
        competencia=competencia,
        equipo=equipo_competencia,
        orden=1,
        estado="ACTIVO",
    )


@pytest.fixture
def encuentro(db, ronda, competencia_equipo):
    """First encounter of the bracket — only one participant so far."""
    return Encuentro.objects.create(
        ronda=ronda,
        orden=1,
        participante_1=competencia_equipo,
        participante_2=None,
        estado="BORRADOR",
    )


# ── Teams that CANNOT compete in the bracket ─────────────────────────────────


@pytest.fixture
def equipo_competencia_cancelado(
    db,
    evento_competencia,
    persona_competencia_3,
    paquete_competencia,
    promocion_competencia,
    disciplina_competencia,
    categoria_competencia,
):
    """Team of the right event/discipline/category but NOT active."""
    inscripcion = _crear_inscripcion(
        evento_competencia,
        persona_competencia_3,
        paquete_competencia,
        promocion_competencia,
    )
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_competencia,
        categoria=categoria_competencia,
        nombre="Equipo Cancelado",
        estado=EstadoEquipoChoices.EQUIPO_CANCELADO,
    )


@pytest.fixture
def equipo_competencia_disciplina_ajena(
    db,
    evento_competencia,
    persona_competencia_2,
    paquete_competencia,
    promocion_competencia,
    disciplina_competencia_2,
    categoria_competencia,
):
    """Active team of the same event but of ANOTHER discipline."""
    inscripcion = _crear_inscripcion(
        evento_competencia,
        persona_competencia_2,
        paquete_competencia,
        promocion_competencia,
    )
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_competencia_2,
        categoria=categoria_competencia,
        nombre="Equipo Otra Disciplina",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )


@pytest.fixture
def evento_competencia_2(db):
    """Second event — used to prove the event scope of the eligibility."""
    return Evento.objects.create(
        nombre="Salesianos FEST Test 2026 (otro evento)",
        fecha_inicio=FECHA_EVENTO_INICIO,
        fecha_fin=FECHA_EVENTO_FIN,
        esta_activo=True,
    )


@pytest.fixture
def categoria_competencia_ajena(db, evento_competencia):
    """Category of the SAME event but different from the one of the bracket."""
    return Categoria.objects.create(
        evento=evento_competencia,
        nombre="Sub-16",
        promocion_desde=2013,
        promocion_hasta=2014,
        esta_activa=True,
    )


@pytest.fixture
def equipo_competencia_evento_ajeno(
    db,
    evento_competencia_2,
    disciplina_competencia,
    categoria_competencia,
    promocion_competencia,
):
    """Active team of the right discipline/category but of ANOTHER event.

    Only the event of the enrollment differs: the rule of the eligibility
    that compares the event of the enrollment is proved in isolation.
    """
    persona = Persona.objects.create(
        nombres="Responsable",
        apellidos="Equipo Otro Evento",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="45790001",
        genero=GeneroChoices.MASCULINO,
    )
    paquete = Paquete.objects.create(
        evento=evento_competencia_2,
        nombre="Pack Otro Evento",
        descripcion="Paquete de pruebas de otro evento",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )
    inscripcion = _crear_inscripcion(
        evento_competencia_2,
        persona,
        paquete,
        promocion_competencia,
    )
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_competencia,
        categoria=categoria_competencia,
        nombre="Equipo Otro Evento",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )


@pytest.fixture
def equipo_competencia_categoria_ajena(
    db,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia_ajena,
    paquete_competencia,
    promocion_competencia,
):
    """Active team of the right event/discipline but of ANOTHER category."""
    persona = Persona.objects.create(
        nombres="Responsable",
        apellidos="Equipo Otra Categoria",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="45790002",
        genero=GeneroChoices.MASCULINO,
    )
    inscripcion = _crear_inscripcion(
        evento_competencia,
        persona,
        paquete_competencia,
        promocion_competencia,
    )
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_competencia,
        categoria=categoria_competencia_ajena,
        nombre="Equipo Otra Categoria",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )


# ── Builder of many eligible teams ───────────────────────────────────────────


@pytest.fixture
def crear_equipos_competencia(
    db,
    evento_competencia,
    disciplina_competencia,
    categoria_competencia,
    paquete_competencia,
    promocion_competencia,
):
    """Return a builder of N eligible teams of the bracket.

    Every team needs its own enrollment: the enrollment domain forbids two
    active teams of the same discipline inside the same enrollment.
    """
    contador = {"valor": 0}

    def _crear(cantidad: int, prefijo: str = "Equipo"):
        equipos = []
        for _ in range(cantidad):
            indice = contador["valor"]
            contador["valor"] += 1
            persona = Persona.objects.create(
                nombres="Responsable",
                apellidos=f"Bracket {prefijo} {indice}",
                tipo_documento=TipoDocumentoChoices.DNI,
                numero_documento=f"{45700000 + indice:08d}",
                genero=GeneroChoices.MASCULINO,
            )
            inscripcion = _crear_inscripcion(
                evento_competencia,
                persona,
                paquete_competencia,
                promocion_competencia,
            )
            equipos.append(
                Equipo.objects.create(
                    inscripcion=inscripcion,
                    disciplina=disciplina_competencia,
                    categoria=categoria_competencia,
                    nombre=f"{prefijo} {indice + 1}",
                    estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
                )
            )
        return equipos

    return _crear


# ── A second competition of the same event/discipline/category ───────────────


@pytest.fixture
def competencia_2(db, evento_competencia, disciplina_competencia, categoria_competencia):
    """Second competition of the same scope and the same day.

    It is used to prove that the overlap check is portable: a physical team
    cannot play two matches at the same time even in two brackets.
    """
    return Competencia.objects.create(
        evento=evento_competencia,
        disciplina=disciplina_competencia,
        categoria=categoria_competencia,
        nombre="Eliminatoria F7 B",
        fecha=date(2026, 11, 16),
        estado="PLANIFICADA",
    )


# ── An edition OUTSIDE of the authorized scope (Phase 3) ────────────────────


@pytest.fixture
def evento_competencia_inactivo(db):
    """Edition that is NOT active: it is outside of the public scope."""
    return Evento.objects.create(
        nombre="Salesianos FEST Test 2025 (cerrado)",
        fecha_inicio=date(2025, 11, 15),
        fecha_fin=date(2025, 11, 20),
        esta_activo=False,
    )


@pytest.fixture
def categoria_competencia_inactiva(
    db,
    evento_competencia_inactivo,
    promocion_competencia,
):
    """Category of the edition that is not active."""
    return Categoria.objects.create(
        evento=evento_competencia_inactivo,
        nombre="Sub-14",
        promocion_desde=2012,
        promocion_hasta=2013,
        esta_activa=True,
    )


@pytest.fixture
def competencia_fuera_de_alcance(
    db,
    evento_competencia_inactivo,
    disciplina_competencia,
    categoria_competencia_inactiva,
):
    """Competition of an edition the public reader is NOT authorized for."""
    return Competencia.objects.create(
        evento=evento_competencia_inactivo,
        disciplina=disciplina_competencia,
        categoria=categoria_competencia_inactiva,
        nombre="Eliminatoria F7 2025",
        fecha=date(2025, 11, 16),
        estado="PLANIFICADA",
    )


# ── HTTP clients of the API (Phase 3) ───────────────────────────────────────


class ClienteApiCompetencias:
    """Thin wrapper of the `TestAsyncClient` that injects the auth headers.

    `ninja_extra.testing.TestAsyncClient.request` OVERRIDES the request of
    the base client and it does NOT merge the headers of the instance with
    the ones of the call: the `Authorization` header must travel in EVERY
    call. The wrapper does it once, so the tests read as plain HTTP calls.
    """

    def __init__(self, client, cabeceras: dict | None = None):
        self._client = client
        self._cabeceras = dict(cabeceras or {})

    async def get(self, path, **kwargs):
        """GET a route of the API."""
        return await self._client.get(path, **self._params(kwargs))

    async def post(self, path, **kwargs):
        """POST a route of the API."""
        return await self._client.post(path, **self._params(kwargs))

    async def patch(self, path, **kwargs):
        """PATCH a route of the API."""
        return await self._client.patch(path, **self._params(kwargs))

    async def delete(self, path, **kwargs):
        """DELETE a route of the API."""
        return await self._client.delete(path, **self._params(kwargs))

    def _params(self, kwargs: dict) -> dict:
        """Merge the headers of the client with the ones of the call."""
        params = dict(kwargs)
        cabeceras = dict(self._cabeceras)
        cabeceras.update(params.pop("headers", None) or {})
        params["headers"] = cabeceras
        return params


@pytest.fixture
def cliente_api_competencias(db):
    """`TestAsyncClient` of the API — the public surface (no authentication).

    The controllers are ASYNC, so the client is the async one of
    `ninja_extra` (`contract/django-app-architecture-contract.md` §2.1).
    """
    from ninja_extra.testing import TestAsyncClient

    from config.api import api

    return ClienteApiCompetencias(TestAsyncClient(api))


@pytest.fixture
def cliente_admin_competencias(
    cliente_api_competencias,
    usuario_admin_staff_competencias,
):
    """`TestAsyncClient` authenticated as an administrator."""
    from ninja_jwt.tokens import AccessToken

    token = AccessToken.for_user(usuario_admin_staff_competencias)
    cliente_api_competencias._cabeceras["Authorization"] = f"Bearer {token}"
    return cliente_api_competencias


@pytest.fixture
def cliente_no_admin_competencias(
    cliente_api_competencias,
    usuario_no_admin_competencias,
):
    """`TestAsyncClient` authenticated as a NON administrator."""
    from ninja_jwt.tokens import AccessToken

    token = AccessToken.for_user(usuario_no_admin_competencias)
    cliente_api_competencias._cabeceras["Authorization"] = f"Bearer {token}"
    return cliente_api_competencias


# ── Orchestrators (public async façade of the commands) ──────────────────────

@pytest.fixture
def orquestador_competencias():
    """Orchestrator of the commands of the competition."""
    return CompetenciaOrchestrator(CompetenciaCoreService())


@pytest.fixture
def orquestador_competencia_equipos():
    """Orchestrator of the commands of the teams of the bracket."""
    return CompetenciaEquipoOrchestrator(
        CompetenciaEquipoCoreService(),
        CompetenciaCoreService(),
    )


@pytest.fixture
def orquestador_rondas():
    """Orchestrator of the commands of the rounds."""
    return RondaOrchestrator(RondaCoreService(), CompetenciaCoreService())


@pytest.fixture
def orquestador_encuentros():
    """Orchestrator of the commands of the encounters."""
    return EncuentroOrchestrator(
        EncuentroCoreService(),
        RondaCoreService(),
        ProgramacionCoreService(),
    )


@pytest.fixture
def orquestador_resultados():
    """Orchestrator of the result of the encounters."""
    return ResultadoOrchestrator(
        ResultadoCoreService(),
        EncuentroCoreService(),
        ProgramacionCoreService(),
    )


@pytest.fixture
def orquestador_avances():
    """Orchestrator of the advance (propagation of the winner)."""
    return AvanceOrchestrator(
        AvanceCoreService(),
        EncuentroCoreService(),
        ProgramacionCoreService(),
    )


@pytest.fixture
def orquestador_correcciones():
    """Orchestrator of the correction of the winner."""
    return CorreccionOrchestrator(
        CorreccionCoreService(),
        EncuentroCoreService(),
        ProgramacionCoreService(),
    )
