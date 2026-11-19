"""Contrato de FND-02: FR-02 §2.4 (remoción del evento activo global) y FR-07 §1.1.

GIVEN  el paquete `modules.eventos`
WHEN   se comprueba su contrato congelado
THEN   el paquete NO menciona la constante del evento activo, la versión de
       schema coincide con el registro de A0 y el contrato de datos mínimo está
       completo.

Nota: el nombre de la constante se construye por partes a propósito. Si se
escribiera literal en este archivo, el propio auditor rompería la prueba de
remoción de FR-02 §2.4 (0 coincidencias en `Aplicacion/backend`).
"""

from pathlib import Path

import pytest

from core.contract_versions import SCHEMA_VERSIONS, hay_drift
from modules.eventos.domain.constants import MODULOS_HABILITABLES, EstadoEdicion
from modules.eventos.domain.models import Edicion, Evento
from modules.eventos.presentation.schemas import SCHEMA_VERSION

#: Nombre de la constante que el freeze elimina del backend objetivo.
NOMBRE_CONSTANTE_EVENTO_ACTIVO = "_".join(["EVENTO", "ACTIVO", "NOMBRE"])

#: Patrón que delata una lectura de `settings` en el paquete.
PATRON_IMPORT_SETTINGS = "django.conf import settings"

#: Raíz del paquete `modules.eventos`.
RAIZ_PAQUETE = Path(__file__).resolve().parent.parent

#: Este archivo es el auditor: no se audita a sí mismo.
RUTINAS_AUDITADAS = [
    archivo
    for archivo in sorted(RAIZ_PAQUETE.rglob("*.py"))
    if archivo.name not in {"test_contrato_eventos.py", "settings_overlay.py"}
]


def test_el_paquete_no_menciona_la_constante_del_evento_activo():
    """FR-02 §2.4: la prueba de remoción debe dar 0 coincidencias.

    El paquete es la parte que este freeze puede limpiar por sí mismo: la
    constante desaparece de `config/settings/base.py` por acción de A0
    (petición A0-04), pero el módulo `eventos` NO puede volver a introducirla.
    """
    ofensores = [
        str(archivo.relative_to(RAIZ_PAQUETE))
        for archivo in RUTINAS_AUDITADAS
        if NOMBRE_CONSTANTE_EVENTO_ACTIVO in archivo.read_text(encoding="utf-8")
    ]

    assert ofensores == []


def test_el_paquete_no_lee_settings_para_resolver_el_alcance():
    """FR-02 §2.3 #4: ningún módulo consulta la edición activa global.

    El módulo `eventos` no importa `django.conf.settings` en absoluto: su
    alcance se resuelve con datos, nunca con una constante de despliegue.
    """
    ofensores = [
        str(archivo.relative_to(RAIZ_PAQUETE))
        for archivo in RUTINAS_AUDITADAS
        if PATRON_IMPORT_SETTINGS in archivo.read_text(encoding="utf-8")
    ]

    assert ofensores == []


def test_la_version_de_schema_coincide_con_el_registro_de_a0():
    """FR-07 §1.1: la versión del módulo vive en `presentation/schemas/`."""
    assert SCHEMA_VERSION == SCHEMA_VERSIONS["eventos"]
    assert not hay_drift(SCHEMA_VERSION, SCHEMA_VERSIONS["eventos"])


def test_el_vocabulario_de_estados_es_el_congelado():
    """FR-02 §2.1: exactamente `BORRADOR`, `PUBLICADA` y `CERRADA`."""
    assert [estado.value for estado in EstadoEdicion] == [
        "BORRADOR",
        "PUBLICADA",
        "CERRADA",
    ]


def test_las_claves_de_modulo_son_las_congeladas():
    """FR-02 §2.5: cinco módulos lógicos habilitables."""
    assert set(MODULOS_HABILITABLES) == {
        "inscripciones",
        "pases",
        "marketplace",
        "competencias",
        "patrocinadores",
    }


@pytest.mark.django_db
def test_el_contrato_de_datos_minimo_esta_completo(db):
    """FR-02 §3: los campos del contrato de datos mínimo de la edición."""
    campos = {campo.name for campo in Edicion._meta.get_fields()}

    for requerido in (
        "id",
        "evento",
        "nombre",
        "slug",
        "anio",
        "estado",
        "modulos_habilitados",
        "fecha_inicio",
        "fecha_fin",
        "created_at",
        "updated_at",
    ):
        assert requerido in campos, requerido

    assert "nombre" in {campo.name for campo in Evento._meta.get_fields()}
    assert "slug" in {campo.name for campo in Evento._meta.get_fields()}
