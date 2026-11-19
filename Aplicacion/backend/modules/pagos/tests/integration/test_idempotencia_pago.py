"""La clave de idempotencia del borde HTTP.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.2)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

| Aspecto | Regla congelada |
|---|---|
| Transporte | Header `Idempotency-Key` (opaca, ≤ 128 caracteres) |
| Ámbito | Por endpoint + actor |
| Repetición | El MISMO resultado, con el status de la primera ejecución. Nunca 500 |
| Conflicto | Misma clave con otro payload → 409 `IDEMPOTENCY_KEY_REUTILIZADA` |
"""

import pytest

from modules.pagos.domain.exceptions import (
    IdempotencyKeyInvalidaError,
    IdempotencyKeyReutilizadaError,
)
from modules.pagos.domain.models import RegistroIdempotencia
from modules.pagos.domain.services.core.idempotencia_pago_service import (
    IdempotenciaPagoService,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def servicio():
    """El servicio real de idempotencia."""
    return IdempotenciaPagoService()


def test_una_clave_valida_se_acepta(servicio):
    """GIVEN una clave con la forma admitida
    WHEN  se normaliza
    THEN  se devuelve tal cual.
    """
    clave = "8f14e45f-ceea-467a-9b0a-1c2d3e4f5a6b"
    assert servicio.normalizar_clave(clave) == clave


def test_una_clave_vacia_significa_que_no_hay_idempotencia(servicio):
    """GIVEN que no llega clave
    WHEN  se normaliza
    THEN  se devuelve una cadena vacía: la operación no es idempotente, pero
          tampoco es un error.
    """
    assert servicio.normalizar_clave(None) == ""
    assert servicio.normalizar_clave("   ") == ""


def test_una_clave_demasiado_larga_se_rechaza(servicio):
    """GIVEN una clave de más de 128 caracteres
    WHEN  se normaliza
    THEN  se rechaza con IDEMPOTENCY_KEY_INVALIDA.
    """
    with pytest.raises(IdempotencyKeyInvalidaError):
        servicio.normalizar_clave("a" * 129)


def test_una_clave_con_caracteres_no_admitidos_se_rechaza(servicio):
    """GIVEN una clave con caracteres fuera del alfabeto admitido
    WHEN  se normaliza
    THEN  se rechaza con IDEMPOTENCY_KEY_INVALIDA.
    """
    with pytest.raises(IdempotencyKeyInvalidaError):
        servicio.normalizar_clave("clave con espacios y acentos áé")


def test_la_huella_no_guarda_el_payload(servicio):
    """GIVEN una petición con datos sensibles
    WHEN  se calcula su huella
    THEN  la huella es un resumen: el payload no queda en la base de datos.
    """
    peticion = {"monto": "100.00", "correo": "comprador@example.com"}
    huella = servicio.huella(peticion)

    assert len(huella) == 64
    assert "correo" not in huella
    assert "example.com" not in huella


def test_la_misma_peticion_produce_la_misma_huella(servicio):
    """GIVEN el mismo contenido en distinto orden
    WHEN  se calculan las huellas
    THEN  son iguales: la normalización es estable.
    """
    primero = servicio.huella({"a": 1, "b": 2})
    segundo = servicio.huella({"b": 2, "a": 1})
    assert primero == segundo


def test_la_repeticion_devuelve_el_registro_previo(servicio):
    """GIVEN una clave ya registrada con la misma huella
    WHEN  se registra otra vez
    THEN  se devuelve el registro previo y se marca como repetición.
    """
    huella = servicio.huella({"x": 1})
    registro, repetida = servicio.registrar(
        ambito="pagos:confirmar:1",
        clave="clave-de-prueba-1234",
        huella=huella,
    )
    assert repetida is False

    repetido, repetida_2 = servicio.registrar(
        ambito="pagos:confirmar:1",
        clave="clave-de-prueba-1234",
        huella=huella,
    )
    assert repetida_2 is True
    assert repetido.id == registro.id


def test_la_misma_clave_con_otra_huella_es_un_conflicto(servicio):
    """GIVEN una clave ya registrada con OTRA huella
    WHEN  se registra otra vez
    THEN  se lanza IDEMPOTENCY_KEY_REUTILIZADA.
    """
    servicio.registrar(
        ambito="pagos:confirmar:1",
        clave="clave-de-prueba-1234",
        huella=servicio.huella({"x": 1}),
    )

    with pytest.raises(IdempotencyKeyReutilizadaError):
        servicio.registrar(
            ambito="pagos:confirmar:1",
            clave="clave-de-prueba-1234",
            huella=servicio.huella({"x": 2}),
        )


def test_la_misma_clave_en_otro_ambito_es_otra_operacion(servicio):
    """GIVEN una clave usada en un ámbito
    WHEN  se usa en otro ámbito
    THEN  es otra operación: el ámbito es endpoint + actor.
    """
    huella = servicio.huella({"x": 1})
    servicio.registrar(
        ambito="pagos:confirmar:1",
        clave="clave-de-prueba-1234",
        huella=huella,
    )

    registro, repetida = servicio.registrar(
        ambito="pagos:confirmar:2",
        clave="clave-de-prueba-1234",
        huella=huella,
    )
    assert repetida is False
    assert registro.ambito == "pagos:confirmar:2"


def test_la_respuesta_registrada_se_conserva(servicio):
    """GIVEN una operación registrada con su respuesta
    WHEN  se relee el registro
    THEN  la respuesta es la de la primera ejecución.
    """
    registro, _ = servicio.registrar(
        ambito="pagos:confirmar:1",
        clave="clave-de-prueba-1234",
        huella=servicio.huella({"x": 1}),
    )
    servicio.actualizar_respuesta(
        registro,
        respuesta={"orden_pago_id": "abc", "monto": "100.00"},
        codigo_estado=200,
    )

    releido = servicio.obtener("pagos:confirmar:1", "clave-de-prueba-1234")
    assert releido.respuesta["orden_pago_id"] == "abc"
    assert releido.codigo_estado == 200
    assert RegistroIdempotencia.objects.count() == 1
