"""
Management command to create a fixed admin superuser.

Usage:
    python manage.py create_admin --settings=config.settings.development
    python manage.py create_admin --settings=config.settings.development --force
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from modules.usuarios.domain.constants import GeneroChoices, TipoDocumentoChoices
from modules.usuarios.domain.models import Persona, Usuario

ADMIN_DNI = "00000000"
ADMIN_PASSWORD = "admin"


class Command(BaseCommand):
    help = "Create or update a fixed admin superuser (DNI: 00000000, password: admin)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force password reset even if user already exists with correct password",
        )

    def _get_or_create_admin_persona(self):
        """Create or reuse the deterministic admin Persona."""
        persona, created = Persona.objects.update_or_create(
            tipo_documento=TipoDocumentoChoices.DNI,
            numero_documento=ADMIN_DNI,
            defaults={
                "nombres": "Admin",
                "apellidos": "Sistema",
                "genero": GeneroChoices.MASCULINO,
            },
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin Persona created: {persona.nombres} {persona.apellidos}, "
                    f"DNI {ADMIN_DNI}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin Persona reused: {persona.nombres} {persona.apellidos}, "
                    f"DNI {ADMIN_DNI}, id={persona.pk}"
                )
            )
        return persona

    def handle(self, *args, **options):
        persona = self._get_or_create_admin_persona()

        defaults = {
            "persona_fk": persona,
            "email": "admin@example.com",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }

        user, created = Usuario.objects.update_or_create(
            username="admin",
            defaults=defaults,
        )

        # Always set the password to ensure it matches
        user.set_password(ADMIN_PASSWORD)
        user.save(update_fields=["password"])

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin user created: username=admin, password={ADMIN_PASSWORD}"
                )
            )
        else:
            action = "updated" if options["force"] else "verified"
            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin user {action}: username=admin, password={ADMIN_PASSWORD}, "
                    f"is_staff={user.is_staff}, is_superuser={user.is_superuser}, "
                    f"is_active={user.is_active}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Login credentials: username=admin, password={ADMIN_PASSWORD}"
            )
        )