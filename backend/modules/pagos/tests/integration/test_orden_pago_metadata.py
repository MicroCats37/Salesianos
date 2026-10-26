"""
Integration tests for OrdenPago metadata contract.

Tests:
- sanitize_metadata strips unauthorized keys
- sanitize_metadata strips forbidden keys
- sanitize_metadata accepts None gracefully
- crear_orden_pago accepts and stores descripcion, referencia_externa
- crear_orden_pago stores sanitized metadata
- crear_orden_pago rejects forbidden metadata keys
- metadata is not exposed in OrdenPagoOut schema (by omission)
- METADATA_ALLOWED_KEYS contract documented
"""
import pytest
from decimal import Decimal

from modules.pagos.domain.models import OrdenPago
from modules.pagos.domain.constants import METADATA_ALLOWED_KEYS, METADATA_FORBIDDEN_KEYS
from modules.pagos.domain.services.core.izipay_core_service import (
    IzipayCoreService,
    sanitize_metadata,
)


@pytest.fixture
def izipay_core_service():
    return IzipayCoreService()


# ── sanitize_metadata contract tests ────────────────────────────────────────────

def test_sanitize_metadata_strips_unknown_keys():
    """
    GIVEN: metadata with allowed + unknown keys
    WHEN: sanitize_metadata is called
    THEN: Only allowed keys are kept.
    """
    dirty = {
        "source": "fest",
        "purchase_reference": "REF-001",
        "inscripcion_id": "uuid-123",
        "unknown_key": "should be stripped",
        "another_bad": 42,
    }
    result = sanitize_metadata(dirty)
    assert result == {
        "source": "fest",
        "purchase_reference": "REF-001",
        "inscripcion_id": "uuid-123",
    }
    assert "unknown_key" not in result
    assert "another_bad" not in result


def test_sanitize_metadata_strips_forbidden_keys():
    """
    GIVEN: metadata with forbidden security-sensitive keys
    WHEN: sanitize_metadata is called
    THEN: Forbidden keys are stripped even if they are in ALLOWED_KEYS.
    """
    dangerous = {
        "source": "fest",
        "auth_token": "Bearer secret",
        "session_token": "sess_abc",
        "password": "hunter2",
        "api_key": "sk_live_xxx",
        "secret": "top_secret",
    }
    result = sanitize_metadata(dangerous)
    assert result == {"source": "fest"}
    assert "auth_token" not in result
    assert "session_token" not in result
    assert "password" not in result
    assert "api_key" not in result
    assert "secret" not in result


def test_sanitize_metadata_none_returns_empty_dict():
    """
    GIVEN: metadata is None
    WHEN: sanitize_metadata is called
    THEN: An empty dict is returned (safe for JSONField).
    """
    assert sanitize_metadata(None) == {}


def test_sanitize_metadata_empty_dict_returns_empty_dict():
    """
    GIVEN: metadata is {}
    WHEN: sanitize_metadata is called
    THEN: {} is returned.
    """
    assert sanitize_metadata({}) == {}


def test_metadata_allowed_keys_defined():
    """
    GIVEN: METADATA_ALLOWED_KEYS constant
    THEN: It is a frozenset with expected audit/display keys.
    """
    assert "source" in METADATA_ALLOWED_KEYS
    assert "purchase_reference" in METADATA_ALLOWED_KEYS
    assert "display_context" in METADATA_ALLOWED_KEYS
    assert "inscripcion_id" in METADATA_ALLOWED_KEYS
    assert "paquete_id" in METADATA_ALLOWED_KEYS
    assert "evento_id" in METADATA_ALLOWED_KEYS


def test_metadata_forbidden_keys_defined():
    """
    GIVEN: METADATA_FORBIDDEN_KEYS constant
    THEN: It contains security-sensitive key names.
    """
    assert "auth_token" in METADATA_FORBIDDEN_KEYS
    assert "password" in METADATA_FORBIDDEN_KEYS
    assert "secret" in METADATA_FORBIDDEN_KEYS
    assert "api_key" in METADATA_FORBIDDEN_KEYS


# ── crear_orden_pago with new fields ──────────────────────────────────────────

@pytest.mark.django_db
def test_crear_orden_pago_stores_descripcion(izipay_core_service):
    """
    GIVEN: A generated order number
    WHEN: crear_orden_pago is called with descripcion
    THEN: descripcion is stored on the OrdenPago.
    """
    numero = izipay_core_service.generar_numero_orden()
    orden = izipay_core_service.crear_orden_pago(
        numero=numero,
        monto_total=Decimal("150.00"),
        moneda="PEN",
        descripcion="Compra Inicial - Paquete Premium",
    )
    assert orden.descripcion == "Compra Inicial - Paquete Premium"


