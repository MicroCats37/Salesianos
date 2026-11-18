"""Vocabulario central de las capacidades de la superficie administrativa.

Este módulo es el ÚNICO lugar donde se decide qué puede hacer un actor en el
área de administración. No introduce un modelo, una tabla ni una migración:
la ÚNICA fuente de verdad son las banderas de Django (`is_staff`,
`is_superuser`), tal como exige
`contract/django-app-architecture-contract.md` §10 ("Permisos centralizados").

El mapa traduce esas banderas a un vocabulario explícito de capacidades:

- `usuario` — una cuenta registrada. No tiene capacidades administrativas.
- `staff` — administrador OPERATIVO: lee todo el área y escribe en los dominios
  operativos (competencias, acreditaciones, inscripciones, equipos). NO aprueba
  ni anula pagos ni gestiona cuentas.
- `superusuario` — break-glass: resuelve TODAS las capacidades.

Regla inviolable: en Django `is_superuser=True` salta CUALQUIER comprobación
de permisos automáticamente. Por eso el mapa NUNCA estrecha ese nivel: la
tupla de capacidades de un superusuario es siempre la completa, de modo que
nuestra comprobación nunca sea más laxa que la de Django.
"""

# ── Niveles ────────────────────────────────────────────────────────────────────

NIVEL_USUARIO = "usuario"
NIVEL_STAFF = "staff"
NIVEL_SUPERUSUARIO = "superusuario"

NIVELES = (NIVEL_USUARIO, NIVEL_STAFF, NIVEL_SUPERUSUARIO)

# ── Capacidades ───────────────────────────────────────────────────────────────

CAP_ADMIN_VER = "admin.ver"
CAP_INSCRIPCIONES_ESCRIBIR = "admin.inscripciones.escribir"
CAP_EQUIPOS_ESCRIBIR = "admin.equipos.escribir"
CAP_COMPETENCIAS_ESCRIBIR = "admin.competencias.escribir"
CAP_ACREDITACIONES_ESCRIBIR = "admin.acreditaciones.escribir"
CAP_PAGOS_VER = "admin.pagos.ver"
CAP_PAGOS_APROBAR = "admin.pagos.aprobar"
CAP_USUARIOS_VER = "admin.usuarios.ver"
CAP_USUARIOS_GESTIONAR = "admin.usuarios.gestionar"
CAP_USUARIOS_PROMOVER_SUPERUSUARIO = "admin.usuarios.promover_superusuario"
CAP_CONFIGURACION_GESTIONAR = "admin.configuracion.gestionar"

TODAS_LAS_CAPACIDADES = frozenset(
    {
        CAP_ADMIN_VER,
        CAP_INSCRIPCIONES_ESCRIBIR,
        CAP_EQUIPOS_ESCRIBIR,
        CAP_COMPETENCIAS_ESCRIBIR,
        CAP_ACREDITACIONES_ESCRIBIR,
        CAP_PAGOS_VER,
        CAP_PAGOS_APROBAR,
        CAP_USUARIOS_VER,
        CAP_USUARIOS_GESTIONAR,
        CAP_USUARIOS_PROMOVER_SUPERUSUARIO,
        CAP_CONFIGURACION_GESTIONAR,
    }
)

# El staff operativo lee TODO el área y escribe en los dominios operativos.
# NO aprueba ni anula pagos (capacidad sensible) ni gestiona cuentas.
CAPACIDADES_DE_STAFF = frozenset(
    {
        CAP_ADMIN_VER,
        CAP_INSCRIPCIONES_ESCRIBIR,
        CAP_EQUIPOS_ESCRIBIR,
        CAP_COMPETENCIAS_ESCRIBIR,
        CAP_ACREDITACIONES_ESCRIBIR,
        CAP_PAGOS_VER,
        CAP_USUARIOS_VER,
    }
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _bandera(usuario, nombre: str) -> bool:
    """Read a Django flag safely (an anonymous user has no flags)."""
    return bool(getattr(usuario, nombre, False))


def es_superusuario(usuario) -> bool:
    """Whether the actor holds the break-glass tier."""
    return _bandera(usuario, "is_superuser")


def es_staff(usuario) -> bool:
    """Whether the actor holds the operational-staff tier (without break-glass)."""
    return _bandera(usuario, "is_staff")


def es_admin(usuario) -> bool:
    """Whether the actor may enter the administration area.

    The rule is the one of the project, stated once:

        admin = is_staff OR is_superuser
    """
    return es_staff(usuario) or es_superusuario(usuario)


def nivel_de(usuario) -> str:
    """The tier of the actor: `usuario`, `staff` or `superusuario`.

    The break-glass tier wins: a superuser is `is_staff=True` too, and its
    level must never be reported as the operational one.
    """
    if es_superusuario(usuario):
        return NIVEL_SUPERUSUARIO
    if es_staff(usuario):
        return NIVEL_STAFF
    return NIVEL_USUARIO


def capacidades_de(usuario) -> frozenset:
    """The capabilities of the actor.

    - superusuario → the COMPLETE set (Django bypasses every check, so our
      map must never be narrower).
    - staff → the operational set.
    - usuario → none.
    """
    nivel = nivel_de(usuario)

    if nivel == NIVEL_SUPERUSUARIO:
        return TODAS_LAS_CAPACIDADES
    if nivel == NIVEL_STAFF:
        return CAPACIDADES_DE_STAFF
    return frozenset()


def tiene_capacidad(usuario, codigo: str) -> bool:
    """Whether the actor holds the given capability."""
    return codigo in capacidades_de(usuario)


__all__ = [
    "NIVEL_USUARIO",
    "NIVEL_STAFF",
    "NIVEL_SUPERUSUARIO",
    "NIVELES",
    "CAP_ADMIN_VER",
    "CAP_INSCRIPCIONES_ESCRIBIR",
    "CAP_EQUIPOS_ESCRIBIR",
    "CAP_COMPETENCIAS_ESCRIBIR",
    "CAP_ACREDITACIONES_ESCRIBIR",
    "CAP_PAGOS_VER",
    "CAP_PAGOS_APROBAR",
    "CAP_USUARIOS_VER",
    "CAP_USUARIOS_GESTIONAR",
    "CAP_USUARIOS_PROMOVER_SUPERUSUARIO",
    "CAP_CONFIGURACION_GESTIONAR",
    "TODAS_LAS_CAPACIDADES",
    "CAPACIDADES_DE_STAFF",
    "es_superusuario",
    "es_staff",
    "es_admin",
    "nivel_de",
    "capacidades_de",
    "tiene_capacidad",
]
