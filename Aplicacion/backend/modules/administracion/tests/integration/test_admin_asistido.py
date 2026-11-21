"""Tests de los comandos ADMINISTRATIVOS asistidos.

Change: `admin-client-purchases-and-participants`

GIVEN  un equipo con su plantilla y un administrador autenticado
WHEN   el administrador agrega un participante por documento o compra para un
       cliente externo
THEN   el comando usa las REGLAS del dueño (capacidad, duplicado,
       disciplina, elegibilidad), el COMPRADOR es el CLIENTE y nunca el
       administrador, el pago queda liquidado por el flujo canónico del
       dueño y la acción queda en el ACTA con QUIÉN, QUÉ y POR QUÉ.

AND    la IDENTIDAD se REUTILIZA si ya está en el padrón y se REGISTRA —sin
       cuenta— si no existe. El alta nunca crea un `Usuario`, nunca borra
       ninguna `Persona` y nunca reescribe sus NOMBRES ni sus APELLIDOS.

AND    el alta es UNA unidad de trabajo: si el dueño la rechaza —por
       género, por disciplina, por duplicado, por capacidad o por falta de
       cupos pagados— la identidad recién creada y el género corregido se
       DESHACEN con el resto de la operación.

AND    el GÉNERO de una identidad existente sólo se corrige cuando el
       administrador lo declara EXPLÍCITAMENTE (`M` o `F`) y es DISTINTO del
       almacenado. Sin declaración, el género del padrón se conserva.
"""

import json

import pytest
from django.test import Client
from ninja_jwt.tokens import AccessToken

from modules.administracion.tests.fixtures.asistido_fixtures import (  # noqa: F401
    admin_con_persona,
    admin_sin_persona,
    categoria_tienda,
    cliente_externo,
    edicion_con_tienda_y_pases,
    equipo_disciplina_femenina,
    equipo_femenino_sin_cupos,
    equipo_sin_cupos,
    pase_venta,
    persona_masculina,
    producto_tienda,
)

pytestmark = pytest.mark.django_db


# ── Utilidades ──────────────────────────────────────────────────────────────


def _cabeceras(usuario):
    """Las cabeceras de una petición autenticada como `usuario`."""
    return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(usuario)}"}


def _post(cliente, url, cuerpo, cabeceras):
    """Una petición JSON."""
    return cliente.post(
        url,
        data=json.dumps(cuerpo),
        content_type="application/json",
        **cabeceras,
    )


def _codigo_de_error(respuesta):
    """El código estable del error de la envoltura congelada."""
    return respuesta.json()["error"]["code"]


# ── La plantilla del equipo ─────────────────────────────────────────────────


def test_el_alta_por_documento_agrega_a_la_plantilla(
    equipo, persona_participante, admin_con_persona
):
    """GIVEN una persona EXISTENTE en el padrón · WHEN el administrador la
    agrega al equipo por su documento · THEN la participación existe y el
    ACTA nombra al administrador, el motivo y la acción."""
    from modules.administracion.domain.models import AccionAuditada
    from modules.salesianos_fest.domain.models import Participacion

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "33333333",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["persona_id"] == str(persona_participante.id)
    assert cuerpo["rol"] == "JUGADOR"
    assert cuerpo["estado"] == "ACTIVA"

    participacion = Participacion.objects.get(id=cuerpo["participacion_id"])
    assert participacion.equipo_id == equipo.id
    assert participacion.inscripcion_id == equipo.inscripcion_id

    acta = AccionAuditada.objects.get(accion="AGREGAR_PARTICIPANTE_EQUIPO")
    assert acta.actor_usuario_id == admin_con_persona.id
    assert acta.motivo == "Inscripción presencial en la mesa de control."


def test_el_alta_reutiliza_la_persona_existente_sin_reescribir_sus_nombres(
    equipo, persona_participante, admin_con_persona
):
    """GIVEN una persona YA en el padrón · WHEN el administrador la agrega con
    OTROS nombres · THEN se reutiliza ESA persona y sus NOMBRES y sus
    APELLIDOS NO se reescriben: la identidad del padrón es la autoridad.

    El género NO se declara: el que está en el padrón se conserva."""
    from modules.usuarios.domain.models import Persona

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "33333333",
            "nombres": "Nombre Inventado",
            "apellidos": "Apellido Inventado",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["persona_id"] == str(persona_participante.id)

    persona = Persona.objects.get(id=persona_participante.id)
    assert persona.nombres == "María"
    assert persona.apellidos == "Quispe"
    # Sin género declarado se CONSERVA el del padrón.
    assert persona.genero == "F"


