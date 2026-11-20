"""Contrato de datos y de HTTP del módulo `patrocinadores`.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md` ·
          `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

GIVEN  el paquete `modules.patrocinadores`
WHEN   se comprueba su contrato congelado
THEN   la versión de schema coincide con el registro de A0, el modelo tiene
       los campos del contrato de datos, la representación de un archivo es
       ÚNICA, el almacenamiento es el de `core/media.py`, el presenter es un
       transformador puro y NO existe ningún dominio financiero.
"""

import importlib
from pathlib import Path

import pytest
from django.db import IntegrityError, transaction

from core.contract_versions import SCHEMA_VERSIONS, hay_drift
from modules.patrocinadores.domain.models import (
    Patrocinador,
    PatrocinadorImagen,
)
from modules.patrocinadores.presentation.schemas import SCHEMA_VERSION

#: Raíz del paquete `modules.patrocinadores`.
RAIZ_PAQUETE = Path(__file__).resolve().parent.parent.parent

#: Nombres de campo que introducirían un hecho financiero o contable.
CAMPOS_FINANCIEROS_PROHIBIDOS = (
    "precio",
    "precio_oferta",
    "precio_efectivo",
    "monto",
    "total",
    "moneda",
    "comision",
    "aportacion",
    "factura",
    "pago",
    "saldo",
    "margen",
)


def _fuente_de(modulo: str) -> str:
    """El código fuente de un módulo del paquete."""
    return Path(importlib.import_module(modulo).__file__).read_text(encoding="utf-8")


def _fuentes_de_produccion() -> list[tuple[str, str]]:
    """(nombre, fuente) de todos los `.py` de producción del paquete."""
    return [
        (str(ruta.relative_to(RAIZ_PAQUETE)), ruta.read_text(encoding="utf-8"))
        for ruta in sorted(RAIZ_PAQUETE.rglob("*.py"))
        if "tests" not in ruta.parts and "__pycache__" not in ruta.parts
    ]


# ── Versión del contrato ────────────────────────────────────────────────────


def test_la_version_de_schema_coincide_con_el_registro_de_a0():
    """FR-07 §1.1: la versión del módulo vive en `presentation/schemas/`."""
    assert SCHEMA_VERSION == SCHEMA_VERSIONS["patrocinadores"]
    assert not hay_drift(SCHEMA_VERSION, SCHEMA_VERSIONS["patrocinadores"])


# ── Contrato de datos mínimo ────────────────────────────────────────────────


@pytest.mark.django_db
def test_el_contrato_de_datos_minimo_esta_completo(db):
    """FR-06 §2.6 y el plan `funcional/03` §1: los campos congelados."""
    campos_patrocinador = {campo.name for campo in Patrocinador._meta.get_fields()}
    for requerido in (
        "id",
        "edicion",
        "nombre",
        "slug",
        "descripcion",
        "sitio_web",
        "visible",
        "logo",
        "created_at",
        "updated_at",
    ):
        assert requerido in campos_patrocinador, requerido

    campos_imagen = {campo.name for campo in PatrocinadorImagen._meta.get_fields()}
    for requerido in ("id", "patrocinador", "imagen", "orden", "texto_alternativo"):
        assert requerido in campos_imagen, requerido