@pytest.mark.django_db
def test_crear_orden_pago_stores_referencia_externa(izipay_core_service):
    """
    GIVEN: A generated order number
    WHEN: crear_orden_pago is called with referencia_externa
    THEN: referencia_externa is stored on the OrdenPago.
    """
    numero = izipay_core_service.generar_numero_orden()
    orden = izipay_core_service.crear_orden_pago(
        numero=numero,
        monto_total=Decimal("150.00"),
        moneda="PEN",
        referencia_externa="FEST-ABCDEF12",
    )
    assert orden.referencia_externa == "FEST-ABCDEF12"


@pytest.mark.django_db
def test_crear_orden_pago_stores_sanitized_metadata(izipay_core_service):
    """
    GIVEN: metadata with allowed + unknown keys
    WHEN: crear_orden_pago is called with metadata
    THEN: Only allowed keys are stored (unknown keys stripped).
    """
    numero = izipay_core_service.generar_numero_orden()
    orden = izipay_core_service.crear_orden_pago(
        numero=numero,
        monto_total=Decimal("200.00"),
        moneda="PEN",
        metadata={
            "source": "fest",
            "inscripcion_id": "uuid-456",
            "paquete_id": "uuid-789",
            "paquete_nombre": "Paquete Full",
            "evento_id": "uuid-event",
            "unknown_field": "should be stripped",
        },
    )
    assert orden.metadata == {
        "source": "fest",
        "inscripcion_id": "uuid-456",
        "paquete_id": "uuid-789",
        "paquete_nombre": "Paquete Full",
        "evento_id": "uuid-event",
    }
    assert "unknown_field" not in orden.metadata


@pytest.mark.django_db
def test_crear_orden_pago_strips_forbidden_metadata_keys(izipay_core_service):
    """
    GIVEN: metadata with forbidden keys
    WHEN: crear_orden_pago is called
    THEN: Forbidden keys are not stored.
    """
    numero = izipay_core_service.generar_numero_orden()
    orden = izipay_core_service.crear_orden_pago(
        numero=numero,
        monto_total=Decimal("200.00"),
        moneda="PEN",
        metadata={
            "source": "fest",
            "auth_token": "Bearer xxx",
            "password": "secret",
        },
    )
    assert orden.metadata == {"source": "fest"}
    assert "auth_token" not in orden.metadata
    assert "password" not in orden.metadata


@pytest.mark.django_db
def test_crear_orden_pago_metadata_none_is_safe(izipay_core_service):
    """
    GIVEN: metadata=None
    WHEN: crear_orden_pago is called
    THEN: No exception is raised — None is safely converted to {}.
    """
    numero = izipay_core_service.generar_numero_orden()
    orden = izipay_core_service.crear_orden_pago(
        numero=numero,
        monto_total=Decimal("50.00"),
        moneda="PEN",
        metadata=None,
    )
    assert orden.metadata == {}


# ── OrdenPagoOut schema — metadata NOT exposed ─────────────────────────────────

def test_orden_pago_out_schema_excludes_metadata():
    """
    GIVEN: OrdenPagoOut schema
    WHEN: inspecting the schema fields
    THEN: metadata is NOT a field (not exposed to frontend by default).
    """
    from modules.pagos.presentation.schemas.pago_schema import OrdenPagoOut
    # metadata must not be in the schema output fields
    assert "metadata" not in OrdenPagoOut.model_fields


def test_orden_pago_out_schema_includes_descripcion():
    """
    GIVEN: OrdenPagoOut schema
    WHEN: inspecting the schema fields
    THEN: descripcion IS exposed (safe — CharField).
    """
    from modules.pagos.presentation.schemas.pago_schema import OrdenPagoOut
    assert "descripcion" in OrdenPagoOut.model_fields


def test_orden_pago_out_schema_includes_referencia_externa():
    """
    GIVEN: OrdenPagoOut schema
    WHEN: inspecting the schema fields
    THEN: referencia_externa IS exposed (safe — CharField).
    """
    from modules.pagos.presentation.schemas.pago_schema import OrdenPagoOut
    assert "referencia_externa" in OrdenPagoOut.model_fields


# ── admin displays correct fields ──────────────────────────────────────────────

def test_orden_pago_admin_list_display_includes_snapshot_fields():
    """
    GIVEN: OrdenPagoAdmin
    WHEN: inspecting list_display
    THEN: descripcion and referencia_externa are shown; metadata is not.
    """
    from modules.pagos.admin import OrdenPagoAdmin
    admin = OrdenPagoAdmin(OrdenPago, None)
    assert "descripcion" in admin.list_display
    assert "referencia_externa" in admin.list_display
    # metadata should NOT be in list_display — not exposed to admin users by default
    assert "metadata" not in admin.list_display
