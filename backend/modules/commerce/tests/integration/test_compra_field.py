"""
Focused integration tests for Compra.orden_pago field name and cardinality.

Batch 1 tests for commerce-refactor-clean-rebuild:
- Verifies the field is named 'orden_pago' (not 'orden_pago_fk')
- Verifies the reverse ORM accessor is suppressed (related_name='+')
- Verifies OneToOne cardinality: Compra -> OrdenPago
- Verifies no FK back-reference from OrdenPago to Compra
"""
import pytest
from decimal import Decimal

from django.test import Client

from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.models import OrdenPago
from modules.pagos.domain.constants import OrdenPagoStatus


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(db):
    """Django test client."""
    return Client()


@pytest.fixture
def orden_pago(db):
    """Create a test OrdenPago."""
    return OrdenPago.objects.create(
        numero="ORD-TEST-001",
        monto_total=Decimal("100.00"),
        moneda="PEN",
        estado=OrdenPagoStatus.PENDIENTE,
        descripcion="Test purchase",
        referencia_externa="TEST-REF-001",
    )


# ── Tests: Field Name and Model Structure ────────────────────────────────────

@pytest.mark.django_db
def test_compra_has_orden_pago_field():
    """
    GIVEN: commerce.Compra model
    WHEN:  Inspecting the model's field list
    THEN:  Field named 'orden_pago' exists (not 'orden_pago_fk').
    """
    field_names = [f.name for f in Compra._meta.get_fields()]
    assert "orden_pago" in field_names
    assert "orden_pago_fk" not in field_names


@pytest.mark.django_db
def test_compra_orden_pago_field_is_onetoone():
    """
    GIVEN: commerce.Compra model
    WHEN:  Inspecting the 'orden_pago' field type
    THEN:  It is a OneToOneField (not ForeignKey).
    """
    from django.db.models import OneToOneField
    field = Compra._meta.get_field("orden_pago")
    assert isinstance(field, OneToOneField)


@pytest.mark.django_db
def test_compra_orden_pago_related_name_is_plus():
    """
    GIVEN: commerce.Compra model
    WHEN:  Inspecting the 'orden_pago' field's related_name
    THEN:  related_name is '+' (reverse accessor suppressed).
    """
    field = Compra._meta.get_field("orden_pago")
    assert field.remote_field.related_name == "+"


@pytest.mark.django_db
def test_orden_pago_has_no_backref_to_compra():
    """
    GIVEN: pagos.OrdenPago model
    WHEN:  Inspecting related objects on OrdenPago
    THEN:  No related object with accessor_name 'compra_comercial' exists.
           Only 'transacciones' (TransaccionPago FK) should be present.
    """
    related = OrdenPago._meta.related_objects
    accessor_names = [r.get_accessor_name() for r in related]
    assert "compra_comercial" not in accessor_names
    assert "transacciones" in accessor_names  # TransaccionPago FK - expected


@pytest.mark.django_db
def test_orden_pago_has_no_compra_field():
    """
    GIVEN: pagos.OrdenPago model
    WHEN:  Inspecting the field list on OrdenPago
    THEN:  No field named 'compra' exists.
    """
    field_names = [f.name for f in OrdenPago._meta.get_fields()]
    assert "compra" not in field_names


# ── Tests: OneToOne Cardinality ──────────────────────────────────────────────

@pytest.mark.django_db
def test_compra_orden_pago_one_to_one_assignment(api_client, orden_pago):
    """
    GIVEN: A Compra and an OrdenPago exist
    WHEN:  Assigning orden_pago to compra
    THEN:  The OneToOne relation is established correctly.
    """
    compra = Compra.objects.create(
        total=Decimal("100.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra.orden_pago = orden_pago
    compra.save()

    # Refresh from DB
    compra.refresh_from_db()

    assert compra.orden_pago == orden_pago
    assert compra.orden_pago_id == orden_pago.id


@pytest.mark.django_db
def test_compra_can_be_created_without_orden_pago():
    """
    GIVEN: No OrdenPago exists
    WHEN:  Creating a Compra without orden_pago
    THEN:  Compra is created with orden_pago=None (nullable).
    """
    compra = Compra.objects.create(
        total=Decimal("50.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    assert compra.orden_pago is None


@pytest.mark.django_db
def test_orden_pago_is_unique_per_compra(api_client, orden_pago):
    """
    GIVEN: A Compra with an OrdenPago assigned
    WHEN:  Trying to assign the same OrdenPago to another Compra
    THEN:  IntegrityError is raised (OneToOne unique constraint).
    """
    compra1 = Compra.objects.create(
        total=Decimal("100.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra1.orden_pago = orden_pago
    compra1.save()

    compra2 = Compra.objects.create(
        total=Decimal("200.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra2.orden_pago = orden_pago

    with pytest.raises(Exception):  # IntegrityError
        compra2.save()


@pytest.mark.django_db
def test_compra_filter_by_orden_pago_id(api_client, orden_pago):
    """
    GIVEN: A Compra with an OrdenPago assigned
    WHEN:  Querying Compra by orden_pago_id
    THEN:  The correct Compra is returned.
    """
    compra = Compra.objects.create(
        total=Decimal("100.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra.orden_pago = orden_pago
    compra.save()

    found = Compra.objects.filter(orden_pago_id=orden_pago.id).first()
    assert found is not None
    assert found.id == compra.id


@pytest.mark.django_db
def test_orden_pago_column_name_is_orden_pago_id():
    """
    GIVEN: commerce.Compra model
    WHEN:  Inspecting the database column name for 'orden_pago'
    THEN:  The column is 'orden_pago_id' (Django auto-generates _id suffix).
    """
    field = Compra._meta.get_field("orden_pago")
    assert field.column == "orden_pago_id"
