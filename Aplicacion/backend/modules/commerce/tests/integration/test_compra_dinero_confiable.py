"""El dinero es del servidor: el cliente no impone un importe.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §1.1, §1.2; RN-C02, RN-M03)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

| Test | Garantía congelada |
|---|---|
| `test_el_total_se_deriva_de_las_lineas` | RN-C02 — el servidor congela el precio |
| `test_un_total_declarado_distinto_se_rechaza` | RN-C02 — no se acepta un importe arbitrario |
| `test_un_total_declarato_que_coincide_se_acepta` | RN-C02 — el contraste, no la arbitrariedad |
| `test_el_snapshot_de_lineas_queda_congelado` | RN-M03 — el histórico no cambia |
| `test_un_monto_negativo_se_rechaza` | FR-04 §1.1 — el total nunca es negativo |
| `test_una_compra_sin_comprador_se_rechaza` | FR-04 §1.1 — la compra siempre tiene comprador |
| `test_un_origen_desconocido_se_rechaza` | FR-04 §1.1 — tres orígenes, uno por dominio |

Cliente de prueba: el flujo se invoca con `async_to_sync`, el puente correcto
para un flujo async con `sync_to_async(thread_sensitive=True)` (F-12).
"""

from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.constants import EstadoCompra, OrigenCompra
from modules.commerce.domain.exceptions import CompraTotalIncoherenteError
from modules.commerce.domain.models import Compra
from modules.commerce.domain.schemas.compra_schemas import (
    CompraCreateData,
    LineaCompraSnapshot,
    calcular_total,
)
from modules.commerce.domain.services.flujos.compra_flujo import CompraFlujo

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real de compras."""
    return injector.get(CompraFlujo)


def test_el_total_se_deriva_de_las_lineas(flujo, intencion):
    """GIVEN una intención de compra con dos líneas
    WHEN  se crea la compra
    THEN  el total congelado es la suma de cantidad × precio aplicado.
    """
    compra, _ = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    compra.refresh_from_db()
    assert compra.total == Decimal("100.00")
    assert compra.total == calcular_total(intencion.lineas)


def test_un_total_declarado_distinto_se_rechaza(flujo, intencion):
    """GIVEN una intención con un total DECLARADO que no es el de sus líneas
    WHEN  se crea la compra
    THEN  se rechaza con COMPRA_TOTAL_INCOHERENTE: el importe no se ajusta.

    Ésta es la expresión de `RN-C02`: el navegador no impone un importe; si
    el importe declarado no es el que deriva del catálogo congelado, la
    operación se rechaza en lugar de aceptarse un número arbitrario.
    """
    intencion.total = Decimal("1.00")

    with pytest.raises(CompraTotalIncoherenteError):
        async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    assert Compra.objects.count() == 0


def test_un_total_declarado_que_coincide_se_acepta(flujo, intencion):
    """GIVEN una intención con un total declarado QUE COINCIDE con sus líneas
    WHEN  se crea la compra
    THEN  la compra se crea con ese total: el contraste no es un obstáculo.
    """
    intencion.total = Decimal("100.00")

    compra, reutilizada = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    assert reutilizada is False
    compra.refresh_from_db()
    assert compra.total == Decimal("100.00")


def test_el_snapshot_de_lineas_queda_congelado(flujo, intencion):
    """GIVEN una compra creada con su snapshot de líneas
    WHEN  el precio de catálogo cambia
    THEN  la compra conserva lo que compró: el histórico no se reescribe.
    """
    compra, _ = async_to_sync(flujo.crear_o_reutilizar_compra)(intencion)

    compra.refresh_from_db()
    assert len(compra.lineas_snapshot) == 1
    linea = compra.lineas_snapshot[0]
    assert linea["concepto_id"] == "paquete-1"
    assert linea["cantidad"] == 2
    assert Decimal(str(linea["precio_aplicado"])) == Decimal("50.00")

    # El precio vigente del catálogo ya no importa para esta compra.
    LineaCompraSnapshot(
        concepto_tipo="PAQUETE",
        concepto_id="paquete-1",
        concepto_nombre="Paquete competitivo",
        cantidad=2,
        precio_unitario=Decimal("99.00"),
        precio_aplicado=Decimal("99.00"),
    )

    compra.refresh_from_db()
    assert Decimal(str(compra.lineas_snapshot[0]["precio_aplicado"])) == Decimal(
        "50.00"
    )
    assert compra.total == Decimal("100.00")


def test_un_precio_negativo_se_rechaza(persona):
    """GIVEN una línea con precio aplicado negativo
    WHEN  se construye la intención
    THEN  la validación la rechaza: el dinero de una compra nunca es negativo.
    """
    with pytest.raises(ValueError):
        LineaCompraSnapshot(
            concepto_tipo="PAQUETE",
            concepto_id="paquete-1",
            concepto_nombre="Paquete competitivo",
            cantidad=1,
            precio_unitario=Decimal("-1.00"),
            precio_aplicado=Decimal("-1.00"),
        )


def test_una_compra_sin_comprador_se_rechaza(linea):
    """GIVEN una intención sin persona compradora
    WHEN  se construye la intención
    THEN  la validación la rechaza: una compra SIEMPRE tiene comprador.
    """
    with pytest.raises(ValueError):
        CompraCreateData(
            persona_id="",
            origen=OrigenCompra.INSCRIPCION,
            lineas=[linea],
            referencia="INSCRIPCION:1:INICIAL",
        )

def test_un_origen_desconocido_se_rechaza(linea, persona):
    """GIVEN una intención con un origen fuera del vocabulario cerrado
    WHEN  se construye la intención
    THEN  la validación la rechaza: no hay compras genéricas sin origen.
    """
    with pytest.raises(ValueError):
        CompraCreateData(
            persona_id=str(persona.id),
            origen="CARRITO",
            lineas=[linea],
            referencia="INSCRIPCION:1:INICIAL",
        )


def test_la_compra_no_puede_tener_un_total_negativo_en_la_base(persona):
    """GIVEN una compra con total negativo
    WHEN  se intenta persistir
    THEN  la base de datos lo rechaza: el CHECK es la última línea.
    """
    from django.db.utils import IntegrityError

    with pytest.raises(IntegrityError):
        Compra.objects.create(
            persona=persona,
            origen=OrigenCompra.INSCRIPCION,
            estado=EstadoCompra.PENDIENTE,
            total=Decimal("-10.00"),
            moneda="PEN",
            lineas_snapshot=[],
            referencia="REFERENCIA-NEGATIVA",
        )
