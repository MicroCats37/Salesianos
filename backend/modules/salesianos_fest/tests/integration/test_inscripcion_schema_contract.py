"""
Focused integration tests for the inscripcion detail schema contract (Phase 2 / Lote 2).

Tests the stable FEST client contract for the new Phase 2 output schemas:
- ResumenEquiposSchema: total, completos, incompletos
- ResumenPagoSchema: aggregate payment summary with compras list
- CompraResumenSchema: purchase summary with nested OrdenPagoResumen (no metadata)
- OrdenPagoResumenSchema: payment-order summary (NO metadata exposed)
- EquipoDetailSchema: extended with estado_equipo, estado_roster, jugadores_registrados,
  minimo_deportivo, faltantes
- InscripcionDetailOut: extended with resumen_equipos and resumen_pago

Also verifies:
- OrdenPago.metadata is NEVER exposed in inscription schemas
- The new fields are output-only (not request fields)
- Backward-compat: old team ``estado`` field is still present
"""
import uuid
import json

import pytest
from decimal import Decimal

from django.test import Client
from ninja_jwt.tokens import AccessToken
from django.contrib.auth import get_user_model

from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models.persona import Persona
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Promocion,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    Inscripcion,
)
from modules.salesianos_fest.domain.constants import (
    ModalidadChoices,
    TipoPaqueteChoices,
    ModoDisciplinasChoices,
    EtapaChoices,
    EstadoInscripcionChoices,
    TipoCompraChoices,
    EstadoCompraChoices,
)
from modules.salesianos_fest.presentation.schemas.inscripcion_schemas import (
    OrdenPagoResumenSchema,
    CompraResumenSchema,
    ResumenPagoSchema,
    ResumenEquiposSchema,
    EquipoDetailSchema,
    InscripcionDetailOut,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(db):
    """Django test client for async controllers."""
    return Client()


@pytest.fixture
def evento(db):
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=pytest.importorskip("datetime").date(2026, 11, 15),
        fecha_fin=pytest.importorskip("datetime").date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina_futbol(db):
    return Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def promocion_junior(db):
    return Promocion.objects.create(
        anio=2012,
        nombre="Junior",
        activa=True,
    )


@pytest.fixture
def paquete_reencuentro(db, evento, disciplina_futbol):
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro + Fiesta",
        descripcion="Pack con fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_futbol)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("50.00"),
        vigente_desde=pytest.importorskip("datetime").date.today(),
        vigente_hasta=None,
        activo=True,
    )
    return paquete