def test_el_alta_registra_la_identidad_inexistente_sin_crear_cuenta(
    equipo, admin_con_persona
):
    """GIVEN un documento que NO está en el padrón · WHEN el administrador
    declara sus datos y la agrega · THEN la identidad se REGISTRA como
    `Persona` SIN CUENTA y la persona entra al equipo.

    La UI administrativa no expone un CRUD de `Persona`: sí puede REGISTRAR
    una identidad civil, pero jamás crea una cuenta."""
    from modules.salesianos_fest.domain.models import Participacion
    from modules.usuarios.domain.models import Persona, Usuario

    cuentas_antes = Usuario.objects.count()
    personas_antes = Persona.objects.count()

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "55555555",
            "nombres": "Elena",
            "apellidos": "Vega",
            "genero": "F",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]

    persona = Persona.objects.get(numero_documento="55555555")
    assert persona.nombres == "Elena"
    assert persona.apellidos == "Vega"
    assert persona.genero == "F"
    assert cuerpo["persona_id"] == str(persona.id)

    participacion = Participacion.objects.get(id=cuerpo["participacion_id"])
    assert participacion.persona_id == persona.id

    # NADIE nació con una cuenta: la identidad es civil.
    assert Usuario.objects.count() == cuentas_antes
    assert Persona.objects.count() == personas_antes + 1


def test_el_alta_exige_los_nombres_cuando_la_identidad_no_existe(
    equipo, admin_con_persona
):
    """GIVEN un documento que NO está en el padrón · WHEN el administrador no
    declara los nombres · THEN 422 y NO se crea ninguna `Persona`: una
    identidad sin nombre no es una identidad."""
    from modules.usuarios.domain.models import Persona

    personas_antes = Persona.objects.count()

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "55555555",
            "nombres": "",
            "apellidos": "",
            "genero": "F",
            "rol": "JUGADOR",
            "motivo": "Intento de alta sin datos de identidad.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 422
    assert _codigo_de_error(respuesta) == "VALIDATION_ERROR"
    assert Persona.objects.count() == personas_antes


def test_el_alta_normaliza_el_documento_antes_de_resolver(
    equipo, persona_participante, admin_con_persona
):
    """GIVEN el mismo documento escrito con separadores · WHEN se envía · THEN
    la resolución es EXACTA y NORMALIZADA: se reutiliza la misma `Persona` y
    no se registra una segunda."""
    from modules.usuarios.domain.models import Persona

    personas_antes = Persona.objects.count()

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": " 3333-3333 ",
            "nombres": "María",
            "apellidos": "Quispe",
            "genero": "F",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["persona_id"] == str(persona_participante.id)
    assert Persona.objects.count() == personas_antes


def test_el_alta_no_duplica_la_identidad_que_ya_gano_la_carrera(
    equipo, admin_con_persona
):
    """GIVEN que otra petición registró la identidad PRIMERO · WHEN el
    administrador la agrega otra vez · THEN se REUTILIZA la fila que ganó la
    carrera: el padrón queda con UNA sola identidad y sus nombres NO se
    reescriben."""
    from modules.usuarios.domain.models import Persona

    ganador = Persona.objects.create(
        nombres="Ana",
        apellidos="Original",
        tipo_documento="DNI",
        numero_documento="55555555",
        genero="F",
    )

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "55555555",
            "nombres": "Otro",
            "apellidos": "Nombre",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["persona_id"] == str(ganador.id)
    assert Persona.objects.filter(numero_documento="55555555").count() == 1

    ganador.refresh_from_db()
    assert ganador.nombres == "Ana"
    assert ganador.apellidos == "Original"


def test_la_disciplina_exige_el_genero_de_la_identidad_registrada(
    equipo_disciplina_femenina, admin_con_persona
):
    """GIVEN una disciplina FEMENINA · WHEN el administrador registra a una
    persona de género MASCULINO · THEN el DUEÑO lo rechaza con su propio
    código: este comando no reimplementa la regla de elegibilidad."""
    from modules.salesianos_fest.domain.models import Participacion

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo_disciplina_femenina.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "55555555",
            "nombres": "Elena",
            "apellidos": "Vega",
            "genero": "M",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 422
    assert _codigo_de_error(respuesta) == "PARTICIPANTE_NO_ELEGIBLE"
    assert not Participacion.objects.exists()


