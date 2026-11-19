"""Fixtures del módulo `salesianos_fest`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3 — las fixtures viven
aquí; `tests/conftest.py` sólo las importa y registra.

La compra se crea con el `CompraFlujo` REAL de `commerce`: este paquete
consume la interfaz CONGELADA de `commerce`, así que los tests la prueban
contra la implementación real y no contra un doble.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from modules.eventos.domain.constants import EstadoEdicion, ModuloLogico
from modules.eventos.domain.models import Edicion, Evento
from modules.salesianos_fest.domain.constants import (
    EstadoDisciplina,
    EstadoPaquete,
    TipoBeneficioPaquete,
)
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    PaqueteBeneficio,
    PaqueteDisciplina,
    PaquetePrecio,
)
from modules.usuarios.domain.models import Persona, Usuario


# ── Edición ─────────────────────────────────────────────────────────────────


@pytest.fixture
def evento(db):
    """Evento propietario de las ediciones del test."""
    return Evento.objects.create(nombre="Salesianos FEST", slug="salesianos-fest")


@pytest.fixture
def edicion_publicada(db, evento):
    """Edición `PUBLICADA` con el módulo `inscripciones` habilitado."""
    edicion = Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2027",
        slug="2027",
        anio=2027,
        estado=EstadoEdicion.PUBLICADA,
        modulos_habilitados=[ModuloLogico.INSCRIPCIONES],
    )
    return edicion


@pytest.fixture
def edicion_borrador(db, evento):
    """Edición en `BORRADOR`: no se puede comprar ni publicar catálogo."""
    return Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2028",
        slug="2028",
        anio=2028,
        modulos_habilitados=[ModuloLogico.INSCRIPCIONES],
    )


@pytest.fixture
def edicion_otra(db):
    """Una SEGUNDA edición publicada: permite comprobar el aislamiento."""
    otro_evento = Evento.objects.create(nombre="Otro FEST", slug="otro-fest")
    return Edicion.objects.create(
        evento=otro_evento,
        nombre="Otro FEST 2027",
        slug="2027",
        anio=2027,
        estado=EstadoEdicion.PUBLICADA,
        modulos_habilitados=[ModuloLogico.INSCRIPCIONES],
    )


@pytest.fixture
def edicion_sin_modulo(db):
    """Edición publicada SIN el módulo `inscripciones` habilitado.

    Tiene su propio evento: el evento admite UNA sola edición `PUBLICADA`
    (invariante de `eventos`).
    """
    otro_evento = Evento.objects.create(nombre="FEST sin módulo", slug="sin-modulo")
    return Edicion.objects.create(
        evento=otro_evento,
        nombre="FEST sin módulo 2027",
        slug="2027",
        anio=2027,
        estado=EstadoEdicion.PUBLICADA,
    )


# ── Catálogo ────────────────────────────────────────────────────────────────


@pytest.fixture
def disciplina(db, edicion_publicada):
    """Disciplina activa de la edición publicada."""
    return Disciplina.objects.create(
        edicion=edicion_publicada,
        nombre="Vóley Mixto",
        slug="voley-mixto",
        minimo_por_equipo=5,
        maximo_por_equipo=12,
    )


@pytest.fixture
def disciplina_inactiva(db, edicion_publicada):
    """Disciplina `INACTIVA`: no puede entrar en un equipo."""
    return Disciplina.objects.create(
        edicion=edicion_publicada,
        nombre="Vóley Legacy",
        slug="voley-legacy",
        estado=EstadoDisciplina.INACTIVA,
    )


@pytest.fixture
def disciplina_otra_edicion(db, edicion_otra):
    """Disciplina de OTRA edición: no puede entrar en un equipo."""
    return Disciplina.objects.create(
        edicion=edicion_otra,
        nombre="Fútbol de Otro FEST",
        slug="futbol-otro",
    )


@pytest.fixture
def paquete(db, edicion_publicada, disciplina):
    """Paquete vigente de la edición publicada, con su disciplina."""
    paquete = Paquete.objects.create(
        edicion=edicion_publicada,
        nombre="Paquete competitivo",
        slug="competitivo",
        descripcion="Paquete de la edición publicada.",
        cupos_incluidos=10,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)
    return paquete


@pytest.fixture
def paquete_sin_precio(db, edicion_publicada, disciplina):
    """Paquete VIGENTE sin precio: NO está a la venta."""
    paquete = Paquete.objects.create(
        edicion=edicion_publicada,
        nombre="Paquete sin precio",
        slug="sin-precio",
        cupos_incluidos=5,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)
    return paquete


@pytest.fixture
def paquete_retirado(db, edicion_publicada, disciplina):
    """Paquete `RETIRADO`: no se ofrece ni se compra."""
    paquete = Paquete.objects.create(
        edicion=edicion_publicada,
        nombre="Paquete retirado",
        slug="retirado",
        estado=EstadoPaquete.RETIRADO,
        cupos_incluidos=5,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)
    return paquete


@pytest.fixture
def precio(db, paquete):
    """Precio vigente del paquete."""
    return PaquetePrecio.objects.create(
        paquete=paquete,
        monto=Decimal("250.00"),
        moneda="PEN",
        vigente_desde=date.today() - timedelta(days=1),
    )


@pytest.fixture
def beneficio(db, paquete):
    """Beneficio `FIJO_INICIAL` ofrecido por el paquete."""
    return PaqueteBeneficio.objects.create(
        paquete=paquete,
        codigo="BIENVENIDA",
        nombre="Bienvenida al FEST",
        tipo=TipoBeneficioPaquete.FIJO_INICIAL,
        cantidad=1,
    )


@pytest.fixture
def beneficio_por_cupo(db, paquete):
    """Beneficio `POR_CUPO` ofrecido por el paquete.

    Su regla de reparto sigue ABIERTA (`PD-09`): el módulo NO lo concede.
    """
    return PaqueteBeneficio.objects.create(
        paquete=paquete,
        codigo="FIESTA",
        nombre="Entrada de fiesta",
        tipo=TipoBeneficioPaquete.POR_CUPO,
        cantidad=1,
    )


# ── Inscripción y pool (DOM-02) ─────────────────────────────────────────────


@pytest.fixture
def inscripcion(db, edicion_publicada, paquete, persona):
    """Inscripción viva con la capacidad YA pagada.

    La capacidad pagada se escribe DIRECTAMENTE porque estos tests ejercitan
    el pool, no el pago: la activación de derechos tiene su propio fichero
    de pruebas (`test_cupo_activacion.py`).
    """
    return Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona,
        paquete=paquete,
        referencia="INS-TEST-0001",
        cupos_solicitados=10,
        cupos_pagados=10,
        cupos_asignados=0,
    )


@pytest.fixture
def inscripcion_sin_pagos(db, edicion_publicada, paquete, persona):
    """Inscripción viva SIN capacidad pagada.

    Es el estado en el que queda una inscripción cuya compra está PENDIENTE:
    la activación de derechos es la que la llena (`RN-I02`).
    """
    return Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona,
        paquete=paquete,
        referencia="INS-TEST-0002",
        cupos_solicitados=10,
        cupos_pagados=0,
        cupos_asignados=0,
    )


@pytest.fixture
def equipo(db, inscripcion, disciplina):
    """Equipo de la inscripción, de la disciplina del paquete."""
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina,
        nombre="Equipo Vóley",
    )


@pytest.fixture
def persona_participante(db):
    """Una segunda persona, para agregar al pool."""
    return Persona.objects.create(
        nombres="María",
        apellidos="Quispe",
        tipo_documento="DNI",
        numero_documento="33333333",
        genero="F",
    )


@pytest.fixture
def persona_otro_participante(db):
    """Una tercera persona, para los casos de reasignación."""
    return Persona.objects.create(
        nombres="Pedro",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento="44444444",
        genero="M",
    )


# ── Identidad ───────────────────────────────────────────────────────────────


@pytest.fixture
def persona(db):
    """La persona responsable de la inscripción."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Quispe",
        tipo_documento="DNI",
        numero_documento="11111111",
    )


