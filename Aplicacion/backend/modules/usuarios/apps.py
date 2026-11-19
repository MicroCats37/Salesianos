"""AppConfig del módulo `usuarios`.

El `label` es `usuarios` (no `modules_usuarios`) porque `AUTH_USER_MODEL`
usa el formato `<label>.<Model>`: `"usuarios.Usuario"`.
"""

from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.usuarios"
    label = "usuarios"
    verbose_name = "Usuarios e Identidad"
