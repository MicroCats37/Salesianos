"""
Admin forms for the usuarios module.

`PersonaAdminForm` guards the `genero` field: an administrator cannot change
the gender of a persona who holds an ACTIVE participacion in a discipline
whose modality would become incompatible. The rule itself is NOT duplicated
here — the shared domain predicate owns the matrix, and this form only
translates a rejection into an admin validation error.
"""
from django import forms
from django.core.exceptions import ValidationError

from modules.salesianos_fest.domain.constants import EstadoParticipacionChoices
from modules.salesianos_fest.domain.models import Disciplina, Participacion
from modules.salesianos_fest.domain.validators import (
    es_genero_compatible_con_modalidad,
)
from modules.salesianos_fest.forms import (
    bloquear_para_actualizar,
    etiquetas_de_modalidad,
)

from .domain.models import Persona


class PersonaAdminForm(forms.ModelForm):
    """Admin form for Persona — guards the `genero` field.

    The guard only runs when the gender actually CHANGES: re-saving a person
    without touching the gender is always allowed, and retired participations
    never block the edit.
    """

    class Meta:
        model = Persona
        fields = "__all__"

    def clean_genero(self):
        """Reject a gender change that breaks an ACTIVE participacion."""
        genero = self.cleaned_data.get("genero")
        if not genero or genero == self.instance.genero:
            return genero

        modalidades = self._modalidades_de_las_disciplinas_activas()
        conflictivas = sorted(
            modalidad
            for modalidad in modalidades
            if not es_genero_compatible_con_modalidad(genero, modalidad)
        )
        if conflictivas:
            raise ValidationError(
                "No se puede cambiar el género: hay participaciones activas en "
                "disciplinas con modalidad "
                f"«{etiquetas_de_modalidad(conflictivas)}» que no admiten el "
                "género seleccionado."
            )
        return genero

    def _modalidades_de_las_disciplinas_activas(self):
        """Modalities of the disciplines with an ACTIVE participacion of this person.

        The query spans EVERY edition: a persona participates in disciplines of
        different events and all of them must stay compatible. The lock order
        is `discipline -> person`, the same as the core write service: the
        disciplines are locked first and the person is locked by the admin
        save that follows.
        """
        if not self.instance.pk:
            return []

        disciplina_ids = (
            Participacion.objects.filter(
                inscripcion_persona__persona_id=self.instance.pk,
                estado=EstadoParticipacionChoices.ACTIVA,
            )
            .values_list("equipo__disciplina_id", flat=True)
            .distinct()
        )
        disciplinas = bloquear_para_actualizar(
            Disciplina.objects.filter(pk__in=disciplina_ids),
        )
        return [disciplina.modalidad for disciplina in disciplinas]
