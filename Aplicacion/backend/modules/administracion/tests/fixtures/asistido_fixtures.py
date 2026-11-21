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


@pytest.fixture
def equipo_disciplina_femenina(db, inscripcion, categoria):
    """Un equipo de una disciplina FEMENINA.

    La modalidad exige un género DECLARADO: sin género conocido no se
    concede el beneficio de la duda (`PoolFlujo._genero_compatible`).
    """
    from modules.salesianos_fest.domain.constants import ModalidadDisciplina
    from modules.salesianos_fest.domain.models import (
        Disciplina,
        Equipo,
        PaqueteDisciplina,
    )

    disciplina = Disciplina.objects.create(
        edicion_id=inscripcion.edicion_id,
        nombre="Vóley Femenino Asistido",
        slug="voley-femenino-asistido",
        modalidad=ModalidadDisciplina.FEMENINO,
        minimo_por_equipo=5,
        maximo_por_equipo=12,
    )
    PaqueteDisciplina.objects.create(
        paquete_id=inscripcion.paquete_id,
        disciplina=disciplina,
    )
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina,
        categoria=categoria,
        nombre="Equipo Femenino Asistido",
    )


@pytest.fixture
def equipo_sin_cupos(db, inscripcion_sin_pagos, disciplina, categoria):
    """Un equipo de una inscripción SIN cupos PAGADOS.

    Es el estado en el que el dueño rechaza el alta por saldo
    (`SinCuposDisponiblesError`, 409). Sirve para comprobar que un alta
    fallida NO deja basura: la identidad recién creada tiene que deshacerse
    con el resto de la unidad de trabajo.
    """
    from modules.salesianos_fest.domain.models import Equipo

    return Equipo.objects.create(
        inscripcion=inscripcion_sin_pagos,
        disciplina=disciplina,
        categoria=categoria,
        nombre="Equipo Sin Cupos Asistido",
    )


@pytest.fixture
def equipo_femenino_sin_cupos(db, inscripcion_sin_pagos, categoria):
    """Un equipo FEMENINO de una inscripción SIN cupos PAGADOS.

    Junta las dos razones por las que un alta puede fallar: el género no es
    compatible con la disciplina y, además, no hay cupo pagado.
    """
    from modules.salesianos_fest.domain.constants import ModalidadDisciplina
    from modules.salesianos_fest.domain.models import (
        Disciplina,
        Equipo,
        PaqueteDisciplina,
    )

    disciplina = Disciplina.objects.create(
        edicion_id=inscripcion_sin_pagos.edicion_id,
        nombre="Fútbol 7 Femenino Asistido",
        slug="futbol-7-femenino-asistido",
        modalidad=ModalidadDisciplina.FEMENINO,
        minimo_por_equipo=5,
        maximo_por_equipo=12,
    )
    PaqueteDisciplina.objects.create(
        paquete_id=inscripcion_sin_pagos.paquete_id,
        disciplina=disciplina,
    )
    return Equipo.objects.create(
        inscripcion=inscripcion_sin_pagos,
        disciplina=disciplina,
        categoria=categoria,
        nombre="Equipo Fútbol 7 Femenino Asistido",
    )


@pytest.fixture
def persona_masculina(db):
    """Una persona MASCULINA del padrón, con su género declarado.

    Es la identidad que la corrección administrativa del género puede
    cambiar: el administrador la declara `F` y el DUEÑO la admite en una
    disciplina femenina.
    """
    from modules.usuarios.domain.models import Persona

    return Persona.objects.create(
        nombres="Pedro",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento="12121212",
        genero="M",
    )


__all__ = [
    "admin_con_persona",
    "admin_sin_persona",
    "categoria_tienda",
    "cliente_externo",
    "edicion_con_tienda_y_pases",
    "equipo_disciplina_femenina",
    "equipo_femenino_sin_cupos",
    "equipo_sin_cupos",
    "pase_venta",
    "persona_masculina",
    "producto_tienda",
]