# ── La unidad de trabajo: un fallo NO deja basura ────────────────────────────


def test_el_alta_sin_cupos_no_deja_una_persona_registrada(
    equipo_sin_cupos, admin_con_persona
):
    """GIVEN una inscripción SIN cupos PAGADOS · WHEN el administrador registra
    a una persona nueva · THEN el DUEÑO rechaza el alta y la identidad
    recién creada se DESHACE con el resto de la unidad de trabajo.

    Sin esta atomicidad, el padrón accumulates identidades que nadie pidió:
    una `Persona` por cada intento fallido."""
    from modules.administracion.domain.models import AccionAuditada
    from modules.salesianos_fest.domain.models import Participacion
    from modules.usuarios.domain.models import Persona, Usuario

    personas_antes = Persona.objects.count()
    cuentas_antes = Usuario.objects.count()

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo_sin_cupos.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "55555555",
            "nombres": "Elena",
            "apellidos": "Vega",
            "genero": "F",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 409, respuesta.content
    assert _codigo_de_error(respuesta) == "SIN_CUPOS_DISPONIBLES"

    # NADA queda a medias: ni la identidad, ni el cupo, ni el acta.
    assert Persona.objects.count() == personas_antes
    assert not Persona.objects.filter(numero_documento="55555555").exists()
    assert Usuario.objects.count() == cuentas_antes
    assert not Participacion.objects.exists()
    assert not AccionAuditada.objects.filter(
        accion="AGREGAR_PARTICIPANTE_EQUIPO"
    ).exists()


def test_el_alta_con_el_genero_incompatible_no_deja_una_persona_registrada(
    equipo_disciplina_femenina, admin_con_persona
):
    """GIVEN una disciplina FEMENINA · WHEN el administrador registra a una
    persona de género MASCULINO · THEN el DUEÑO la rechaza y la identidad
    recién creada se DESHACE.

    El género incompatible se comprueba DESPUÉS de registrar la identidad:
    sin la unidad de trabajo, quedaría una `Persona` con el género
    equivocado en el padrón."""
    from modules.usuarios.domain.models import Persona

    personas_antes = Persona.objects.count()

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo_disciplina_femenina.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "55555555",
            "nombres": "Elena",
            "apellidos": "Vega",
            "genero": "M",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 422
    assert _codigo_de_error(respuesta) == "PARTICIPANTE_NO_ELEGIBLE"
    assert Persona.objects.count() == personas_antes
    assert not Persona.objects.filter(numero_documento="55555555").exists()


# ── La corrección explícita del género ──────────────────────────────────────


def test_el_alta_corrige_el_genero_cuando_el_administrador_lo_declara(
    equipo_disciplina_femenina, persona_masculina, admin_con_persona
):
    """GIVEN una persona MASCULINA en el padrón · WHEN el administrador
    declara EXPLÍCITAMENTE el género femenino · THEN el género se corrige, la
    persona entra al equipo y el ACTA nombra el ANTIGUO y el NUEVO.

    Es la ÚNICA corrección que el padrón admite sobre una identidad viva:
    los nombres y los apellidos no se tocan."""
    from modules.administracion.domain.models import AccionAuditada
    from modules.salesianos_fest.domain.models import Participacion
    from modules.usuarios.domain.models import Persona, Usuario

    cuentas_antes = Usuario.objects.count()

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo_disciplina_femenina.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "12121212",
            "nombres": "Nombre Inventado",
            "apellidos": "Apellido Inventado",
            "genero": "F",
            "rol": "JUGADOR",
            "motivo": "Corrección de género verificada en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["persona_id"] == str(persona_masculina.id)

    persona_masculina.refresh_from_db()
    assert persona_masculina.genero == "F"
    # Los NOMBRES y los APELLIDOS NUNCA se sobrescriben.
    assert persona_masculina.nombres == "Pedro"
    assert persona_masculina.apellidos == "Torres"

    participacion = Participacion.objects.get(id=cuerpo["participacion_id"])
    assert participacion.persona_id == persona_masculina.id

    acta = AccionAuditada.objects.get(accion="AGREGAR_PARTICIPANTE_EQUIPO")
    assert acta.datos["genero_anterior"] == "M"
    assert acta.datos["genero_nuevo"] == "F"

    # La corrección NO crea ninguna cuenta.
    assert Usuario.objects.count() == cuentas_antes


