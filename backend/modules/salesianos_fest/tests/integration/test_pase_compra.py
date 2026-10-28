"""
Integration tests — purchase of independent party passes (Apply 2).

What this file proves:

1. the purchase is ATOMIC: `Compra(PENDIENTE)` + `OrdenPago(PENDIENTE)` +
   `CompraPase` are created together, and nothing is created when the
   purchase is rejected;
2. the price is FROZEN BY THE SERVER: the client never controls the unit
   price nor the total, and the frozen total is consistent everywhere;
3. the availability rules hold: rollout flag, active event, active pass and
   vigente price;
4. the inventory cap is enforced against the NOT cancelled purchases
   (`cantidad_maxima == 0` means unlimited);
5. the purchase is OWNED by the buyer (`Compra.responsable`) and only the
   owner can read it;
6. STRUCTURALLY, a pass purchase creates no sports object: no `Inscripcion`,
   no `CompraInscripcion`, no `AsignacionCupo`, no `Participacion`, no
   `Equipo` and no sports balance.

NOT EXECUTED IN THIS PHASE: the tests are written here and run only once, in
Apply 9 (the consolidated validation of the whole change).
"""
import json
import uuid
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.models import Compra
from modules.pagos.domain.models import OrdenPago
from modules.salesianos_fest.domain.constants import (
    CANTIDAD_MAXIMA_POR_COMPRA,
    EtapaChoices,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    CompraPase,
    Equipo,
    Inscripcion,
    Participacion,
    Pase,
    PasePrecio,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _auth_post(client, path, user, data):
    """POST with a JWT bearer token."""
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _auth_get(client, path, user):
    """GET with a JWT bearer token."""
    token = AccessToken.for_user(user)
    return client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")


def _contar_objetos_deportivos():
    """Snapshot of every sports object a pass purchase must NOT touch."""
    return {
        "inscripcion": Inscripcion.objects.count(),
        "compra_inscripcion": CompraInscripcion.objects.count(),
        "asignacion_cupo": AsignacionCupo.objects.count(),
        "participacion": Participacion.objects.count(),
        "equipo": Equipo.objects.count(),
    }


# ── Creación atómica ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_comprar_pases_crea_compra_orden_y_linea(
    api_client, usuario_comprador, pase_fiesta, settings
):
    """
    GIVEN: el flag habilitado y un pase activo con precio vigente
    WHEN:  POST /api/pases/comprar con 2 unidades
    THEN:  200 y se crean atómicamente Compra(PENDIENTE), OrdenPago(PENDIENTE)
           y CompraPase, con el comprador como responsable
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_fiesta.id), "cantidad": 2},
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["cantidad"] == 2
    assert data["estado_compra"] == "PENDIENTE"
    assert data["estado_orden"] == "PENDIENTE"

    compra = Compra.objects.get(id=data["compra_id"])
    orden = OrdenPago.objects.get(id=data["orden_pago_id"])
    linea = CompraPase.objects.get(compra_id=data["compra_id"])

    assert compra.estado == "PENDIENTE"
    assert str(compra.responsable_id) == str(usuario_comprador.persona_fk_id)
    assert orden.estado == "PENDIENTE"
    assert orden.numero == data["numero_orden"]
    assert linea.compra_id == compra.id
    assert linea.pase_id == pase_fiesta.id
    assert linea.evento_id == pase_fiesta.evento_id
    assert linea.cantidad == 2


@pytest.mark.django_db
def test_comprar_pases_congela_el_precio_del_servidor(
    api_client, usuario_comprador, pase_fiesta, settings
):
    """
    GIVEN: el cliente intenta mandar su propio precio y su propio total
    WHEN:  POST /api/pases/comprar
    THEN:  el precio y el total congelados son los del SERVIDOR
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {
            "pase_id": str(pase_fiesta.id),
            "cantidad": 2,
            "precio_unitario": 0.01,
            "total": 0.02,
        },
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["precio_unitario"] == 25.0
    assert data["total"] == 50.0

    linea = CompraPase.objects.get(compra_id=data["compra_id"])
    assert linea.precio_unitario == Decimal("25.00")
    assert linea.total == Decimal("50.00")