@pytest.fixture
def persona_ajena(db):
    """Una segunda persona, para comprobar la titularidad."""
    return Persona.objects.create(
        nombres="Luis",
        apellidos="Ramos",
        tipo_documento="DNI",
        numero_documento="22222222",
    )


@pytest.fixture
def usuario_responsable(db, persona):
    """Cuenta autenticada con persona vinculada."""
    return Usuario.objects.create_user(
        username="responsable",
        password="Prueba-12345",
        persona_fk=persona,
    )


@pytest.fixture
def usuario_ajeno(db, persona_ajena):
    """Cuenta autenticada de OTRA persona."""
    return Usuario.objects.create_user(
        username="ajeno",
        password="Prueba-12345",
        persona_fk=persona_ajena,
    )


# ── Servicios ───────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def injector():
    """El inyector de dependencias del paquete DOM-01.

    Incluye los módulos de DI de los Dueños que este módulo consume:
    `usuarios` (titularidad), `eventos` (alcance de edición), `pagos` y
    `commerce` (la interfaz comercial congelada).
    """
    from injector import Injector

    from modules.commerce.di import CommerceModule
    from modules.eventos.di import EventosModule
    from modules.pagos.di import PagosModule
    from modules.salesianos_fest.di import SalesianosFestModule
    from modules.usuarios.di import UsuariosModule

    return Injector(
        [
            UsuariosModule,
            EventosModule,
            PagosModule,
            CommerceModule,
            SalesianosFestModule,
        ]
    )


__all__ = [
    "beneficio",
    "beneficio_por_cupo",
    "disciplina",
    "disciplina_inactiva",
    "disciplina_otra_edicion",
    "edicion_borrador",
    "edicion_otra",
    "edicion_publicada",
    "edicion_sin_modulo",
    "equipo",
    "evento",
    "injector",
    "inscripcion",
    "inscripcion_sin_pagos",
    "paquete",
    "paquete_retirado",
    "paquete_sin_precio",
    "persona",
    "persona_ajena",
    "persona_otro_participante",
    "persona_participante",
    "precio",
    "usuario_ajeno",
    "usuario_responsable",
]

