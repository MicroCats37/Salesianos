"""
Domain exceptions of the `modules.competencias` module.

Every exception carries a STABLE machine-readable `code`. The public message
is fixed prose: it never interpolates UUIDs, internal ids, names or raw
database text (contract/api-wrapper-presenter-contract.md §8).

The public catalog itself lives in `core/exceptions.py` and is wired by the
API phase (Phase 3); until then these classes are the ones the domain
raises and their messages are the ones the API would publish.

Codes used by this phase (the design catalog):

- 404 → COMPETENCIA_NOT_FOUND, RONDA_NOT_FOUND, ENCUENTRO_NOT_FOUND,
  COMPETENCIA_EQUIPO_NOT_FOUND
- 409 → COMPETENCIA_DUPLICADA, EQUIPO_NO_ELEGIBLE, EQUIPO_SOLAPADO,
  SLOT_OCUPADO, DESTINO_BLOQUEADO, INVALID_STATE_TRANSITION,
  DELETE_NOT_ALLOWED, RESOURCE_CHANGED
- 422 → INVALID_SCHEDULE, INVALID_LINK, INVALID_WINNER, REASON_REQUIRED
"""
from core.exceptions import ConflictError, NotFoundError, UnprocessableEntityError


# ── 404 — the resource does not exist ─────────────────────────────────────────


class CompetenciaNotFoundError(NotFoundError):
    """The competition does not exist."""

    code: str = "COMPETENCIA_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Competencia", code=self.code)


class RondaNotFoundError(NotFoundError):
    """The round does not exist."""

    code: str = "RONDA_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Ronda", code=self.code)


class EncuentroNotFoundError(NotFoundError):
    """The encounter does not exist."""

    code: str = "ENCUENTRO_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Encuentro", code=self.code)


class CompetenciaEquipoNotFoundError(NotFoundError):
    """The entry of a team inside the bracket does not exist."""

    code: str = "COMPETENCIA_EQUIPO_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Equipo de competencia", code=self.code)


# ── 409 — business conflict ───────────────────────────────────────────────────


class CompetenciaDuplicadaError(ConflictError):
    """A duplicate already exists inside the scope of the competition.

    The same code covers the identity of the competition (event + discipline
    + category + name) and the duplicates of the bracket (label/order of a
    round, order of an encounter, manual order of an active team).
    """

    code: str = "COMPETENCIA_DUPLICADA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Ya existe un elemento con esos datos en la competencia.",
            code=self.code,
        )


class EquipoNoElegibleError(ConflictError):
    """The team cannot be registered in the competition.

    The team is either not active, belongs to another event, plays another
    discipline or category, or it is already registered in the competition.
    """

    code: str = "EQUIPO_NO_ELEGIBLE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message=(
                "El equipo no cumple las condiciones para incorporarse a la "
                "competencia."
            ),
            code=self.code,
        )


class EquipoSolapadoError(ConflictError):
    """One of the teams already plays in an overlapping interval."""

    code: str = "EQUIPO_SOLAPADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El equipo ya tiene un encuentro programado en ese horario.",
            code=self.code,
        )


class InvalidStateTransitionError(ConflictError):
    """The requested transition is not allowed for the current state."""

    code: str = "INVALID_STATE_TRANSITION"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="La transición de estado no es válida para este recurso.",
            code=self.code,
        )


class DeleteNotAllowedError(ConflictError):
    """The resource is already in use and must be cancelled, not deleted."""

    code: str = "DELETE_NOT_ALLOWED"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message=(
                "El recurso ya está en uso en el cuadro y solo puede "
                "cancelarse o invalidarse."
            ),
            code=self.code,
        )


class ResourceChangedError(ConflictError):
    """The caller edited a stale version of the resource."""

    code: str = "RESOURCE_CHANGED"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message=(
                "El recurso cambió mientras lo editabas. Actualiza tus datos "
                "e inténtalo nuevamente."
            ),
            code=self.code,
        )


class SlotOcupadoError(ConflictError):
    """The slot of destination of the link already holds another team."""

    code: str = "SLOT_OCUPADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El slot de destino del encuentro ya está ocupado.",
            code=self.code,
        )


class DestinoBloqueadoError(ConflictError):
    """The linked encounter already started, finished or was cancelled.

    The same code covers the blocked propagation (the destination of the
    link cannot receive the winner anymore) and the blocked correction (a
    descendant of the link already started, finished or was cancelled and
    would need an explicit override).
    """

    code: str = "DESTINO_BLOQUEADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message=(
                "El encuentro de destino ya comenzó, finalizó o fue cancelado "
                "y no puede reescribirse sin una decisión administrativa "
                "explícita."
            ),
            code=self.code,
        )


# ── 422 — the request is well formed but its content is invalid ──────────────


class InvalidScheduleError(UnprocessableEntityError):
    """The schedule of the encounter is not a valid interval of the day."""

    code: str = "INVALID_SCHEDULE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El horario del encuentro no es válido.",
            code=self.code,
        )


class InvalidLinkError(UnprocessableEntityError):
    """The link of the encounter points to something that does not belong."""

    code: str = "INVALID_LINK"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El vínculo del encuentro no es válido.",
            code=self.code,
        )


class InvalidWinnerError(UnprocessableEntityError):
    """The winner is not valid for the current state of the encounter."""

    code: str = "INVALID_WINNER"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El ganador no es válido para este encuentro.",
            code=self.code,
        )


class ReasonRequiredError(UnprocessableEntityError):
    """The change touches a protected field and needs an audited motive."""

    code: str = "REASON_REQUIRED"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Debes indicar el motivo del cambio.",
            code=self.code,
        )
