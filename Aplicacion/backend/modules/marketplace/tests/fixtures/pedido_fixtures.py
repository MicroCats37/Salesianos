"""Fixtures del pedido de marketplace (`DOM-05`).

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3

Las fixtures viven aquí; `modules/marketplace/tests/conftest.py` sólo las
importa y registra. No hay mocks: los dobles son implementaciones reales de
los puertos y los servicios son los de producción.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from modules.marketplace.domain.models import Producto
from modules.marketplace.tests.fixtures.marketplace_fixtures import STOCK_EJEMPLO


# ── Identidad ───────────────────────────────────────────────────────────────


@pytest.fixture
def persona_compradora(db):
    """La `Persona` que compra: está VINCULADA a una cuenta."""
    from modules.usuarios.domain.models import Persona

    return Persona.objects.create(
        tipo_documento="DNI",
        numero_documento="70123456",
        nombres="ANA",
        apellidos="COMPRADORA",
        genero="F",
    )


@pytest.fixture
def usuario_comprador(db, persona_compradora):
    """La cuenta autenticada del comprador."""
    from modules.usuarios.domain.models import Usuario

    return Usuario.objects.create_user(
        username="ana.compradora",
        password="Prueba-12345",
        email="ana.compradora@example.com",
        persona_fk=persona_compradora,
    )


@pytest.fixture
def usuario_ajeno(db):
    """Otra cuenta autenticada, con su propia persona: NO es el comprador."""
    from modules.usuarios.domain.models import Persona, Usuario

    persona = Persona.objects.create(
        tipo_documento="DNI",
        numero_documento="70987654",
        nombres="CARLOS",
        apellidos="AJENO",
        genero="M",
    )
    return Usuario.objects.create_user(
        username="carlos.ajeno",
        password="Prueba-12345",
        email="carlos.ajeno@example.com",
        persona_fk=persona,
    )


@pytest.fixture
def usuario_sin_persona(db):
    """Una cuenta autenticada SIN `Persona` vinculada.

    Es una cuenta técnica: puede entrar, pero NO puede comprar, porque el
    comprador es la `Persona` de la cuenta (`Compra.persona` es obligatorio).
    """
    from modules.usuarios.domain.models import Usuario

    return Usuario.objects.create_user(
        username="cuenta.tecnica",
        password="Prueba-12345",
        email="cuenta.tecnica@example.com",
    )


@pytest.fixture
def token_comprador(usuario_comprador):
    """Token JWT de la cuenta compradora."""
    from ninja_jwt.tokens import AccessToken

    return AccessToken.for_user(usuario_comprador)


@pytest.fixture
def token_ajeno(usuario_ajeno):
    """Token JWT de la cuenta ajena."""
    from ninja_jwt.tokens import AccessToken

    return AccessToken.for_user(usuario_ajeno)


# ── Catálogo ────────────────────────────────────────────────────────────────


@pytest.fixture
def edicion_ajena(db):
    """Una edición de OTRO evento, en BORRADOR.

    NO puede ser `PUBLICADA`: la resolución de alcance (FR-02 §2.2, nivel 3)
    exige una única edición publicada, y dos publicadas la volverían ambigua.
    """
    from modules.eventos.domain.constants import EstadoEdicion
    from modules.eventos.domain.models import Edicion, Evento

    otro_evento = Evento.objects.create(nombre="Otro FEST", slug="otro-fest-pedido")
    return Edicion.objects.create(
        evento=otro_evento,
        nombre="Otro FEST 2027",
        slug="2027",
        anio=2027,
        estado=EstadoEdicion.BORRADOR,
        modulos_habilitados=["marketplace"],
    )


@pytest.fixture
def producto_con_oferta(db, edicion_publicada, categoria_producto):
    """Producto con oferta VIGENTE: el precio efectivo es el de oferta.

    Declara existencias (`DOM-06`): sin `stock` el producto está AGOTADO y no
    se puede pedir (`RN-M06`).
    """
    return Producto.objects.create(
        edicion=edicion_publicada,
        categoria=categoria_producto,
        nombre="Polo del festival",
        slug="polo-festival",
        descripcion="Polo oficial.",
        precio="10.00",
        precio_oferta="7.00",
        oferta_inicia=timezone.now() - timedelta(days=1),
        oferta_termina=timezone.now() + timedelta(days=1),
        estado="ACTIVO",
        stock=STOCK_EJEMPLO,
    )


@pytest.fixture
def producto_inactivo(db, edicion_publicada, categoria_producto):
    """Producto `INACTIVO`: no se puede pedir."""
    return Producto.objects.create(
        edicion=edicion_publicada,
        categoria=categoria_producto,
        nombre="Producto retirado",
        slug="producto-retirado",
        precio="5.00",
        estado="INACTIVO",
    )


@pytest.fixture
def edicion_publicada_sin_tienda(db):
    """Una edición `PUBLICADA` con el módulo `marketplace` DESHABILITADO.

    Vive en su PROPIO evento a propósito: la resolución de alcance (FR-02
    §2.2, nivel 3) exige una única edición publicada, así que esta fixture NO
    puede convivir con `edicion_publicada` en el mismo test (dos publicadas
    la volverían ambigua y el rechazo sería `EDICION_AMBIGUA`, no
    `MODULO_NO_HABILITADO`).
    """
    from modules.eventos.domain.constants import EstadoEdicion
    from modules.eventos.domain.models import Edicion, Evento

    evento = Evento.objects.create(nombre="FEST sin tienda", slug="fest-sin-tienda")
    return Edicion.objects.create(
        evento=evento,
        nombre="FEST sin tienda 2026",
        slug="2026",
        anio=2026,
        estado=EstadoEdicion.PUBLICADA,
        modulos_habilitados=["pases"],
    )


@pytest.fixture
def producto_ajeno(db, edicion_ajena):
    """Producto de OTRA edición: no es coherente con el alcance del pedido."""
    return Producto.objects.create(
        edicion=edicion_ajena,
        nombre="Producto ajeno",
        slug="producto-ajeno",
        precio="9.00",
        estado="ACTIVO",
    )


# ── Grafo de servicios ──────────────────────────────────────────────────────


@pytest.fixture
def pedido_orchestrator(db):
    """El orquestador del pedido, resuelto por el INYECTOR de producción.

    Es el MISMO wiring que usa la HTTP: `MarketplaceModule` registra los
    puertos (`IAlcanceEdicion`, `ICommerceMarketplaceService`,
    `ITitularidadActorService`) y sus adaptadores. Resolverlo por el inyector
    verifica el DI, no sólo el comportamiento.
    """
    from ninja_extra.dependency_resolver import service_resolver

    from modules.marketplace.domain.services.orchestrators.pedido_orchestrator import (
        PedidoOrchestrator,
    )

    return service_resolver(PedidoOrchestrator)


__all__ = [
    "edicion_ajena",
    "edicion_publicada_sin_tienda",
    "pedido_orchestrator",
    "persona_compradora",
    "producto_ajeno",
    "producto_con_oferta",
    "producto_inactivo",
    "token_ajeno",
    "token_comprador",
    "usuario_ajeno",
    "usuario_comprador",
    "usuario_sin_persona",
]
