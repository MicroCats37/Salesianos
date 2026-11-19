"""
`GrupoFuncionalService` — autoridad de los DOS grupos funcionales.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.2 · `DEC-02` · `RN-U02`.

Vocabulario cerrado de grupos de negocio (`FR-03` §1.2):

- `Normal` — accede a sus propias operaciones.
- `Administrador` — administra las operaciones previstas.

`is_superuser` es el nivel TÉCNICO (`DEC-02`): no es un rol de negocio, pero
resuelve TODAS las capacidades (igual que el bypass automático de Django en
`core/capacidades.py`). Prohibido crear un tercer grupo por defecto: la
política de los operadores de validación sigue abierta (`GOV-01-OPEN-04`).

Este servicio NO sustituye a la titularidad (`FR-03` §2.1 regla 3): ser
administrador no hace a alguien responsable de una inscripción ajena.
"""

import logging

from django.contrib.auth.models import Group

from modules.usuarios.domain.constants import GrupoFuncionalChoices
from modules.usuarios.domain.models import Usuario

logger = logging.getLogger(__name__)

#: Niveles de rol de negocio (no son los niveles técnicos de `core.capacidades`).
NIVEL_ROL_NORMAL = "normal"
NIVEL_ROL_ADMINISTRADOR = "administrador"
NIVEL_ROL_SIN_ROL = "sin_rol"


class GrupoFuncionalService:
    """Autoridad de los grupos `Normal` y `Administrador`."""

    def grupos_de(self, usuario) -> frozenset[str]:
        """Nombres de los grupos funcionales que tiene la cuenta."""
        if usuario is None or not getattr(usuario, "is_authenticated", False):
            return frozenset()
        return frozenset(
            usuario.groups.values_list("name", flat=True).distinct()
        )

    def es_normal(self, usuario) -> bool:
        """Si la cuenta tiene el grupo funcional `Normal`."""
        return GrupoFuncionalChoices.NORMAL.value in self.grupos_de(usuario)

    def es_administrador(self, usuario) -> bool:
        """Si la cuenta administra las operaciones del evento.

        El grupo `Administrador` es la vía de negocio; `is_superuser` es el
        nivel técnico de soporte y resuelve todo, para que nuestra
        comprobación nunca sea más laxa que el bypass de Django.
        """
        if usuario is None:
            return False
        if getattr(usuario, "is_superuser", False):
            return True
        return GrupoFuncionalChoices.ADMINISTRADOR.value in self.grupos_de(usuario)

    def nivel_rol(self, usuario) -> str:
        """Nivel de rol de negocio de la cuenta."""
        if self.es_administrador(usuario):
            return NIVEL_ROL_ADMINISTRADOR
        if self.es_normal(usuario):
            return NIVEL_ROL_NORMAL
        return NIVEL_ROL_SIN_ROL

    def asignar_grupo(self, usuario: Usuario, nombre_grupo: str) -> Usuario:
        """Asigna un grupo funcional, con control de elevación.

        Otorgar el grupo `Administrador` es una acción sensible: la ejecuta
        el actor y queda registrada en el log del servidor con el motivo del
        paquete que la pide (`FR-03` §5).
        """
        valido = GrupoFuncionalChoices(nombre_grupo)
        grupo, _creado = Group.objects.get_or_create(name=valido.value)
        usuario.groups.add(grupo)
        logger.info(
            "Grupo funcional %s asignado a la cuenta %s.",
            valido.value,
            usuario.username,
        )
        return usuario

    def quitar_grupo(self, usuario: Usuario, nombre_grupo: str) -> Usuario:
        """Quita un grupo funcional de la cuenta."""
        valido = GrupoFuncionalChoices(nombre_grupo)
        usuario.groups.remove(Group.objects.filter(name=valido.value).first())
        logger.info(
            "Grupo funcional %s retirado a la cuenta %s.",
            valido.value,
            usuario.username,
        )
        return usuario


__all__ = [
    "NIVEL_ROL_ADMINISTRADOR",
    "NIVEL_ROL_NORMAL",
    "NIVEL_ROL_SIN_ROL",
    "GrupoFuncionalService",
]