def test_la_correccion_del_genero_se_deshace_si_la_participacion_falla(
    equipo_femenino_sin_cupos, persona_masculina, admin_con_persona
):
    """GIVEN una identidad MASCULINA · WHEN el administrador la corrige a
    femenino en un equipo SIN cupos · THEN el dueño rechaza el alta y el
    género VUELVE al que tenía: la corrección comparte la unidad de
    trabajo."""
    from modules.usuarios.domain.models import Persona

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo_femenino_sin_cupos.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "12121212",
            "genero": "F",
            "rol": "JUGADOR",
            "motivo": "Corrección de género sobre un equipo sin cupos.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 409, respuesta.content
    assert _codigo_de_error(respuesta) == "SIN_CUPOS_DISPONIBLES"

    persona_masculina.refresh_from_db()
    assert persona_masculina.genero == "M"
    assert Persona.objects.filter(numero_documento="12121212").count() == 1


def test_el_alta_sin_genero_conserva_el_genero_registrado(
    equipo, persona_masculina, admin_con_persona
):
    """GIVEN una persona con género MASCULINO · WHEN el administrador NO
    declara género · THEN el género del padrón se CONSERVA tal cual.

    La ausencia de género NO es una orden de borrarlo: corregir es
    EXPLÍCITO."""
    from modules.usuarios.domain.models import Persona

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "12121212",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content

    persona_masculina.refresh_from_db()
    assert persona_masculina.genero == "M"
    assert Persona.objects.filter(numero_documento="12121212").count() == 1


def test_el_genero_masculino_sigue_sin_admitirse_en_una_disciplina_femenina(
    equipo_disciplina_femenina, persona_masculina, admin_con_persona
):
    """GIVEN una persona MASCULINA · WHEN el administrador NO corrige su
    género · THEN el DUEÑO la rechaza: la regla de elegibilidad NO se
    relaja."""
    from modules.salesianos_fest.domain.models import Participacion

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo_disciplina_femenina.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "12121212",
            "rol": "JUGADOR",
            "motivo": "Inscripción presencial en la mesa de control.",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 422
    assert _codigo_de_error(respuesta) == "PARTICIPANTE_NO_ELEGIBLE"
    assert not Participacion.objects.exists()


def test_el_alta_exige_el_motivo(equipo, persona_participante, admin_con_persona):
    """GIVEN un comando sin motivo · WHEN se envía · THEN 422
    `MOTIVO_REQUERIDO`: sin motivo no hay acta y sin acta no hay comando."""
    from modules.salesianos_fest.domain.models import Participacion

    respuesta = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "33333333",
            "rol": "JUGADOR",
            "motivo": "   ",
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 422
    assert _codigo_de_error(respuesta) == "MOTIVO_REQUERIDO"
    assert not Participacion.objects.exists()


def test_el_alta_respeta_el_duplicado_del_dueno(
    equipo, persona_participante, admin_con_persona
):
    """GIVEN una persona YA en la plantilla · WHEN se la agrega otra vez ·
    THEN el DUEÑO lo rechaza con su propio código: este comando no
    reimplementa la regla de duplicado."""
    from modules.salesianos_fest.domain.models import Participacion

    primero = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "33333333",
            "rol": "JUGADOR",
            "motivo": "Alta de la primera vez.",
        },
        _cabeceras(admin_con_persona),
    )
    assert primero.status_code == 201

    segundo = _post(
        Client(),
        f"/api/administracion/equipos/{equipo.id}/participantes",
        {
            "tipo_documento": "DNI",
            "numero_documento": "33333333",
            "rol": "JUGADOR",
            "motivo": "Alta repetida.",
        },
        _cabeceras(admin_con_persona),
    )

    assert segundo.status_code == 422
    assert _codigo_de_error(segundo) == "PARTICIPANTE_DUPLICADO"
    assert Participacion.objects.count() == 1


# ── La compra asistida de pases ─────────────────────────────────────────────


