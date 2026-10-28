"""Presentation controllers — thin HTTP handlers."""

from .auth_controller import AuthLoginController
from .registro_controller import RegistroController
from .persona_busqueda_controller import PersonaBusquedaController
from .persona_resolucion_controller import PersonaResolucionController

__all__ = [
    "AuthLoginController",
    "RegistroController",
    "PersonaBusquedaController",
    "PersonaResolucionController",
]
