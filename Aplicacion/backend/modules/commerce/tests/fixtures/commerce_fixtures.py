"""Fixtures y helpers de prueba del módulo `commerce`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3
"""

from decimal import Decimal

import pytest

from modules.commerce.domain.constants import OrigenCompra
from modules.commerce.domain.schemas.compra_schemas import (
    CompraCreateData,
    LineaCompraSnapshot,
)
from modules.usuarios.domain.models import Persona


@pytest.fixture
def persona(db):
    """La persona compradora."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Quispe",
        tipo_documento="DNI",
        numero_documento="11111111",
    )


@pytest.fixture
def otra_persona(db):
    """Una segunda persona, para comprobar que la compra es del comprador."""
    return Persona.objects.create(
        nombres="Luis",
        apellidos="Ramos",
        tipo_documento="DNI",
        numero_documento="22222222",
    )


@pytest.fixture
def linea(db):
    """Una línea de compra: un paquete a 100.00 PEN."""
    return LineaCompraSnapshot(
        concepto_tipo="PAQUETE",
        concepto_id="paquete-1",
        concepto_nombre="Paquete competitivo",
        cantidad=2,
        precio_unitario=Decimal("50.00"),
        precio_aplicado=Decimal("50.00"),
    )


@pytest.fixture
def intencion(linea, persona):
    """La intención de compra de una persona, con su referencia."""
    return CompraCreateData(
        persona_id=persona.id,
        origen=OrigenCompra.INSCRIPCION,
        lineas=[linea],
        referencia="INSCRIPCION:1:INICIAL",
    )


@pytest.fixture(scope="session")
def injector():
    """El inyector de dependencias del paquete FND-04."""
    from injector import Injector

    from modules.commerce.di import CommerceModule
    from modules.pagos.di import PagosModule

    return Injector([CommerceModule, PagosModule])


__all__ = [
    "intencion",
    "linea",
    "otra_persona",
    "persona",
]