@pytest.mark.django_db
def test_comprar_pases_total_consistente_en_todas_las_filas(
    api_client, usuario_comprador, pase_fiesta, settings
):
    """
    GIVEN: una compra de 3 pases
    WHEN:  se inspeccionan Compra, CompraPase y OrdenPago
    THEN:  los tres totales coinciden y son cantidad * precio_unitario
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_fiesta.id), "cantidad": 3},
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]

    compra = Compra.objects.get(id=data["compra_id"])
    linea = CompraPase.objects.get(compra_id=data["compra_id"])
    orden = OrdenPago.objects.get(id=data["orden_pago_id"])

    esperado = Decimal("25.00") * 3
    assert linea.precio_unitario == Decimal("25.00")
    assert linea.total == esperado
    assert compra.total == esperado
    assert orden.monto_total == esperado
    assert orden.moneda == "PEN"


@pytest.mark.django_db
def test_comprar_pases_no_crea_ningun_objeto_deportivo(
    api_client, usuario_comprador, pase_fiesta, settings
):
    """
    GIVEN: una compra de pases
    WHEN:  se comparan los conteos de objetos deportivos antes y después
    THEN:  no se crea ni se modifica ningún objeto deportivo
    """
    settings.PASES_FIESTA_ENABLED = True
    antes = _contar_objetos_deportivos()

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_fiesta.id), "cantidad": 2},
    )

    assert response.status_code == 200, response.content
    assert _contar_objetos_deportivos() == antes
    assert Inscripcion.objects.count() == 0
    assert CompraInscripcion.objects.count() == 0
    assert AsignacionCupo.objects.count() == 0
    assert Participacion.objects.count() == 0
    assert Equipo.objects.count() == 0


# ── Disponibilidad ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_comprar_pases_rechazado_con_flag_deshabilitado(
    api_client, usuario_comprador, pase_fiesta, settings
):
    """
    GIVEN: el flag de despliegue está DESHABILITADO
    WHEN:  POST /api/pases/comprar
    THEN:  409 con el código estable y NINGUNA fila comercial creada
    """
    settings.PASES_FIESTA_ENABLED = False

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_fiesta.id), "cantidad": 1},
    )

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "PASES_FIESTA_DESHABILITADO"
    assert Compra.objects.count() == 0
    assert OrdenPago.objects.count() == 0
    assert CompraPase.objects.count() == 0


@pytest.mark.django_db
def test_comprar_pases_rechazado_si_el_pase_esta_inactivo(
    api_client, usuario_comprador, pase_inactivo, settings
):
    """
    GIVEN: un pase INACTIVO
    WHEN:  POST /api/pases/comprar
    THEN:  409 PASE_NO_DISPONIBLE y ninguna fila comercial creada
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_inactivo.id), "cantidad": 1},
    )

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "PASE_NO_DISPONIBLE"
    assert Compra.objects.count() == 0
    assert CompraPase.objects.count() == 0


@pytest.mark.django_db
def test_comprar_pases_rechazado_si_el_pase_no_es_de_la_edicion_activa(
    api_client, usuario_comprador, evento, pase_de_edicion_inactiva, settings
):
    """
    GIVEN: un pase activo de una edición que NO es la activa
    WHEN:  POST /api/pases/comprar
    THEN:  409 PASE_NO_DISPONIBLE y ninguna fila comercial creada
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_de_edicion_inactiva.id), "cantidad": 1},
    )

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "PASE_NO_DISPONIBLE"
    assert Compra.objects.count() == 0
    assert CompraPase.objects.count() == 0


@pytest.mark.django_db
def test_comprar_pases_rechazado_sin_precio_vigente(
    api_client, usuario_comprador, pase_precios_fuera_de_ventana, settings
):
    """
    GIVEN: un pase activo cuyos dos precios están fuera de su ventana
    WHEN:  POST /api/pases/comprar
    THEN:  409 PASE_PRECIO_NO_VIGENTE y ninguna fila comercial creada
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_precios_fuera_de_ventana.id), "cantidad": 1},
    )

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "PASE_PRECIO_NO_VIGENTE"
    assert Compra.objects.count() == 0
    assert CompraPase.objects.count() == 0


