"""La prueba de redacción de secretos: lo que NUNCA se persiste ni se registra.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §3) · `contratos/03` §8 (Seguridad operativa)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Reglas congeladas que estos tests demuestran:

- La clave del comercio es un **secreto**: se lee de los settings, no sale del
  servidor y no se escribe en ninguna fila, ninguna evidencia ni ningún log.
- El payload del proveedor se **sanea** antes de persistirse: ni datos de
  tarjeta, ni tokens de sesión, ni la firma, ni el payload firmado.
- La evidencia pública del pago contiene **hechos**, no credenciales.
"""

import json
import logging

import pytest
from asgiref.sync import async_to_sync

from modules.pagos.domain.services.core.idempotencia_pago_service import (
    IdempotenciaPagoService,
)
from modules.pagos.domain.services.flujos.pago_confirmacion_flujo import (
    PagoConfirmacionFlujo,
)
from modules.pagos.infrastructure.services import (
    ProveedorPagoIzipayAdapter,
    sanitizar_payload_proveedor,
)
from modules.pagos.tests.fixtures.pagos_fixtures import (
    CLAVE_COMERCIO_PRUEBA,
    firmar,
    payload_confirmacion,
    payload_http,
)

pytestmark = pytest.mark.django_db


# ── El saneado del payload ─────────────────────────────────────────────────


def test_el_payload_saneado_no_conserva_datos_de_tarjeta():
    """GIVEN un payload con datos de tarjeta
    WHEN  se sanea
    THEN  ninguno de los campos sensibles sobrevive.
    """
    payload = {
        "code": "00",
        "transactionId": "10000000000001",
        "cardNumber": "4111111111111111",
        "cardAlias": "alias-de-tarjeta",
        "cvv": "123",
        "cardHolderName": "ANA QUISPE",
        "eci": "05",
        "xid": "xid-de-3ds",
    }

    saneado = sanitizar_payload_proveedor(payload)

    assert saneado["code"] == "00"
    assert saneado["transactionId"] == "10000000000001"
    for prohibido in (
        "cardNumber",
        "cardAlias",
        "cvv",
        "cardHolderName",
        "eci",
        "xid",
    ):
        assert prohibido not in saneado


def test_el_payload_saneado_no_conserva_la_firma_ni_el_payload_firmado():
    """GIVEN un payload con la firma y el texto firmado
    WHEN  se sanea
    THEN  ninguno de los dos sobrevive.
    """
    payload = {
        "signature": "firma-en-base64",
        "payloadHttp": "{\"code\":\"00\"}",
        "keyHash": CLAVE_COMERCIO_PRUEBA,
        "sessionToken": "token-de-sesion",
    }

    saneado = sanitizar_payload_proveedor(payload)

    assert saneado == {}


def test_el_payload_saneado_recorre_las_estructuras_anidadas():
    """GIVEN un payload con datos sensibles anidados
    WHEN  se sanea
    THEN  los anidados también se limpian.
    """
    payload = {
        "response": {
            "order": [{"cardNumber": "4111111111111111", "status": "APPROVED"}],
            "authToken": "token",
        }
    }

    saneado = sanitizar_payload_proveedor(payload)

    assert "cardNumber" not in json.dumps(saneado)
    assert "authToken" not in json.dumps(saneado)
    assert saneado["response"]["order"][0]["status"] == "APPROVED"


def test_un_payload_que_no_es_diccionario_no_rompe_nada():
    """GIVEN un payload que no es un diccionario
    WHEN  se sanea
    THEN  se devuelve un diccionario vacío y no se lanza ninguna excepción.
    """
    assert sanitizar_payload_proveedor(None) == {}
    assert sanitizar_payload_proveedor("texto") == {}
    assert sanitizar_payload_proveedor([1, 2, 3]) == {}


# ── La clave del comercio ──────────────────────────────────────────────────


def test_la_clave_del_comercio_se_lee_de_los_settings(settings):
    """GIVEN la clave configurada en el entorno
    WHEN  se consulta el verificador
    THEN  está disponible y la firma verifica.
    """
    settings.IZIPAY_KEY_HASH = CLAVE_COMERCIO_PRUEBA
    verificador = ProveedorPagoIzipayAdapter()

    assert verificador.disponible is True
    crudo = '{"code":"00"}'
    assert verificador.verificar_firma(crudo, firmar(crudo, CLAVE_COMERCIO_PRUEBA))
    assert not verificador.verificar_firma(crudo, "otra-firma")


def test_sin_clave_del_comercio_la_verificacion_no_esta_disponible(settings):
    """GIVEN un entorno SIN clave del comercio
    WHEN  se verifica una firma
    THEN  el resultado es SIEMPRE falso: no hay fallback.
    """
    settings.IZIPAY_KEY_HASH = ""
    verificador = ProveedorPagoIzipayAdapter()

    assert verificador.disponible is False
    crudo = '{"code":"00"}'
    assert not verificador.verificar_firma(crudo, firmar(crudo, CLAVE_COMERCIO_PRUEBA))


def test_la_clave_del_comercio_no_aparece_en_la_evidencia_del_pago(
    injector, orden_pago, compra, intento, persona, clave_comercio, caplog
):
    """GIVEN un pago confirmado con evidencia
    WHEN  se inspecciona la evidencia, el metadata y los logs
    THEN  la clave del comercio no aparece en ninguno de ellos.
    """
    flujo = injector.get(PagoConfirmacionFlujo)
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    with caplog.at_level(logging.DEBUG):
        async_to_sync(flujo.confirmar_desde_navegador)(
            orden_pago_id=str(orden_pago.id),
            payload={
                **payload,
                "payloadHttp": crudo,
                "signature": firmar(crudo, clave_comercio),
            },
            persona_id=str(persona.id),
        )

    intento.refresh_from_db()
    evidencia = json.dumps(intento.evidencia)
    metadata = json.dumps(intento.metadata)

    assert clave_comercio not in evidencia
    assert clave_comercio not in metadata
    assert clave_comercio not in caplog.text
    # La firma del proveedor tampoco se persiste.
    assert "signature" not in metadata
    assert clave_comercio not in json.dumps(intento.__dict__, default=str)


def test_el_registro_de_idempotencia_no_guarda_el_payload(injector):
    """GIVEN una operación idempotente
    WHEN  se registra su huella
    THEN  el registro guarda la huella, no el contenido de la petición.
    """
    servicio = injector.get(IdempotenciaPagoService)
    peticion = {"correo": "comprador@example.com", "documento": "11111111"}

    registro, _ = servicio.registrar(
        ambito="pagos:confirmar:1",
        clave="clave-de-prueba-1234",
        huella=servicio.huella(peticion),
    )

    assert "example.com" not in json.dumps(registro.respuesta)
    assert "11111111" not in json.dumps(registro.respuesta)
    assert len(registro.huella) == 64