def test_la_compra_de_pases_tiene_al_cliente_como_comprador(
    pase_venta, cliente_externo, admin_con_persona
):
    """GIVEN un cliente de tercera persona · WHEN el administrador compra
    pases para él · THEN el COMPRADOR es el cliente y NUNCA el
    administrador, aunque el administrador tenga persona vinculada."""
    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import CompraPase

    respuesta = _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 2,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "77777777",
                "nombres": "Rosa",
                "apellidos": "Díaz",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": {
                "canal": "EFECTIVO",
                "referencia": "REC-0001",
                "motivo": "Cobro en la boletería del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["tipo"] == "PASE"
    assert cuerpo["comprador_persona_id"] == str(cliente_externo.id)
    assert cuerpo["comprador_persona_id"] != str(admin_con_persona.persona_fk_id)
    assert cuerpo["cantidad"] == 2

    lote = CompraPase.objects.get(id=cuerpo["recurso_id"])
    assert str(lote.comprador_id) == str(cliente_externo.id)

    compra = Compra.objects.get(id=lote.compra_id)
    assert str(compra.persona_id) == str(cliente_externo.id)
    assert str(compra.id) == cuerpo["compra_id"]


def test_la_compra_de_pases_liquida_el_pago_con_el_flujo_canonico(
    pase_venta, cliente_externo, admin_con_persona
):
    """GIVEN una compra asistida · WHEN el administrador registra la
    evidencia del pago · THEN la orden queda CONFIRMADA, la EVIDENCIA
    MANUAL queda persistida y la compra consta pagada."""
    from modules.commerce.domain.constants import EstadoCompra
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.constants import EstadoOrdenPago
    from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago
    from modules.salesianos_fest.domain.models import CompraPase

    respuesta = _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 1,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "77777777",
                "nombres": "Rosa",
                "apellidos": "Díaz",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": {
                "canal": "EFECTIVO",
                "referencia": "REC-0002",
                "motivo": "Cobro en la boletería del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]

    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    assert orden.estado == EstadoOrdenPago.CONFIRMADA

    aprobacion = AprobacionPagoManual.objects.get(orden_pago=orden)
    assert aprobacion.canal == "EFECTIVO"
    assert aprobacion.referencia == "REC-0002"
    assert str(aprobacion.actor_id) == str(admin_con_persona.id)

    lote = CompraPase.objects.get(id=cuerpo["recurso_id"])
    compra = Compra.objects.get(id=lote.compra_id)
    assert compra.estado == EstadoCompra.PAGADA


def test_la_compra_de_pases_deja_el_acta_con_el_administrador(
    pase_venta, cliente_externo, admin_con_persona
):
    """GIVEN una compra asistida · WHEN se revisa el ACTA · THEN nombra al
    ADMINISTRADOR como actor y guarda el motivo y la referencia."""
    from modules.administracion.domain.models import AccionAuditada

    _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 1,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "77777777",
                "nombres": "Rosa",
                "apellidos": "Díaz",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": {
                "canal": "YAPE",
                "referencia": "OP-9988",
                "motivo": "Pago por Yape registrado en la mesa.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    acta = AccionAuditada.objects.get(accion="COMPRAR_PASE_PARA_CLIENTE")
    assert acta.actor_usuario_id == admin_con_persona.id
    assert acta.motivo == "Pago por Yape registrado en la mesa."
    assert acta.datos["referencia"] == "OP-9988"
    assert acta.datos["canal"] == "YAPE"


# ── La compra asistida de tienda ────────────────────────────────────────────