@pytest.mark.django_db
def test_el_slug_del_patrocinador_es_unico_dentro_de_la_edicion(edicion_publicada):
    """GIVEN dos patrocinadores con el mismo slug en la MISMA edición
    THEN   la `UniqueConstraint` los rechaza: la base es la autoridad.
    """
    Patrocinador.objects.create(
        edicion=edicion_publicada, nombre="Colegio", slug="colegio"
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Patrocinador.objects.create(
                edicion=edicion_publicada, nombre="Colegio 2", slug="colegio"
            )


@pytest.mark.django_db
def test_la_galeria_no_declara_una_imagen_principal(edicion_publicada, patrocinador):
    """FR-06 §2.6: el logo ES la imagen de identidad; la galería es un
    carrusel ordenado y NO tiene `es_principal`.
    """
    campos = {campo.name for campo in PatrocinadorImagen._meta.get_fields()}
    assert "es_principal" not in campos


# ── El protocolo de media es el compartido ──────────────────────────────────


def test_la_representacion_de_un_archivo_es_unica():
    """El archivo viaja como `ArchivoPatrocinadorUploadData` en el DTO.

    El contrato exige UNA sola representación del archivo entre el
    controller, el DTO, el orquestador y el flujo: no hay un segundo
    argumento de archivos en ninguna firma.
    """
    from modules.patrocinadores.domain.schemas.patrocinadores_schemas import (
        ArchivoPatrocinadorUploadData,
        ImagenPatrocinadorData,
        LogoPatrocinadorData,
        PatrocinadorCreateData,
    )

    assert ArchivoPatrocinadorUploadData.model_fields["archivo"].annotation is not None
    assert LogoPatrocinadorData.model_fields["upload"].annotation is not None
    assert ImagenPatrocinadorData.model_fields["upload"].annotation is not None
    assert PatrocinadorCreateData.model_fields["imagenes"].annotation is not None

    fuente_controller = _fuente_de(
        "modules.patrocinadores.presentation.controllers.patrocinadores_controller"
    )
    fuente_flujo = _fuente_de(
        "modules.patrocinadores.domain.services.flujos.patrocinador_flujo"
    )
    assert "files: list" not in fuente_controller
    assert "archivos: list" not in fuente_flujo


def test_el_paquete_no_declara_un_almacenamiento_propio():
    """El almacenamiento es el de `core/media.py`: un solo contrato.

    El módulo NO lee `django.conf.settings` por su cuenta: la política de
    media vive en `core/media.py` (A0) y el módulo la CONSUME.
    """
    from core.media import allowed_domains

    assert "patrocinadores" in allowed_domains()

    fuente = _fuente_de(
        "modules.patrocinadores.domain.services.core.patrocinador_media_service"
    )
    # La ÚNICA escritura de disco es la del storage de Django, a través de
    # la ruta que construye `core.media.construir_ruta_media`.
    assert "construir_ruta_media" in fuente
    assert "from django.conf import settings" not in fuente


def test_el_paquete_reutiliza_el_matching_de_tokens_compartido():
    """El matching EXACTAMENTE UNA VEZ es el de `core.media`.

    El módulo NO implementa su propio escaneo de tokens: consume
    `parsear_archivos_media` y `resolver_tokens_media`.
    """
    fuente = _fuente_de(
        "modules.patrocinadores.presentation.hydration.patrocinadores_hydrator"
    )
    assert "parsear_archivos_media" in fuente
    assert "resolver_tokens_media" in fuente
    assert "TOKEN_PATTERN" not in fuente
    assert "FILE_KEY_PATTERN" not in fuente


# ── El módulo NO introduce un dominio financiero ────────────────────────────


def test_el_paquete_no_declara_ningun_hecho_financiero():
    """ADM-21: no se administran aportaciones, comisiones ni facturación.

    El módulo NO declara ningún campo financiero, NO usa `Decimal` y NO
    importa los dominios comerciales compartidos (`commerce`, `pagos`).
    """
    for nombre, fuente in _fuentes_de_produccion():
        for prohibido in CAMPOS_FINANCIEROS_PROHIBIDOS:
            assert prohibido not in nombre, f"{nombre} declara {prohibido}"
        assert "Decimal" not in fuente, nombre
        assert "from modules.commerce" not in fuente, nombre
        assert "from modules.pagos" not in fuente, nombre
        assert "import commerce" not in fuente, nombre
        assert "import pagos" not in fuente, nombre


def test_los_modelos_no_declaran_campos_financieros():
    """Los modelos del módulo no tienen ni un solo campo financiero."""
    for modelo in (Patrocinador, PatrocinadorImagen):
        campos = {campo.name for campo in modelo._meta.get_fields()}
        for prohibido in CAMPOS_FINANCIEROS_PROHIBIDOS:
            assert prohibido not in campos, f"{modelo.__name__}.{prohibido}"


# ── Capas: el presenter es un transformador puro ───────────────────────────


def test_el_presenter_no_consulta_la_base_de_datos():
    """`api-wrapper-presenter-contract.md` §3: el presenter NO consulta la BD."""
    fuente = _fuente_de(
        "modules.patrocinadores.presentation.presenters.patrocinadores_presenter"
    )
    assert "objects" not in fuente
    assert "Selector" not in fuente
    assert "from modules.patrocinadores.domain.models" not in fuente
    assert "from modules.patrocinadores.domain.selectors" not in fuente


def test_el_controller_no_importa_otro_modulo_de_negocio():
    """`api-wrapper-presenter-contract.md` §1: cada módulo es dueño de su
    superficie; un controller NO importa presenters ni schemas ajenos.
    """
    fuente = _fuente_de(
        "modules.patrocinadores.presentation.controllers.patrocinadores_controller"
    )
    for modulo_ajeno in (
        "modules.marketplace",
        "modules.salesianos_fest",
        "modules.eventos",
        "modules.usuarios",
        "modules.commerce",
        "modules.pagos",
        "modules.competencias",
    ):
        assert modulo_ajeno not in fuente, modulo_ajeno


def test_el_dominio_no_importa_el_modulo_de_eventos():
    """F-49: un módulo que cruza otro DOMINIO lo hace por un PUERTO.

    El dominio `patrocinadores` declara `IAlcanceEdicion`; la implementación
    (que sí conoce `eventos`) vive en `infrastructure/`.
    """
    for nombre, fuente in _fuentes_de_produccion():
        if nombre.startswith("infrastructure"):
            continue
        assert "modules.eventos" not in fuente, nombre
