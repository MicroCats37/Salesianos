"""
auditar_genero_disciplinas — read-only audit of discipline/gender compatibility.

A persona may only hold an ACTIVE participacion in a discipline whose
modalidad is compatible with the persisted ``Persona.genero``:

    M/M, M/X, F/F, F/X  -> compatible
    M/F, F/M            -> incompatible
    any other pair      -> incompatible (fail closed)

This command is the pre-enforcement diagnostic: it reports every incompatible
ACTIVE participacion so operators can remediate the persisted data BEFORE the
lifecycle validator is enabled. It never writes.

Usage:
    python manage.py auditar_genero_disciplinas
    python manage.py auditar_genero_disciplinas --evento-id <uuid>

Output is deterministic and pipe friendly (one record per line):

    VIOLATION|<evento_id>|<participacion_id>|<persona_id>|<genero>|<disciplina_id>|<modalidad>
    SUMMARY|scanned=<n>|violations=<n>

Exit code: 0 when the audited scope has no violations, 1 when there are
violations or when the requested scope is invalid.
"""
import uuid

from django.core.management.base import BaseCommand, CommandError

from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.constants import EstadoParticipacionChoices
from modules.salesianos_fest.domain.models import Participacion

# The compatibility matrix has a single owner: the pure domain predicate.
# This command only READS data, so it must never keep a private copy of the
# rule — the audit and the lifecycle enforcement have to agree by
# construction.
from modules.salesianos_fest.domain.validators import (
    es_genero_compatible_con_modalidad,
)


class Command(BaseCommand):
    help = (
        "Audita en modo solo lectura las participaciones activas cuyo género es "
        "incompatible con la modalidad de la disciplina. No modifica ningún registro."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--evento-id",
            dest="evento_id",
            default=None,
            help="Audit only the active participations of this evento (UUID).",
        )

    def handle(self, *args, **options):
        evento_id = options.get("evento_id")

        queryset = Participacion.objects.filter(
            estado=EstadoParticipacionChoices.ACTIVA,
        )
        if evento_id is not None:
            queryset = queryset.filter(evento_id=self._resolver_evento_id(evento_id))

        participaciones = list(
            queryset.select_related("evento", "persona", "disciplina").order_by(
                "evento_id", "id",
            )
        )

        violaciones = 0
        for participacion in participaciones:
            genero = participacion.persona.genero
            modalidad = participacion.disciplina.modalidad
            if es_genero_compatible_con_modalidad(genero, modalidad):
                continue
            violaciones += 1
            self.stdout.write(
                "VIOLATION|{}|{}|{}|{}|{}|{}".format(
                    participacion.evento_id,
                    participacion.id,
                    participacion.persona_id,
                    genero,
                    participacion.disciplina_id,
                    modalidad,
                )
            )

        self.stdout.write(
            f"SUMMARY|scanned={len(participaciones)}|violations={violaciones}"
        )

        if violaciones:
            raise CommandError(
                f"Se detectaron {violaciones} participaciones activas con género "
                "incompatible con la modalidad de la disciplina."
            )

    def _resolver_evento_id(self, raw_evento_id) -> uuid.UUID:
        """Validate the --evento-id scope and return it as a UUID."""
        try:
            evento_id = uuid.UUID(str(raw_evento_id))
        except (AttributeError, TypeError, ValueError):
            raise CommandError(f"--evento-id inválido: {raw_evento_id}")

        if not Evento.objects.filter(id=evento_id).exists():
            raise CommandError(f"--evento-id inválido: no existe el evento {raw_evento_id}")

        return evento_id
