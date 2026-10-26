"""
Admin forms for the salesianos_fest module.

The discipline/gender compatibility rule has a single owner: the pure domain
predicate `es_genero_compatible_con_modalidad`. Every admin form CALLS that
predicate — nobody keeps a private copy of the matrix, because a duplicated
matrix lets the audit, the lifecycle enforcement and the admin drift apart
silently.

Guards implemented here:

- `DisciplinaAdminForm` rejects a `modalidad` change that would leave an
  ACTIVE participacion incompatible, in ANY edition.
- `ParticipacionAdminForm` does NOT re-check the rule: `Participacion.clean()`
  is the safety net for the write paths that bypass the core service and it
  already raises the Django `ValidationError`. The form wires that single
  report into the admin, so the conflict is never reported twice.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.db import connection

from modules.usuarios.domain.constants import GeneroChoices
from modules.usuarios.domain.models import Persona

from .domain.constants import EstadoParticipacionChoices, ModalidadChoices
from .domain.models import Disciplina, Participacion
from .domain.validators import es_genero_compatible_con_modalidad


# Human labels for the admin messages: they name the RULE, never a record.
ETIQUETAS_MODALIDAD = {
    ModalidadChoices.MASCULINO: "Masculino",
    ModalidadChoices.FEMENINO: "Femenino",
    ModalidadChoices.MIXTO: "Mixto",
}

ETIQUETAS_GENERO = {
    GeneroChoices.MASCULINO: "Masculino",
    GeneroChoices.FEMENINO: "Femenino",
}


def etiquetas_de_modalidad(codigos):
    """Sorted, human readable labels for a collection of modality codes."""
    etiquetas = {ETIQUETAS_MODALIDAD.get(codigo, codigo) for codigo in codigos}
    return ", ".join(sorted(etiquetas))


def etiquetas_de_genero(codigos):
    """Sorted, human readable labels for a collection of gender codes."""
    etiquetas = {ETIQUETAS_GENERO.get(codigo, codigo) for codigo in codigos}
    return ", ".join(sorted(etiquetas))


def bloquear_para_actualizar(queryset):
    """Return the rows of `queryset`, locking them when inside a transaction.

    The Django admin runs inside a transaction, so the row locks are taken in
    the same `discipline -> person` order as the core write service, which
    closes the race against a concurrent participation write. Outside a
    transaction (scripts, tests) the rows are read without a lock instead of
    failing with a transaction error.
    """
    if connection.in_atomic_block:
        return list(queryset.select_for_update())
    return list(queryset)


class DisciplinaAdminForm(forms.ModelForm):
    """Admin form for Disciplina — guards the `modalidad` field.

    The guard only runs when the modality actually CHANGES: re-saving a
    discipline without touching its modality is always allowed.
    """

    class Meta:
        model = Disciplina
        fields = "__all__"

    def clean_modalidad(self):
        """Reject a modality change that breaks an ACTIVE participacion."""
        modalidad = self.cleaned_data.get("modalidad")
        if not modalidad or modalidad == self.instance.modalidad:
            return modalidad

        generos = self._generos_de_los_participantes_activos()
        conflictivos = sorted(
            genero
            for genero in generos
            if not es_genero_compatible_con_modalidad(genero, modalidad)
        )
        if conflictivos:
            raise ValidationError(
                "No se puede cambiar la modalidad a "
                f"«{ETIQUETAS_MODALIDAD.get(modalidad, modalidad)}»: hay "
                "participaciones activas de personas con género "
                f"«{etiquetas_de_genero(conflictivos)}» que no admiten esa "
                "modalidad."
            )
        return modalidad

    def _generos_de_los_participantes_activos(self):
        """Genders of the people with an ACTIVE participacion in this discipline.

        The query spans EVERY edition: a discipline is used by several events
        and all of its active participations must stay compatible. The lock
        order is `discipline -> person`, the same as the core write service.
        """
        if not self.instance.pk:
            return []

        # discipline first ...
        bloquear_para_actualizar(
            Disciplina.objects.filter(pk=self.instance.pk),
        )

        persona_ids = (
            Participacion.objects.filter(
                equipo__disciplina_id=self.instance.pk,
                estado=EstadoParticipacionChoices.ACTIVA,
            )
            .values_list("inscripcion_persona__persona_id", flat=True)
            .distinct()
        )
        # ... and then the people.
        personas = bloquear_para_actualizar(
            Persona.objects.filter(pk__in=persona_ids),
        )
        return [persona.genero for persona in personas]


class ParticipacionAdminForm(forms.ModelForm):
    """Admin form for Participacion.

    The discipline/gender rule is NOT re-implemented here: `Participacion.clean()`
    is the safety net for the write paths that bypass the core service, and it
    raises the Django `ValidationError` when an ACTIVE participacion is
    incompatible with the modality of its discipline.

    This form exists to make that SINGLE report explicit in the admin (and in
    the `Equipo` inline). It deliberately does not check the rule again, so a
    conflict is never reported twice.
    """

    class Meta:
        model = Participacion
        fields = "__all__"
