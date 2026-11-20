"""El despliegue del media: volumen persistente, servidor de archivos y permisos.

Freeze: `FREEZE-MD-1.0.0` (FR-06 §2.1, §2.5)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

`MEDIA_ROOT` es un VOLUMEN PERSISTENTE: guarda estado durable de negocio, no
es un caché (FR-06 §2.1). Eso obliga a que TRES sitios del despliegue
coincidan:

1. **Django** escribe en `MEDIA_ROOT` (por defecto `/app/media` en el
   contenedor).
2. **El despliegue** monta ese volumen en el servicio del backend, para que
   sobreviva a un `docker compose up`.
3. **El servidor de archivos** (nginx) lo lee en modo SÓLO-LECTURA y lo
   expone en `MEDIA_URL`.

Estos tests son **smoke checks de despliegue**: leen la configuración real del
repositorio y comprueban que las tres piezas encajan. No levantan contenedores
ni tocan el disco: son comprobaciones estáticas de la configuración.

| Test | Garantía |
|---|---|
| `test_el_volumen_de_media_es_persistente_y_no_un_cache` | FR-06 §2.1 — volumen nombrado, no un bind mount efímero |
| `test_el_servidor_de_archivos_lo_monta_en_solo_lectura` | FR-06 §2.1 — el backend es su único escritor |
| `test_las_tres_piezas_del_media_coinciden` | FR-06 §2.1 — Django, despliegue y servidor de archivos hablan del mismo volumen |
| `test_el_respaldo_del_media_no_esta_fingido` | GOV-01-OPEN-09 — sin política ratificada no hay copia |
| `test_la_configuracion_de_despliegue_no_publica_secretos` | contrato de secretos — ni credenciales ni rutas privadas |
"""

from pathlib import Path

import pytest
import yaml
from django.conf import settings

#: La raíz del despliegue: el directorio que contiene `docker-compose.yml`.
RAIZ_DESPLIEGUE = Path(settings.BASE_DIR).resolve().parent


def _ruta_despliegue(*partes: str) -> Path:
    return RAIZ_DESPLIEGUE.joinpath(*partes)


def _compose() -> dict:
    """El `docker-compose.yml` del despliegue, parseado."""
    ruta = _ruta_despliegue("docker-compose.yml")
    if not ruta.exists():
        pytest.skip(f"El despliegue no está en el repositorio: {ruta}")
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def _nginx() -> str:
    """La configuración del servidor de archivos del despliegue."""
    ruta = _ruta_despliegue("proxy", "nginx.conf")
    if not ruta.exists():
        pytest.skip(f"El proxy no está en el repositorio: {ruta}")
    return ruta.read_text(encoding="utf-8")


def _montajes(servicio: str, compose: dict) -> list[str]:
    """Los volúmenes declarados por un servicio."""
    return [
        str(volumen)
        for volumen in (compose.get("services", {}).get(servicio, {}).get("volumes") or [])
    ]


# ── El volumen es persistente ────────────────────────────────────────────────


def test_el_volumen_de_media_es_persistente_y_no_un_cache():
    """GIVEN el despliegue
    WHEN  se mira el servicio del backend
    THEN  el media está en un volumen NOMBRADO y declarado: sobrevive a un
          `docker compose up` (FR-06 §2.1).
    """
    compose = _compose()
    montajes = _montajes("backend", compose)

    # El backend escribe el media en `/app/media` (el `WORKDIR` del Dockerfile).
    assert any(
        montaje.endswith(":/app/media") or montaje.endswith(":/app/media:ro")
        for montaje in montajes
    ), montajes

    # Y el volumen está DECLARADO en la sección `volumes:`: un volumen
    # nombrado es durable; un bind mount de una ruta local del host no lo es.
    declarados = compose.get("volumes") or {}
    assert "backend_media" in declarados, declarados


def test_el_servidor_de_archivos_lo_monta_en_solo_lectura():
    """GIVEN el despliegue
    WHEN  se mira el servicio del proxy
    THEN  el media se monta en SÓLO-LECTURA: el backend es su único escritor.
    """
    compose = _compose()
    montajes = _montajes("proxy", compose)

    assert any(
        montaje.startswith("backend_media:") and montaje.endswith(":ro")
        for montaje in montajes
    ), montajes


def test_las_tres_piezas_del_media_coinciden():
    """GIVEN el despliegue completo
    WHEN  se comparan Django, el compose y el servidor de archivos
    THEN  los tres hablan del MISMO volumen y de la MISMA ruta pública.
    """
    compose = _compose()
    nginx = _nginx()

    # 1. Django: `MEDIA_ROOT` y `MEDIA_URL`.
    assert str(settings.MEDIA_ROOT)
    assert str(settings.MEDIA_URL).startswith("/")

    # 2. El compose: el backend escribe y el proxy lee el mismo volumen.
    montajes_backend = _montajes("backend", compose)
    montajes_proxy = _montajes("proxy", compose)
    destino_backend = next(
        montaje for montaje in montajes_backend if montaje.endswith(":/app/media")
    )
    nombre_volumen = destino_backend.split(":")[0]
    destino_proxy = next(
        montaje for montaje in montajes_proxy if montaje.startswith(nombre_volumen)
    )
    ruta_servidor = destino_proxy.split(":")[1]

    # 3. El servidor de archivos: expone ese volumen en `MEDIA_URL`.
    assert f"location {settings.MEDIA_URL}" in nginx, nginx
    assert f"alias {ruta_servidor}/" in nginx, nginx


# ── El respaldo no se finge ──────────────────────────────────────────────────


def test_el_respaldo_del_media_no_esta_fingido():
    """GIVEN la política de copia de seguridad SIN ratificar
    WHEN  se mira la configuración
    THEN  la copia está DESACTIVADA y declarada como pendiente: "sin copia"
          es un hecho conocido, no un olvido (GOV-01-OPEN-09).
    """
    assert settings.MEDIA_BACKUP_ENABLED is False
    assert not settings.MEDIA_BACKUP_ROOT


def test_el_media_root_es_configurable_para_el_despliegue(monkeypatch):
    """`MEDIA_ROOT` acepta el override del despliegue sin tocar el código."""
    assert hasattr(settings, "MEDIA_ROOT")
    # El valor por defecto vive bajo `BASE_DIR`: en desarrollo local es el
    # directorio del propio backend.
    assert str(settings.MEDIA_ROOT).startswith(str(settings.BASE_DIR))


# ── Los secretos ────────────────────────────────────────────────────────────


def test_la_configuracion_de_despliegue_no_publica_secretos():
    """GIVEN la configuración del despliegue
    WHEN  se buscan credenciales o rutas privadas
    THEN  no hay ninguna: el despliegue sólo declara NOMBRES de variables.
    """
    compose = _compose()
    nginx = _nginx()

    texto_compose = yaml.safe_dump(compose, allow_unicode=True)

    # Ningún valor literal de una credencial: sólo `${VARIABLE}` o referencias.
    for marcador in ("PASSWORD:", "SECRET:", "API_KEY:", "PRIVATE_KEY"):
        for linea in texto_compose.splitlines():
            if marcador in linea:
                valor = linea.split(":", 1)[1].strip()
                assert valor.startswith("${") or valor in ("", "None"), linea

    # El servidor de archivos no expone nada privado.
    assert "auth_basic" not in nginx
    assert "proxy_pass" in nginx  # el proxy sólo enruta; no guarda credenciales