def test_el_pedido_de_tienda_tiene_al_cliente_como_comprador(
    producto_tienda, cliente_externo, admin_con_persona
):
    """GIVEN un cliente de tercera persona · WHEN el administrador pide la
    tienda para él · THEN el PEDIDO y su COMPRA son del cliente, el stock
    queda reservado y el pago queda liquidado."""
    from modules.commerce.domain.constants import EstadoCompra
    from modules.commerce.domain.models import Compra
    from modules.marketplace.domain.models import Pedido
    from modules.pagos.domain.constants import EstadoOrdenPago
    from modules.pagos.domain.models import OrdenPago

    respuesta = _post(
        Client(),
        "/api/administracion/marketplace/pedidos-cliente",
        {
            "items": [
                {"tipo": "PRODUCTO", "producto_id": str(producto_tienda.id), "cantidad": 2}
            ],
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "77777777",
                "nombres": "Rosa",
                "apellidos": "Díaz",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": {
                "canal": "TRANSFERENCIA_BANCARIA",
                "referencia": "OP-7788",
                "motivo": "Transferencia recibida por el banco del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]
    assert cuerpo["tipo"] == "PEDIDO"
    assert cuerpo["comprador_persona_id"] == str(cliente_externo.id)
    assert cuerpo["comprador_persona_id"] != str(admin_con_persona.persona_fk_id)
    assert cuerpo["cantidad"] == 2

    pedido = Pedido.objects.get(id=cuerpo["recurso_id"])
    assert str(pedido.comprador_id) == str(cliente_externo.id)
    assert pedido.contacto_email == "rosa@example.com"

    orden = OrdenPago.objects.get(id=cuerpo["orden_pago_id"])
    assert orden.estado == EstadoOrdenPago.CONFIRMADA

    compra = Compra.objects.get(id=pedido.compra_id)
    assert str(compra.persona_id) == str(cliente_externo.id)
    assert str(compra.id) == cuerpo["compra_id"]
    assert compra.estado == EstadoCompra.PAGADA


def test_el_cliente_inexistente_se_registra_en_el_padron(
    pase_venta, admin_con_persona
):
    """GIVEN un cliente que NO está en el padrón · WHEN se compra para él ·
    THEN su identidad civil se REGISTRA y es la compradora: el cliente no
    necesita cuenta."""
    from modules.usuarios.domain.models import Persona

    respuesta = _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 1,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "66666666",
                "nombres": "Elena",
                "apellidos": "Vega",
                "contacto_email": "elena@example.com",
            },
            "evidencia": {
                "canal": "EFECTIVO",
                "referencia": "REC-0003",
                "motivo": "Cobro en la boletería del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = respuesta.json()["data"]

    persona = Persona.objects.get(numero_documento="66666666")
    assert persona.nombres == "Elena"
    assert cuerpo["comprador_persona_id"] == str(persona.id)


def test_el_cliente_inexistente_se_registra_con_su_genero_sin_cuenta(
    pase_venta, admin_con_persona
):
    """GIVEN un cliente que NO está en el padrón · WHEN se compra para él con
    su género · THEN la identidad se REGISTRA con ese género y NINGUNA cuenta
    nace: el cliente es una identidad civil."""
    from modules.usuarios.domain.models import Persona, Usuario

    cuentas_antes = Usuario.objects.count()

    respuesta = _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 1,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "66666667",
                "nombres": "Elena",
                "apellidos": "Vega",
                "genero": "F",
                "contacto_email": "elena@example.com",
            },
            "evidencia": {
                "canal": "EFECTIVO",
                "referencia": "REC-0008",
                "motivo": "Cobro en la boletería del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content

    persona = Persona.objects.get(numero_documento="66666667")
    assert persona.genero == "F"
    assert Usuario.objects.count() == cuentas_antes


def test_el_cliente_inexistente_exige_sus_nombres(
    pase_venta, admin_con_persona
):
    """GIVEN un cliente que NO está en el padrón · WHEN no se declaran sus
    nombres · THEN 422 y NO se registra ninguna identidad: una identidad sin
    nombre no es una identidad."""
    from modules.usuarios.domain.models import Persona

    personas_antes = Persona.objects.count()

    respuesta = _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 1,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "66666668",
                "nombres": "",
                "apellidos": "",
                "genero": "F",
                "contacto_email": "elena@example.com",
            },
            "evidencia": {
                "canal": "EFECTIVO",
                "referencia": "REC-0010",
                "motivo": "Cobro en la boletería del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 422
    assert _codigo_de_error(respuesta) == "VALIDATION_ERROR"
    assert Persona.objects.count() == personas_antes


def test_el_cliente_ya_registrado_no_se_reescribe(
    pase_venta, cliente_externo, admin_con_persona
):
    """GIVEN un cliente YA en el padrón · WHEN el administrador declara OTROS
    nombres · THEN se reutiliza su identidad y sus nombres NO se
    reescriben."""
    from modules.usuarios.domain.models import Persona

    respuesta = _post(
        Client(),
        "/api/administracion/pases/compras-cliente",
        {
            "pase_id": str(pase_venta.id),
            "cantidad": 1,
            "cliente": {
                "tipo_documento": "DNI",
                "numero_documento": "77777777",
                "nombres": "Nombre Inventado",
                "apellidos": "Apellido Inventado",
                "genero": "M",
                "contacto_email": "rosa@example.com",
            },
            "evidencia": {
                "canal": "EFECTIVO",
                "referencia": "REC-0009",
                "motivo": "Cobro en la boletería del FEST.",
            },
        },
        _cabeceras(admin_con_persona),
    )

    assert respuesta.status_code == 201, respuesta.content

    cliente_externo.refresh_from_db()
    assert cliente_externo.nombres == "Rosa"
    assert cliente_externo.apellidos == "Díaz"
    assert Persona.objects.filter(numero_documento="77777777").count() == 1


# ── La frontera de permisos ─────────────────────────────────────────────────


def test_una_cuenta_normal_no_alcanza_los_comandos_asistidos(
    usuario_responsable, equipo, persona_participante, pase_venta, producto_tienda
):
    """GIVEN una cuenta sin capacidades · WHEN llama a los tres comandos ·
    THEN 403 `ACTION_NOT_ALLOWED`: el permiso se comprueba ANTES que la
    forma del cuerpo."""
    cabeceras = _cabeceras(usuario_responsable)
    cliente = Client()

    respuestas = [
        _post(
            cliente,
            f"/api/administracion/equipos/{equipo.id}/participantes",
            {
                "tipo_documento": "DNI",
                "numero_documento": "33333333",
                "rol": "JUGADOR",
                "motivo": "Intento sin capacidades.",
            },
            cabeceras,
        ),
        _post(
            cliente,
            "/api/administracion/pases/compras-cliente",
            {
                "pase_id": str(pase_venta.id),
                "cantidad": 1,
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "77777777",
                    "nombres": "Rosa",
                    "apellidos": "Díaz",
                    "contacto_email": "rosa@example.com",
                },
                "evidencia": {
                    "canal": "EFECTIVO",
                    "referencia": "REC-0004",
                    "motivo": "Intento sin capacidades.",
                },
            },
            cabeceras,
        ),
        _post(
            cliente,
            "/api/administracion/marketplace/pedidos-cliente",
            {
                "items": [
                    {
                        "tipo": "PRODUCTO",
                        "producto_id": str(producto_tienda.id),
                        "cantidad": 1,
                    }
                ],
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "77777777",
                    "nombres": "Rosa",
                    "apellidos": "Díaz",
                    "contacto_email": "rosa@example.com",
                },
                "evidencia": {
                    "canal": "EFECTIVO",
                    "referencia": "REC-0005",
                    "motivo": "Intento sin capacidades.",
                },
            },
            cabeceras,
        ),
    ]

    for respuesta in respuestas:
        assert respuesta.status_code == 403, respuesta.content
        assert _codigo_de_error(respuesta) == "ACTION_NOT_ALLOWED"


