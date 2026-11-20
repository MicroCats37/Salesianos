"""Fixtures de los comandos ADMINISTRATIVOS asistidos.

Change: `admin-client-purchases-and-participants`

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3 — las fixtures viven
aquí; el `conftest.py` del módulo sólo las importa y registra.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from modules.eventos.domain.constants import ModuloLogico


@pytest.fixture
def edicion_con_tienda_y_pases(db, edicion_publicada):
    """La edición publicada con los módulos `pases` y `marketplace` activos.

    Sin ellos no hay ni catálogo de pases ni catálogo de tienda: un módulo no
    habilitado no expone catálogo (`RN-E02`).
    """
    modulos = list(edicion_publicada.modulos_habilitados or [])
    for modulo in (ModuloLogico.PASES, ModuloLogico.MARKETPLACE):
        if modulo not in modulos:
            modulos.append(modulo)
    edicion_publicada.modulos_habilitados = modulos
    edicion_publicada.save(update_fields=["modulos_habilitados"])
    return edicion_publicada


@pytest.fixture
def admin_con_persona(db):
    """Una cuenta de ADMINISTRADOR con una persona vinculada.

    La persona del administrador es lo que hace DEMOSTRABLE que una compra
    asistida no se le atribuye: el comprador es el cliente, no esta persona.
    """
    from modules.usuarios.domain.models import Persona, Usuario

    persona_admin = Persona.objects.create(
        nombres="Carla",
        apellidos="Ríos",
        tipo_documento="DNI",
        numero_documento="99999999",
    )

    return Usuario.objects.create_user(
        username="admin.asistido",
        password="Prueba-12345",
        email="admin.asistido@example.com",
        is_staff=True,
        persona_fk=persona_admin,
    )


@pytest.fixture
def admin_sin_persona(db):
    """Una cuenta de ADMINISTRADOR sin persona vinculada."""
    from modules.usuarios.domain.models import Usuario

    return Usuario.objects.create_user(
        username="admin.asistido.sin.persona",
        password="Prueba-12345",
        email="admin.asistido.sin.persona@example.com",
        is_staff=True,
    )


@pytest.fixture
def cliente_externo(db):
    """El CLIENTE de la compra asistida: un tercero del FEST.

    NO tiene cuenta: es una identidad civil, como la de un checkout invitado.
    """
    from modules.usuarios.domain.models import Persona

    return Persona.objects.create(
        nombres="Rosa",
        apellidos="Díaz",
        tipo_documento="DNI",
        numero_documento="77777777",
    )


@pytest.fixture
def categoria_tienda(db, edicion_con_tienda_y_pases):
    """La categoría del producto de la tienda."""
    from modules.marketplace.domain.models import CategoriaProducto

    return CategoriaProducto.objects.create(
        edicion=edicion_con_tienda_y_pases,
        nombre="Bebidas",
        slug="bebidas-asistido",
        orden=1,
    )


@pytest.fixture
def producto_tienda(db, edicion_con_tienda_y_pases, categoria_tienda):
    """Un producto ACTIVO con existencias declaradas."""
    from modules.marketplace.domain.models import Producto

    return Producto.objects.create(
        edicion=edicion_con_tienda_y_pases,
        categoria=categoria_tienda,
        nombre="Agua mineral del FEST",
        slug="agua-mineral-asistido",
        descripcion="Botella de 500 ml.",
        precio="3.50",
        estado="ACTIVO",
        stock=10,
    )


@pytest.fixture
def pase_venta(db, edicion_con_tienda_y_pases):
    """Un pase VIGENTE con su precio vigente."""
    from modules.salesianos_fest.domain.models import Pase, PasePrecio

    pase = Pase.objects.create(
        edicion=edicion_con_tienda_y_pases,
        nombre="Pase FEST",
        slug="pase-fest-asistido",
        descripcion="Entrada general del FEST.",
    )
    PasePrecio.objects.create(
        pase=pase,
        monto=Decimal("35.00"),
        moneda="PEN",
        vigente_desde=date.today() - timedelta(days=1),
    )
    return pase


__all__ = [
    "admin_con_persona",
    "admin_sin_persona",
    "categoria_tienda",
    "cliente_externo",
    "edicion_con_tienda_y_pases",
    "pase_venta",
    "producto_tienda",
]