@pytest.mark.django_db
def test_comprar_pases_rechazado_con_cantidad_no_positiva(
    api_client, usuario_comprador, pase_fiesta, settings
):
    """
    GIVEN: una cantidad NO positiva
    WHEN:  POST /api/pases/comprar
    THEN:  se rechaza y ninguna fila comercial creada
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_fiesta.id), "cantidad": 0},
    )

    assert response.status_code == 422, response.content
    assert Compra.objects.count() == 0
    assert CompraPase.objects.count() == 0


@pytest.mark.django_db
def test_comprar_pases_rechazado_con_cantidad_sobre_el_tope(
    api_client, usuario_comprador, pase_fiesta, settings
):
    """
    GIVEN: una cantidad por encima del tope comercial por compra
    WHEN:  POST /api/pases/comprar
    THEN:  422 PASE_CANTIDAD_INVALIDA y ninguna fila comercial creada
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_fiesta.id), "cantidad": CANTIDAD_MAXIMA_POR_COMPRA + 1},
    )

    assert response.status_code == 422, response.content
    assert response.json()["error"]["code"] == "PASE_CANTIDAD_INVALIDA"
    assert Compra.objects.count() == 0
    assert CompraPase.objects.count() == 0


@pytest.mark.django_db
def test_comprar_pases_rechazado_por_inventario_agotado(
    api_client, usuario_comprador, pase_con_inventario_limitado, settings
):
    """
    GIVEN: un pase con inventario máximo 5
    WHEN:  se piden 6 unidades
    THEN:  409 PASE_INVENTARIO_AGOTADO y ninguna fila comercial creada
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_con_inventario_limitado.id), "cantidad": 6},
    )

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "PASE_INVENTARIO_AGOTADO"
    assert Compra.objects.count() == 0
    assert CompraPase.objects.count() == 0


@pytest.mark.django_db
def test_comprar_pases_el_inventario_acumula_entre_compras(
    api_client, usuario_comprador, pase_con_inventario_limitado, settings
):
    """
    GIVEN: un pase con inventario máximo 5
    WHEN:  se compran 3 unidades y luego se piden 3 más
    THEN:  la segunda compra se rechaza (3 + 3 > 5) y la primera sigue viva
    """
    settings.PASES_FIESTA_ENABLED = True

    primera = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_con_inventario_limitado.id), "cantidad": 3},
    )
    assert primera.status_code == 200, primera.content

    segunda = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_con_inventario_limitado.id), "cantidad": 3},
    )

    assert segunda.status_code == 409, segunda.content
    assert segunda.json()["error"]["code"] == "PASE_INVENTARIO_AGOTADO"
    assert Compra.objects.count() == 1
    assert CompraPase.objects.count() == 1


@pytest.mark.django_db
def test_comprar_pases_pase_sin_limite_acepta_el_lote(
    api_client, usuario_comprador, pase_fiesta, settings
):
    """
    GIVEN: un pase con cantidad_maxima = 0 (sin límite)
    WHEN:  se compran 25 unidades
    THEN:  la compra se acepta
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_fiesta.id), "cantidad": 25},
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["cantidad"] == 25
    assert response.json()["data"]["total"] == 625.0


# ── Autenticación y ownership ────────────────────────────────────────────────


