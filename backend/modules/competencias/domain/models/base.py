"""
CompetenciaBaseModel — abstract base of the models of the module.

It adds to `core.models.BaseModel` (UUID + timestamps):

- `version`: the optimistic-locking counter used by the commands to detect
  concurrent edits (`expected_version`).
- The audit contract of the design: EVERY save carries the actor
  (`_history_user`) and the motive (`_change_reason`) that
  django-simple-history writes into the historical record.

The `save()` override only forwards the audit data — it never touches other
models and never applies business rules (those live in the service layer).
"""
from django.db import models

from core.models import BaseModel


class CompetenciaBaseModel(BaseModel):
    """Abstract base of Competencia, CompetenciaEquipo, Ronda and Encuentro."""

    version = models.PositiveIntegerField(
        default=1,
        verbose_name="Versión",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Save attaching the actor and the motive of the change (if given).

        Usage:
            encuentro.save(
                history_user=administrador,
                history_change_reason="Corrección de horarios",
            )
        """
        missing = object()
        history_user = kwargs.pop("history_user", missing)
        history_change_reason = kwargs.pop("history_change_reason", missing)
        previous_user = getattr(self, "_history_user", missing)
        previous_reason = getattr(self, "_change_reason", missing)

        if history_user is not missing:
            self._history_user = history_user
        if history_change_reason is not missing:
            self._change_reason = history_change_reason

        try:
            return super().save(*args, **kwargs)
        finally:
            if history_user is not missing:
                self._restore_history_attribute("_history_user", previous_user, missing)
            if history_change_reason is not missing:
                self._restore_history_attribute("_change_reason", previous_reason, missing)

    def _restore_history_attribute(self, name, previous_value, missing):
        if previous_value is missing:
            delattr(self, name)
        else:
            setattr(self, name, previous_value)