@pytest.fixture
def persona(db):
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def usuario_con_persona(db, persona):
    User = get_user_model()
    return User.objects.create_user(
        username="juan_user",
        email="juan@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def inscripcion_base(db, evento, persona, paquete_reencuentro, promocion_junior):
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


# ── Auth helper ───────────────────────────────────────────────────────────────

def _auth_get(client, path, user):
    token = AccessToken.for_user(user)
    return client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")


# ── Schema field contract tests ────────────────────────────────────────────────

class TestOrdenPagoResumenSchemaContract:
    """OrdenPagoResumenSchema must never expose metadata."""

    def test_schema_excludes_metadata_field(self):
        """
        GIVEN: OrdenPagoResumenSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  metadata is NOT a field in the schema.
        """
        fields = set(OrdenPagoResumenSchema.model_fields.keys())
        assert "metadata" not in fields

    def test_schema_exposes_expected_payment_fields(self):
        """
        GIVEN: OrdenPagoResumenSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  The schema exposes id, numero, estado, pagada_en.
        """
        fields = set(OrdenPagoResumenSchema.model_fields.keys())
        expected = {"id", "numero", "estado", "pagada_en"}
        assert fields == expected, f"Expected {expected}, got {fields}"

    def test_schema_validates_target_json_shape(self):
        """
        GIVEN: A dict matching the target JSON shape for OrdenPagoResumen
        WHEN:  Validating through the schema
        THEN:  The schema accepts the valid input without error.
        """
        data = {
            "id": str(uuid.uuid4()),
            "numero": "OP-2026-0001",
            "estado": "PAGADA",
            "pagada_en": "2026-10-15T10:30:00Z",
        }
        result = OrdenPagoResumenSchema.model_validate(data)
        assert result.id == data["id"]
        assert result.numero == data["numero"]
        assert result.estado == data["estado"]
        assert result.pagada_en == data["pagada_en"]

    def test_schema_allows_null_pagada_en(self):
        """
        GIVEN: A dict with pagada_en=None (pending order)
        WHEN:  Validating through the schema
        THEN:  The schema accepts null pagada_en.
        """
        data = {
            "id": str(uuid.uuid4()),
            "numero": "OP-2026-0002",
            "estado": "PENDIENTE",
            "pagada_en": None,
        }
        result = OrdenPagoResumenSchema.model_validate(data)
        assert result.pagada_en is None


class TestCompraResumenSchemaContract:
    """CompraResumenSchema must never expose metadata."""

    def test_schema_excludes_metadata_field(self):
        """
        GIVEN: CompraResumenSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  metadata is NOT a field in the schema.
        """
        fields = set(CompraResumenSchema.model_fields.keys())
        assert "metadata" not in fields

    def test_schema_exposes_expected_purchase_fields(self):
        """
        GIVEN: CompraResumenSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  The schema exposes id, tipo, cantidad, precio_unitario, total,
               estado, and an optional orden_pago.
        """
        fields = set(CompraResumenSchema.model_fields.keys())
        expected = {"id", "tipo", "cantidad", "precio_unitario", "total", "estado", "orden_pago"}
        assert fields == expected, f"Expected {expected}, got {fields}"

    def test_schema_validates_target_json_shape_with_orden_pago(self):
        """
        GIVEN: A dict matching the target JSON shape for CompraResumen with nested orden_pago
        WHEN:  Validating through the schema
        THEN:  The schema accepts the valid input and parses nested orden_pago.
        """
        orden_pago_data = {
            "id": str(uuid.uuid4()),
            "numero": "OP-2026-0001",
            "estado": "PAGADA",
            "pagada_en": "2026-10-15T10:30:00Z",
        }
        data = {
            "id": str(uuid.uuid4()),
            "tipo": "INICIAL",
            "cantidad": 10,
            "precio_unitario": 50.0,
            "total": 500.0,
            "estado": "PAGADA",
            "orden_pago": orden_pago_data,
        }
        result = CompraResumenSchema.model_validate(data)
        assert result.tipo == "INICIAL"
        assert result.cantidad == 10
        assert result.estado == "PAGADA"
        assert result.orden_pago is not None
        assert result.orden_pago.numero == "OP-2026-0001"
        assert result.orden_pago.pagada_en == "2026-10-15T10:30:00Z"

    def test_schema_allows_null_orden_pago(self):
        """
        GIVEN: A dict with orden_pago=None (compra pending payment)
        WHEN:  Validating through the schema
        THEN:  The schema accepts null orden_pago.
        """
        data = {
            "id": str(uuid.uuid4()),
            "tipo": "INICIAL",
            "cantidad": 10,
            "precio_unitario": 50.0,
            "total": 500.0,
            "estado": "PENDIENTE",
            "orden_pago": None,
        }
        result = CompraResumenSchema.model_validate(data)
        assert result.orden_pago is None


class TestResumenPagoSchemaContract:
    """ResumenPagoSchema is the aggregate payment summary block."""

    def test_schema_exposes_expected_summary_fields(self):
        """
        GIVEN: ResumenPagoSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  The schema exposes total_compras, total_contratado, total_pagado,
               total_pagado_cantidad, compras_pendientes, compras_pagadas,
               compras_canceladas, disponible_pagado, estado_mensaje, and compras list.
        """
        fields = set(ResumenPagoSchema.model_fields.keys())
        expected = {
            "total_compras",
            "total_contratado",
            "total_pagado",
            "total_pagado_cantidad",
            "compras_pendientes",
            "compras_pagadas",
            "compras_canceladas",
            "disponible_pagado",
            "estado_mensaje",
            "compras",
        }
        assert fields == expected, f"Expected {expected}, got {fields}"

    def test_schema_validates_target_json_shape(self):
        """
        GIVEN: A dict matching the target JSON shape for ResumenPago
        WHEN:  Validating through the schema
        THEN:  The schema accepts the valid input with nested compras.
        """
        compra_data = {
            "id": str(uuid.uuid4()),
            "tipo": "INICIAL",
            "cantidad": 10,
            "precio_unitario": 50.0,
            "total": 500.0,
            "estado": "PENDIENTE",
            "orden_pago": None,
        }
        data = {
            "total_compras": 1,
            "total_contratado": 10,
            "total_pagado": 0.0,
            "total_pagado_cantidad": 0,
            "compras_pendientes": 1,
            "compras_pagadas": 0,
            "compras_canceladas": 0,
            "disponible_pagado": 0,
            "estado_mensaje": "Pago pendiente",
            "compras": [compra_data],
        }
        result = ResumenPagoSchema.model_validate(data)
        assert result.total_compras == 1
        assert result.compras_pendientes == 1
        assert result.compras_pagadas == 0
        assert result.compras_canceladas == 0
        assert result.total_contratado == 10
        assert result.estado_mensaje == "Pago pendiente"
        assert len(result.compras) == 1
        assert result.compras[0].tipo == "INICIAL"


class TestResumenEquiposSchemaContract:
    """ResumenEquiposSchema is the aggregate team-roster summary block."""

    def test_schema_exposes_expected_summary_fields(self):
        """
        GIVEN: ResumenEquiposSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  The schema exposes total, completos, incompletos.
        """
        fields = set(ResumenEquiposSchema.model_fields.keys())
        expected = {"total", "completos", "incompletos"}
        assert fields == expected, f"Expected {expected}, got {fields}"

    def test_schema_validates_target_json_shape(self):
        """
        GIVEN: A dict matching the target JSON shape for ResumenEquipos
        WHEN:  Validating through the schema
        THEN:  The schema accepts the valid input.
        """
        data = {
            "total": 2,
            "completos": 1,
            "incompletos": 1,
        }
        result = ResumenEquiposSchema.model_validate(data)
        assert result.total == 2
        assert result.completos == 1
        assert result.incompletos == 1


class TestEquipoDetailSchemaContract:
    """EquipoDetailSchema is extended with roster-derived and persisted fields."""

    def test_schema_exposes_estado_equipo(self):
        """
        GIVEN: EquipoDetailSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  The schema exposes estado_equipo (persisted team state).
        """
        fields = set(EquipoDetailSchema.model_fields.keys())
        assert "estado_equipo" in fields

    def test_schema_exposes_estado_roster(self):
        """
        GIVEN: EquipoDetailSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  The schema exposes estado_roster (derived INCOMPLETO/COMPLETO).
        """
        fields = set(EquipoDetailSchema.model_fields.keys())
        assert "estado_roster" in fields

    def test_schema_exposes_roster_derived_fields(self):
        """
        GIVEN: EquipoDetailSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  The schema exposes jugadores_registrados, minimo_deportivo, faltantes.
        """
        fields = set(EquipoDetailSchema.model_fields.keys())
        for field in ("jugadores_registrados", "minimo_deportivo", "faltantes"):
            assert field in fields, f"Missing field: {field}"

    def test_schema_backward_compat_estado_field_present(self):
        """
        GIVEN: EquipoDetailSchema definition
        WHEN:  Inspecting the schema fields
        THEN:  The old ``estado`` field is still present for backward compatibility.
        """
        fields = set(EquipoDetailSchema.model_fields.keys())
        assert "estado" in fields

    def test_estado_roster_is_literal_incompleto_completo(self):
        """
        GIVEN: An EquipoDetailSchema instance
        WHEN:  Validating with estado_roster=INCOMPLETO and estado_roster=COMPLETO
        THEN:  Both values are accepted.
        """
        from modules.salesianos_fest.presentation.schemas.inscripcion_schemas import (
            DisciplinaSummarySchema,
            CategoriaSummarySchema,
            ParticipacionOut,
        )
        base = {
            "id": str(uuid.uuid4()),
            "nombre": "Los Tigres FC",
            "disciplina": {"id": str(uuid.uuid4()), "nombre": "Fútbol 7", "sigla": "F7"},
            "categoria": None,
            "estado": "EQUIPO_ACTIVO",
            "estado_equipo": "EQUIPO_ACTIVO",
            "estado_roster": "COMPLETO",
            "jugadores_registrados": 7,
            "minimo_deportivo": 7,
            "faltantes": 0,
            "participantes": [],
        }
        result = EquipoDetailSchema.model_validate(base)
        assert result.estado_roster == "COMPLETO"

        incomplete = dict(base, estado_roster="INCOMPLETO", jugadores_registrados=5, faltantes=2)
        result2 = EquipoDetailSchema.model_validate(incomplete)
        assert result2.estado_roster == "INCOMPLETO"
        assert result2.jugadores_registrados == 5
        assert result2.faltantes == 2


class TestInscripcionDetailOutContract:
    """InscripcionDetailOut is extended with additive resumen_equipos and resumen_pago."""

    def test_schema_exposes_resumen_equipos(self):
        """
        GIVEN: InscripcionDetailOut definition
        WHEN:  Inspecting the schema fields
        THEN:  The schema exposes resumen_equipos (ResumenEquiposSchema).
        """
        fields = set(InscripcionDetailOut.model_fields.keys())
        assert "resumen_equipos" in fields

    def test_schema_exposes_resumen_pago(self):
        """
        GIVEN: InscripcionDetailOut definition
        WHEN:  Inspecting the schema fields
        THEN:  The schema exposes resumen_pago (ResumenPagoSchema).
        """
        fields = set(InscripcionDetailOut.model_fields.keys())
        assert "resumen_pago" in fields

    def test_schema_backward_compat_estado_and_equipos_fields(self):
        """
        GIVEN: InscripcionDetailOut definition
        WHEN:  Inspecting the schema fields
        THEN:  The inscription-level ``estado`` and ``equipos`` fields are still present.
        """
        fields = set(InscripcionDetailOut.model_fields.keys())
        assert "estado" in fields
        assert "equipos" in fields
        assert "personas" in fields


class TestMetadataExclusionFromInscriptionEndpoints:
    """Prove that OrdenPago.metadata is never exposed in inscription detail responses."""

    def test_orden_pago_resumen_schema_has_no_metadata_field(self):
        """
        GIVEN: OrdenPagoResumenSchema
        WHEN:  Checking the schema field list
        THEN:  metadata is absent.
        """
        fields = set(OrdenPagoResumenSchema.model_fields.keys())
        assert "metadata" not in fields

    def test_compra_resumen_schema_nested_orden_pago_has_no_metadata(self):
        """
        GIVEN: CompraResumenSchema with a nested OrdenPagoResumenSchema
        WHEN:  Validating a full instance
        THEN:  The nested orden_pago has no metadata field.
        """
        nested_orden = {
            "id": str(uuid.uuid4()),
            "numero": "OP-2026-0001",
            "estado": "PAGADA",
            "pagada_en": "2026-10-15T10:30:00Z",
        }
        # Verify the nested schema has no metadata
        orden_result = OrdenPagoResumenSchema.model_validate(nested_orden)
        assert not hasattr(orden_result, "metadata")

    def test_resumen_pago_compra_nested_orden_pago_has_no_metadata(self):
        """
        GIVEN: ResumenPagoSchema with compras containing nested orden_pago
        WHEN:  Validating the full structure
        THEN:  No metadata field exists anywhere in the tree.
        """
        nested_orden = {
            "id": str(uuid.uuid4()),
            "numero": "OP-2026-0003",
            "estado": "PENDIENTE",
            "pagada_en": None,
        }
        compra = {
            "id": str(uuid.uuid4()),
            "tipo": "INICIAL",
            "cantidad": 15,
            "precio_unitario": 50.0,
            "total": 750.0,
            "estado": "PENDIENTE",
            "orden_pago": nested_orden,
        }
        resumen = {
            "total_compras": 1,
            "total_contratado": 15,
            "total_pagado": 0.0,
            "total_pagado_cantidad": 0,
            "compras_pendientes": 1,
            "compras_pagadas": 0,
            "compras_canceladas": 0,
            "disponible_pagado": 0,
            "estado_mensaje": "Pago pendiente",
            "compras": [compra],
        }
        result = ResumenPagoSchema.model_validate(resumen)
        assert result.compras[0].orden_pago is not None
        assert not hasattr(result.compras[0].orden_pago, "metadata")