def test_una_peticion_anonima_no_alcanza_los_comandos_asistidos(
    equipo, pase_venta, producto_tienda
):
    """GIVEN una petición SIN cuenta · WHEN llama a los tres comandos · THEN
    401 `AUTHENTICATION_REQUIRED`: la autenticación se exige ANTES que el
    permiso."""
    cliente = Client()

    respuestas = [
        _post(
            cliente,
            f"/api/administracion/equipos/{equipo.id}/participantes",
            {
                "tipo_documento": "DNI",
                "numero_documento": "33333333",
                "rol": "JUGADOR",
                "motivo": "Intento anónimo.",
            },
            {},
        ),
        _post(
            cliente,
            "/api/administracion/pases/compras-cliente",
            {
                "pase_id": str(pase_venta.id),
                "cantidad": 1,
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "77777777",
                    "nombres": "Rosa",
                    "apellidos": "Díaz",
                    "contacto_email": "rosa@example.com",
                },
                "evidencia": {
                    "canal": "EFECTIVO",
                    "referencia": "REC-0006",
                    "motivo": "Intento anónimo.",
                },
            },
            {},
        ),
        _post(
            cliente,
            "/api/administracion/marketplace/pedidos-cliente",
            {
                "items": [
                    {
                        "tipo": "PRODUCTO",
                        "producto_id": str(producto_tienda.id),
                        "cantidad": 1,
                    }
                ],
                "cliente": {
                    "tipo_documento": "DNI",
                    "numero_documento": "77777777",
                    "nombres": "Rosa",
                    "apellidos": "Díaz",
                    "contacto_email": "rosa@example.com",
                },
                "evidencia": {
                    "canal": "EFECTIVO",
                    "referencia": "REC-0007",
                    "motivo": "Intento anónimo.",
                },
            },
            {},
        ),
    ]

    for respuesta in respuestas:
        assert respuesta.status_code == 401, respuesta.content
        assert _codigo_de_error(respuesta) == "AUTHENTICATION_REQUIRED"
