"""Comando de gestión: alta de la primera edición de una instalación.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`

FR-02 §2.4 autoriza, durante FND-02, usar el nombre del evento activo como
VALOR SEMILLA al crear la primera edición de una instalación nueva, y
**sólo** en un comando de gestión (nunca en el arranque del servidor).

Este comando materializa esa regla SIN constantes de settings: el nombre se
pide por parámetro. La razón es la PRUEBA DE REMOCIÓN obligatoria de FR-02
§2.4 — la búsqueda del nombre de la constante del evento activo dentro de
`Aplicacion/backend` debe devolver 0 coincidencias al cerrar FND-02 — y una
referencia a ese nombre dentro de este paquete produciría una coincidencia.
El operador escribe el nombre una vez, en la línea de comandos, y el valor
queda en la base de datos.

Uso:

    python manage.py crear_edicion_inicial \
        --evento-nombre "Salesianos FEST" \
        --evento-slug "salesianos-fest" \
        --edicion-nombre "Salesianos FEST 2026" \
        --edicion-slug "2026" \
        --anio 2026 \
        [--publicar] \
        [--modulo inscripciones --modulo pases]

El comando es IDEMPOTENTE: si la edición ya existe (mismo slug dentro del
mismo evento) no la duplica; informa y termina con código 0.
"""

from django.core.management.base import BaseCommand

from modules.eventos.domain.constants import MODULOS_HABILITABLES
from modules.eventos.domain.schemas.edicion_schemas import EdicionCreateData
from modules.eventos.domain.selectors.edicion_selector import EdicionSelector
from modules.eventos.domain.selectors.evento_selector import EventoSelector
from modules.eventos.domain.services.core.edicion_core_service import EdicionCoreService
from modules.eventos.domain.services.core.edicion_scope_service import EdicionScopeService
from modules.eventos.domain.services.flujos.edicion_flujo import EdicionFlujo
from modules.eventos.domain.services.orchestrators.edicion_orchestrator import (
    EdicionOrchestrator,
)


class Command(BaseCommand):
    """Crea (o recupera) la primera edición de una instalación."""

    help = "Crea la primera edición de un evento. Es idempotente."

    def add_arguments(self, parser):
        parser.add_argument("--evento-nombre", required=True, help="Nombre del evento.")
        parser.add_argument("--evento-slug", required=True, help="Slug del evento.")
        parser.add_argument("--edicion-nombre", required=True, help="Nombre de la edición.")
        parser.add_argument("--edicion-slug", required=True, help="Slug de la edición.")
        parser.add_argument("--anio", required=True, type=int, help="Año de la edición.")
        parser.add_argument(
            "--modulo",
            action="append",
            default=[],
            choices=list(MODULOS_HABILITABLES),
            help="Módulo lógico a habilitar (repetible).",
        )
        parser.add_argument(
            "--publicar",
            action="store_true",
            help="Publica la edición al crearla.",
        )

    def handle(self, *args, **options):
        from asgiref.sync import async_to_sync

        evento_selector = EventoSelector()
        edicion_selector = EdicionSelector()
        core_service = EdicionCoreService(
            edicion_selector=edicion_selector,
            evento_selector=evento_selector,
        )
        scope_service = EdicionScopeService(selector=edicion_selector)
        flujo = EdicionFlujo(core_service=core_service, scope_service=scope_service)
        orchestrator = EdicionOrchestrator(scope_service=scope_service, flujo=flujo)

        evento, creado_evento = self._evento(evento_selector, options)
        edicion_existente = edicion_selector.obtener_por_slug(evento.id, options["edicion_slug"])
        if edicion_existente is not None:
            self.stdout.write(
                self.style.WARNING(
                    "La edición ya existía; no se creó una segunda."
                )
            )
            return

        data = EdicionCreateData(
            evento_id=evento.id,
            nombre=options["edicion_nombre"],
            slug=options["edicion_slug"],
            anio=options["anio"],
            modulos_habilitados=list(options["modulo"] or []),
        )
        edicion = async_to_sync(orchestrator.crear_edicion)(data)
        self.stdout.write(
            self.style.SUCCESS(
                f"Edición creada ({'evento nuevo' if creado_evento else 'evento existente'})."
            )
        )

        if options["publicar"]:
            async_to_sync(orchestrator.publicar_edicion)(edicion.id)
            self.stdout.write(self.style.SUCCESS("Edición publicada."))

    def _evento(self, evento_selector, options):
        """Devuelve `(evento, creado)`; crea el evento si no existe."""
        from modules.eventos.domain.models import Evento

        evento = evento_selector.obtener_por_slug(options["evento_slug"])
        if evento is not None:
            return evento, False
        evento = Evento.objects.create(
            nombre=options["evento_nombre"],
            slug=options["evento_slug"],
        )
        return evento, True