@pytest.mark.django_db
def test_comprar_pases_requiere_autenticacion(api_client, pase_fiesta, settings):
    """
    GIVEN: un llamante anónimo
    WHEN:  POST /api/pases/comprar
    THEN:  401 AUTHENTICATION_REQUIRED y ninguna fila comercial creada
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.post(
        "/api/pases/comprar",
        data=json.dumps({"pase_id": str(pase_fiesta.id), "cantidad": 1}),
        content_type="application/json",
    )

    assert response.status_code == 401, response.content
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert Compra.objects.count() == 0


@pytest.mark.django_db
def test_obtener_compra_pase_devuelve_estado_y_valores_congelados(
    api_client, usuario_comprador, pase_fiesta, settings
):
    """
    GIVEN: una compra de pases del comprador
    WHEN:  GET /api/pases/compras/{compra_id}
    THEN:  200 con el estado de compra y orden, los valores congelados y los
           conteos de beneficiarios (0 asignados, todo pendiente)
    """
    settings.PASES_FIESTA_ENABLED = True

    creada = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_fiesta.id), "cantidad": 3},
    )
    assert creada.status_code == 200, creada.content
    compra_id = creada.json()["data"]["compra_id"]

    response = _auth_get(
        api_client, f"/api/pases/compras/{compra_id}", usuario_comprador
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["compra_id"] == compra_id
    assert data["pase_id"] == str(pase_fiesta.id)
    assert data["pase_nombre"] == "Pase de Fiesta"
    assert data["cantidad"] == 3
    assert data["precio_unitario"] == 25.0
    assert data["total"] == 75.0
    assert data["estado_compra"] == "PENDIENTE"
    assert data["estado_orden"] == "PENDIENTE"
    assert data["moneda"] == "PEN"
    assert data["orden_pago_id"] == creada.json()["data"]["orden_pago_id"]
    assert data["numero_orden"] == creada.json()["data"]["numero_orden"]
    assert data["beneficiarios_asignados"] == 0
    assert data["beneficiarios_pendientes"] == 3


@pytest.mark.django_db
def test_obtener_compra_pase_de_otro_comprador_responde_403(
    api_client, usuario_comprador, usuario_ajeno, pase_fiesta, settings
):
    """
    GIVEN: una compra de pases de OTRO comprador
    WHEN:  GET /api/pases/compras/{compra_id}
    THEN:  403 PASE_COMPRA_NO_AUTORIZADA
    """
    settings.PASES_FIESTA_ENABLED = True

    creada = _auth_post(
        api_client,
        "/api/pases/comprar",
        usuario_comprador,
        {"pase_id": str(pase_fiesta.id), "cantidad": 1},
    )
    assert creada.status_code == 200, creada.content
    compra_id = creada.json()["data"]["compra_id"]

    response = _auth_get(
        api_client, f"/api/pases/compras/{compra_id}", usuario_ajeno
    )

    assert response.status_code == 403, response.content
    assert response.json()["error"]["code"] == "PASE_COMPRA_NO_AUTORIZADA"


@pytest.mark.django_db
def test_obtener_compra_pase_inexistente_responde_404(
    api_client, usuario_comprador, settings
):
    """
    GIVEN: una compra que no existe
    WHEN:  GET /api/pases/compras/{compra_id}
    THEN:  404 PASE_COMPRA_NO_ENCONTRADA
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_get(
        api_client, f"/api/pases/compras/{uuid.uuid4()}", usuario_comprador
    )

    assert response.status_code == 404, response.content
    assert response.json()["error"]["code"] == "PASE_COMPRA_NO_ENCONTRADA"


# ── Seed: no deshace la configuración del operador ───────────────────────────


@pytest.mark.django_db
def test_seed_no_desactiva_un_pase_activado_ni_sobrescribe_precios():
    """
    GIVEN: el seed ejecutado y un operador que activa el pase y ajusta el
           precio de preventa
    WHEN:  el seed se vuelve a ejecutar
    THEN:  el pase sigue activo y el precio ajustado NO se sobreescribe
    """
    call_command("seed_catalogo_fest", stdout=StringIO())

    pase = Pase.objects.get(
        evento__nombre="Salesianos FEST 2026", nombre="Pase de Fiesta"
    )
    pase.activo = True
    pase.save(update_fields=["activo", "updated_at"])

    precio = PasePrecio.objects.get(pase=pase, etapa=EtapaChoices.PREVENTA)
    precio.precio_unitario = Decimal("99.00")
    precio.activo = True
    precio.save(update_fields=["precio_unitario", "activo", "updated_at"])

    call_command("seed_catalogo_fest", stdout=StringIO())

    pase.refresh_from_db()
    precio.refresh_from_db()
    assert pase.activo is True
    assert precio.activo is True
    assert precio.precio_unitario == Decimal("99.00")
    assert PasePrecio.objects.filter(pase=pase).count() == 2
