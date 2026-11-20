"""
DTOs internos (Pydantic) de autenticación y sesión.

`contract/PLAN_REFACTORIZACION.md` §3.C: son `BaseModel` de Pydantic puro,
NO schemas HTTP. Reflejan lo que la capa de servicios necesita; el presenter
los traduce a los wrappers `*Out`.

El vocabulario que viajan aquí es el del OBJETIVO:

- El identificador civil NO es una credencial: la cuenta se resuelve por
  `Persona.numero_documento` y el resultado es una cuenta o `None`
  (`FR-03` §1.1, `RN-U04`).
- Los hechos de rol los publica el BACKEND: el grupo funcional de negocio
  (`Normal` / `Administrador`, `FR-03` §1.2) y la política técnica de
  `core/capacidades.py`. El cliente nunca los deriva ni los decide
  (`contratos/02` §3: "no confiar en una cookie de rol").
"""

from datetime import datetime

from pydantic import BaseModel


class SesionUsuarioResult(BaseModel):
    """Hechos de sesión que el backend publica del actor autenticado.

    Todos son AUTOS (self-scoped): el endpoint publica el nivel del propio
    llamador. No es una filtración: es la base de la interfaz, y la
    autorización se vuelve a evaluar en el backend en cada petición.
    """

    id: str
    username: str
    email: str | None = None
    nombres: str | None = None
    apellidos: str | None = None
    persona_id: str | None = None
    rol: str = "sin_rol"
    grupos: list[str] = []
    es_admin: bool = False
    is_staff: bool = False
    is_superuser: bool = False
    nivel: str = "usuario"
    capacidades: list[str] = []


class LoginTokenResult(BaseModel):
    """Resultado de un inicio de sesión exitoso.

    Los tokens los emite `django-ninja-jwt`; este DTO sólo los transporta
    junto con los hechos de sesión del actor.
    """

    access_token: str
    refresh_token: str
    expires_at: datetime
    user: SesionUsuarioResult


__all__ = ["LoginTokenResult", "SesionUsuarioResult"]
