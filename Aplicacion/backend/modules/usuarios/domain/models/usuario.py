"""
`Usuario` — credenciales y sesión, con `Persona` OPCIONAL.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.2 · `DEC-02`.

Invariantes congeladas:

- La relación con `Persona` es 1:1 y OPCIONAL en los dos sentidos: una
  `Persona` puede no tener cuenta y una cuenta puede no tener `Persona`
  (cuentas técnicas, superusuario).
- NUNCA se crea una cuenta automáticamente al consultar un documento, al
  asignar un pase o al prellenar datos de la fuente externa.
- La autorización la resuelven los grupos Django de negocio (`Normal`,
  `Administrador`) y `is_superuser` es el nivel TÉCNICO, no un escalón
  cotidiano del negocio.
- No se inventa un sistema de permisos paralelo: se usan los grupos y las
  banderas de Django (`contract/django-app-architecture-contract.md` §10).
"""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import RegexValidator
from django.db import models

from core.models import BaseModel, DjangoAuthMixin


#: El nombre de usuario sólo admite minúsculas, números, punto, guion y
#: guion bajo. Es el `USERNAME_FIELD` del modelo de usuario.
username_validator = RegexValidator(
    regex=r"^[a-z0-9._-]+$",
    message=(
        "El nombre de usuario debe contener solo letras minúsculas, números, "
        "puntos, guiones bajos o guiones."
    ),
    code="invalid_username",
)


class UsuarioManager(BaseUserManager):
    """Manager del modelo de usuario custom."""

    def create_user(self, username: str, password: str | None = None, **extra_fields):
        if not username:
            raise ValueError("El campo username debe estar establecido.")
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        usuario = self.model(username=username, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, username: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin, DjangoAuthMixin, BaseModel):
    """Cuenta de acceso al festival.

    `AbstractBaseUser` aporta `password` y `last_login`; `PermissionsMixin`
    aporta `groups`, `user_permissions` e `is_superuser`; `DjangoAuthMixin`
    aporta `is_staff` e `is_active`; `BaseModel` aporta `id`, `created_at` y
    `updated_at`.
    """

    persona_fk = models.OneToOneField(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="usuario",
        blank=True,
        null=True,
        verbose_name="Persona asociada",
        help_text=(
            "Opcional: una cuenta técnica o de soporte puede no tener "
            "persona, y una persona puede comprar o participar sin cuenta."
        ),
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
        verbose_name="Nombre de usuario",
        help_text="Nombre de usuario para iniciar sesión.",
    )
    email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Correo electrónico",
        help_text="Contacto de la cuenta. No es un activador de derechos.",
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(email__isnull=False),
                name="unique_email_usuario_no_vacio",
            ),
        ]

    def __str__(self) -> str:
        return f"Usuario {self.username}"
