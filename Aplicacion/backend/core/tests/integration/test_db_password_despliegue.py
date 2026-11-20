"""El despliegue NO arranca con una contraseña de base de datos por defecto.

Hallazgo: `A0-VER03-05` (VER-03 §7 — "la contraseña **por defecto** de
desarrollo del compose aparece literal en 7 ficheros ⇒ quitar el fallback
antes de cualquier despliegue real").

Un valor por defecto escrito en el repositorio NO es un secreto: es una
credencial que cualquiera que lea el repositorio conoce, y el despliegue
arranca con ella aunque el operador nunca haya configurado nada. Por eso el
despliegue tiene que EXIGIR la credencial en vez de suponerla:

| Pieza | Garantía |
|---|---|
| `test_el_compose_exige_la_contrasena_de_la_base_de_datos` | el compose ABORTA si falta `DB_PASSWORD` (forma `${VAR:?error}`) |
| `test_los_settings_no_declaran_contrasena_por_defecto` | ningún módulo de settings da un valor por defecto a `DB_PASSWORD` |
| `test_el_entrypoint_aborta_sin_contrasena` | el arranque del contenedor falla rápido y visible si falta la credencial |
| `test_el_arbol_de_despliegue_no_declara_fallbacks_de_credencial` | ningún archivo del despliegue declara un fallback para `DB_PASSWORD` |
| `test_el_entorno_de_test_no_depende_de_una_credencial` | los tests corren en SQLite: la suite no necesita ninguna credencial |

Estos son **smoke checks de despliegue**: leen la configuración real del
repositorio. No levantan contenedores, no tocan el disco y no leen ningún
valor de credencial: comprueban la FORMA de la declaración, nunca su valor.
"""

import re
from pathlib import Path

import pytest
import yaml
from django.conf import settings

#: La raíz del despliegue: el directorio que contiene `docker-compose.yml`.
RAIZ_DESPLIEGUE = Path(settings.BASE_DIR).resolve().parent

#: La forma "obligatoria" de la interpolación de compose: `${VAR:?mensaje}`.
#: `${VAR:-valor}` es la forma "por defecto": es exactamente lo que se quiere
#: eliminar, porque hace que el despliegue funcione con una credencial conocida.
#: `${VAR:-}` (default vacío) NO es un fallback de credencial: es la forma
#: segura de preguntar "¿está definida?" sin asumir ningún valor.
FORMA_OBLIGATORIA = re.compile(r"^\$\{DB_PASSWORD:\?.+\}$")
FORMA_POR_DEFECTO_SHELL = re.compile(r"\$\{DB_PASSWORD:-[^}]")
FORMA_POR_DEFECTO_PYTHON = re.compile(r"""DB_PASSWORD["']\s*,\s*default\s*=""")


def _ruta_despliegue(*partes: str) -> Path:
    return RAIZ_DESPLIEGUE.joinpath(*partes)


def _compose() -> dict:
    """El `docker-compose.yml` del despliegue, parseado."""
    ruta = _ruta_despliegue("docker-compose.yml")
    if not ruta.exists():
        pytest.skip(f"El despliegue no está en el repositorio: {ruta}")
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def _entrypoint() -> str:
    """El script de arranque del contenedor del backend."""
    ruta = _ruta_despliegue("backend", "docker", "entrypoint.sh")
    if not ruta.exists():
        pytest.skip(f"El entrypoint no está en el repositorio: {ruta}")
    return ruta.read_text(encoding="utf-8")


def _modulos_de_settings() -> list[Path]:
    """Los módulos de settings del backend."""
    return sorted(_ruta_despliegue("backend", "config", "settings").glob("*.py"))


def _archivos_de_despliegue() -> list[Path]:
    """Los archivos de configuración del despliegue que declaran credenciales."""
    return [
        _ruta_despliegue("docker-compose.yml"),
        _ruta_despliegue("backend", "docker", "entrypoint.sh"),
        *_modulos_de_settings(),
    ]


# ── El compose exige la credencial ───────────────────────────────────────────


def test_el_compose_exige_la_contrasena_de_la_base_de_datos():
    """GIVEN el despliegue
    WHEN  se mira el servicio de base de datos
    THEN  `POSTGRES_PASSWORD` exige `DB_PASSWORD`: no hay valor por defecto.
    """
    compose = _compose()
    entorno = compose["services"]["db"]["environment"]
    valor = str(entorno["POSTGRES_PASSWORD"])

    # La forma obligatoria: si la variable falta, compose aborta con el error.
    assert FORMA_OBLIGATORIA.match(valor), valor

    # Y NO la forma por defecto: `${DB_PASSWORD:-...}`.
    assert not FORMA_POR_DEFECTO_SHELL.search(valor), valor


# ── Los settings no inventan la credencial ───────────────────────────────────


def test_los_settings_no_declaran_contrasena_por_defecto():
    """GIVEN los módulos de settings del backend
    WHEN  se buscan declaraciones de `DB_PASSWORD`
    THEN  ninguna le da un valor por defecto.
    """
    for modulo in _modulos_de_settings():
        texto = modulo.read_text(encoding="utf-8")
        assert not FORMA_POR_DEFECTO_PYTHON.search(texto), f"{modulo.name}: declara un valor por defecto"


def test_los_settings_exigen_la_credencial_cuando_el_motor_es_postgresql():
    """GIVEN el módulo base de settings
    WHEN  se lee la rama de PostgreSQL
    THEN  `DB_PASSWORD` se resuelve SIN default: si falta, Django falla.
    """
    base = _ruta_despliegue("backend", "config", "settings", "base.py")
    texto = base.read_text(encoding="utf-8")

    assert '"PASSWORD": env("DB_PASSWORD")' in texto, texto


# ── El entrypoint falla rápido ───────────────────────────────────────────────


def test_el_entrypoint_aborta_sin_contrasena():
    """GIVEN el arranque del contenedor del backend
    WHEN  `DB_PASSWORD` no está en el entorno
    THEN  el entrypoint lo detecta y ABORTA: no sondea con una credencial
          supuesta.
    """
    entrypoint = _entrypoint()

    # La guarda explícita: sin credencial, no se sigue adelante.
    assert 'if [ -z "${DB_PASSWORD:-}" ]; then' in entrypoint, entrypoint
    assert "exit 1" in entrypoint, entrypoint

    # Y el sondeo no lleva ningún valor por defecto.
    assert not FORMA_POR_DEFECTO_SHELL.search(entrypoint), entrypoint


# ── El barrido del árbol de despliegue ───────────────────────────────────────


def test_el_arbol_de_despliegue_no_declara_fallbacks_de_credencial():
    """GIVEN los archivos de configuración del despliegue
    WHEN  se buscan fallbacks de `DB_PASSWORD`
    THEN  no hay ninguno: la credencial siempre es explícita.
    """
    for archivo in _archivos_de_despliegue():
        if not archivo.exists():
            continue
        texto = archivo.read_text(encoding="utf-8")
        assert not FORMA_POR_DEFECTO_SHELL.search(texto), f"{archivo.name}: fallback de shell/compose"
        assert not FORMA_POR_DEFECTO_PYTHON.search(texto), f"{archivo.name}: default en settings"


# ── El entorno de test no depende de una credencial ──────────────────────────


def test_el_entorno_de_test_no_depende_de_una_credencial():
    """GIVEN el módulo de settings de los tests
    WHEN  se mira el motor configurado
    THEN  es SQLite: la suite corre sin ninguna credencial de base de datos.
    """
    motor = settings.DATABASES["default"]["ENGINE"]
    assert motor == "django.db.backends.sqlite3", motor
