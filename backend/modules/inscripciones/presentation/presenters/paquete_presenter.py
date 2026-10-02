"""PaquetePresenter — transforms Paquete ORM to HTTP PaqueteOut/Detalle.

Encapsulates the business rule that derives `cantidad_maxima_equipos`
from the package's `modo_disciplinas` and its current `paquete_disciplinas` /
`cantidad_disciplinas_requeridas`. This is the single source of truth so
that backend validation and frontend wizard agree on how many teams a
package can produce.
"""
from modules.inscripciones.domain.models import Paquete, PaqueteDisciplina
from modules.inscripciones.domain.constants import ModoDisciplinasPaqueteChoices
from modules.inscripciones.presentation.schemas.paquete_schemas import (
    PaqueteOut,
    PaqueteDisciplinaOut,
)


def calcular_cantidad_maxima_equipos(paquete: Paquete) -> int:
    """Return how many equipos a package allows.

    - FIJO: One team per disciplina already linked to the package. The
      frontend MUST create exactly `len(paquete.paquete_disciplinas)` teams
      and MUST NOT add manual controls.
    - ELEGIBLE: One team per disciplina the user selects up to
      `cantidad_disciplinas_requeridas`.
    """
    if paquete.modo_disciplinas == ModoDisciplinasPaqueteChoices.FIJO:
        return PaqueteDisciplina.objects.filter(paquete=paquete).count()
    # ELEGIBLE (default)
    return paquete.cantidad_disciplinas_requeridas or 1


def present_paquete_disciplina(paquete_disciplina: PaqueteDisciplina) -> PaqueteDisciplinaOut:
    """Return discipline metadata embedded in a package response as a typed schema."""
    disciplina = paquete_disciplina.disciplina
    return PaqueteDisciplinaOut(
        disciplina_id=str(disciplina.id),
        disciplina_nombre=disciplina.nombre,
        disciplina_sigla=disciplina.sigla,
        min_jugadores=disciplina.min_jugadores,
        max_jugadores=disciplina.max_jugadores,
    )


def present_paquete(paquete: Paquete) -> PaqueteOut:
    """Return a PaqueteOut schema instance, including the derived
    `cantidad_maxima_equipos` for the frontend wizard."""
    return PaqueteOut(
        id=str(paquete.id),
        nombre=paquete.nombre,
        descripcion=paquete.descripcion,
        cantidad_maxima_participantes=paquete.cantidad_maxima_participantes,
        precio_regular=float(paquete.precio_regular),
        precio_promocional=float(paquete.precio_promocional) if paquete.precio_promocional else None,
        valido_desde=paquete.valido_desde,
        valido_hasta=paquete.valido_hasta,
        esta_activo=paquete.esta_activo,
        modo_disciplinas=paquete.modo_disciplinas,
        cantidad_disciplinas_requeridas=paquete.cantidad_disciplinas_requeridas,
        cantidad_maxima_equipos=calcular_cantidad_maxima_equipos(paquete),
        disciplinas=[
            present_paquete_disciplina(pd)
            for pd in paquete.paquete_disciplinas.all()
        ],
    )
