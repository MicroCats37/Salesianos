"""
Crea (o actualiza) un superusuario por defecto para el admin de Django.

Idempotente: si el username ya existe, actualiza password, is_staff e is_superuser.
La identidad civil se materializa como Persona (FK obligatoria en el modelo Usuario).

Uso:
    python manage.py seed_admin
    python manage.py seed_admin --username admin --password admin
    python manage.py seed_admin --username root --password secret123
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from modules.usuarios.domain.models.persona import Persona
from modules.usuarios.domain.models.usuario import Usuario
from modules.usuarios.domain.constants import TipoDocumentoChoices, GeneroChoices


class Command(BaseCommand):
    help = "Crea o actualiza un superusuario para acceso al admin de Django."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="admin",
            help="Username del superusuario (default: admin).",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="admin",
            help="Password del superusuario (default: admin).",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="admin@salesianos.local",
            help="Email del superusuario.",
        )
        parser.add_argument(
            "--dni",
            type=str,
            default="00000000",
            help="DNI legacy del Usuario (8 dígitos, default: 00000000).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]
        dni = options["dni"]

        persona, persona_created = Persona.objects.get_or_create(
            numero_documento=dni,
            defaults={
                "nombres": "Administrador",
                "apellidos": "Sistema",
                "tipo_documento": TipoDocumentoChoices.DNI,
                "genero": GeneroChoices.MASCULINO,
            },
        )
        persona_action = "Created" if persona_created else "Reused"
        self.stdout.write(f"  {persona_action} Persona: {persona.nombres} {persona.apellidos} (DNI {dni})")

        user, user_created = Usuario.objects.get_or_create(
            username=username,
            defaults={
                "persona_fk": persona,
                "email": email,
                "dni": dni,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        user.set_password(password)
        user.persona_fk = persona
        user.email = email
        user.dni = dni
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        action = "Created" if user_created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"  {action} Superusuario: {username} / {'*' * len(password)}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"  Acceso: http://localhost:7005/admin/  (usuario: {username})"
        ))
