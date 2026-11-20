"""Presenters del módulo `competencias`.

**UN SOLO PRESENTER OPERATIVO.** La agenda, el cuadro y el detalle del
encuentro se proyectan con `CompetenciasPresenter`: no hay un presenter por
ruta que pueda divergir del otro (`FL-11` paso 6, `frontend/05` §3).
"""

from modules.competencias.presentation.presenters.competencias_presenter import (
    CompetenciasPresenter,
)

__all__ = ["CompetenciasPresenter"]
