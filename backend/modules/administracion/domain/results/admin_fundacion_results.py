"""
AdminFundacionResult — internal DTO of the foundation probe.

The presenters transform result objects into HTTP schemas; they never touch
the ORM (`contract/api-wrapper-presenter-contract.md` §3). This DTO is the
hand-off between the orchestrator and the presenter.
"""

from pydantic import BaseModel


class AdminFundacionResult(BaseModel):
    """Result of the administration foundation probe."""

    modulo: str
    estado: str
    evento_activo_id: str | None = None
    evento_activo_nombre: str | None = None


__all__ = ["AdminFundacionResult"]
