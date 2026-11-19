"""Autoridad de permisos y autenticación (FREEZE-ENV-1.0.0 · FR-01 §4.4).

GIVEN  el mapa de capacidades (`core.capacidades`) y las clases de permiso
       (`core.permissions`)
WHEN   se consulta una puerta
THEN   la decisión sale de las banderas de Django (`is_staff` / `is_superuser`)
       y el actor anónimo nunca es autorizado.
"""

import pytest
from django.test import RequestFactory

from core.capacidades import (
    CAP_ADMIN_VER,
    CAP_PAGOS_APROBAR,
    NIVEL_STAFF,
    NIVEL_SUPERUSUARIO,
    NIVEL_USUARIO,
    TODAS_LAS_CAPACIDADES,
    es_admin,
    nivel_de,
    tiene_capacidad,
)
from core.permissions import (
    RequireAdmin,
    RequireAdminVer,
    RequireCapability,
    RequirePagosAprobar,
)


class _Actor:
    """Actor de pruebas con las banderas de Django que importan."""

    def __init__(self, is_staff=False, is_superuser=False, is_authenticated=True):
        self.is_staff = is_staff
        self.is_superuser = is_superuser
        self.is_authenticated = is_authenticated


def _request(actor):
    request = RequestFactory().get("/api/administracion/pagos")
    request.user = actor
    return request


@pytest.fixture
def usuario():
    return _Actor()


@pytest.fixture
def staff():
    return _Actor(is_staff=True)


@pytest.fixture
def superusuario():
    return _Actor(is_staff=True, is_superuser=True)


@pytest.fixture
def anonimo():
    return _Actor(is_authenticated=False)


# ── La autoridad vive en las banderas de Django ──────────────────────────────


def test_el_mapa_de_capacidades_no_inventa_un_tercer_tier(usuario, staff, superusuario):
    assert nivel_de(usuario) == NIVEL_USUARIO
    assert nivel_de(staff) == NIVEL_STAFF
    assert nivel_de(superusuario) == NIVEL_SUPERUSUARIO


def test_el_tier_break_glass_gana_al_tier_operativo(superusuario):
    """Un superusuario es `is_staff=True` también: su nivel es el break-glass."""
    assert superusuario.is_staff is True
    assert nivel_de(superusuario) == NIVEL_SUPERUSUARIO


def test_el_usuario_normal_no_tiene_capacidades(usuario):
    assert es_admin(usuario) is False
    assert tiene_capacidad(usuario, CAP_ADMIN_VER) is False


def test_el_superusuario_resuelve_el_conjunto_completo(superusuario):
    assert es_admin(superusuario) is True
    for codigo in TODAS_LAS_CAPACIDADES:
        assert tiene_capacidad(superusuario, codigo) is True


def test_el_staff_no_aproba_pagos(staff):
    """La capacidad sensible es exclusiva del tier break-glass."""
    assert tiene_capacidad(staff, CAP_ADMIN_VER) is True
    assert tiene_capacidad(staff, CAP_PAGOS_APROBAR) is False


# ── Puertas ──────────────────────────────────────────────────────────────────


def test_require_admin_acepta_al_staff(staff):
    assert RequireAdmin().has_permission(_request(staff), None) is True


def test_require_admin_acepta_al_superusuario(superusuario):
    assert RequireAdmin().has_permission(_request(superusuario), None) is True


def test_require_admin_rechaza_al_usuario_normal(usuario):
    assert RequireAdmin().has_permission(_request(usuario), None) is False


def test_require_admin_rechaza_al_anonimo(anonimo):
    assert RequireAdmin().has_permission(_request(anonimo), None) is False


def test_require_capability_sin_codigo_rechaza_siempre(staff):
    assert RequireCapability().has_permission(_request(staff), None) is False


def test_require_capability_acepta_quien_tiene_la_capacidad(staff):
    assert RequireAdminVer().has_permission(_request(staff), None) is True


def test_require_capability_rechaza_quien_no_la_tiene(usuario):
    assert RequireAdminVer().has_permission(_request(usuario), None) is False


def test_la_capacidad_sensible_solo_la_tiene_el_break_glass(staff, superusuario):
    assert RequirePagosAprobar().has_permission(_request(staff), None) is False
    assert RequirePagosAprobar().has_permission(_request(superusuario), None) is True


def test_una_instancia_con_codigo_explicito_resuelve_la_misma_capacidad(staff):
    puerta = RequireCapability(CAP_ADMIN_VER)

    assert puerta.has_permission(_request(staff), None) is True


# ── La autenticación precede a la autorización ───────────────────────────────


def test_la_api_declara_autenticacion_por_defecto(api):
    """La autenticación se resuelve antes que el permiso: 401 antes que 403.

    Sin `auth` explícito, una petición anónima falla en la autenticación y
    nunca llega a `RequireAdmin`. La API declara `JWTAuth()` globalmente.
    """
    from ninja_jwt.authentication import JWTAuth

    declarados = api.auth if isinstance(api.auth, (list, tuple)) else [api.auth]
    assert any(isinstance(auth, JWTAuth) for auth in declarados)


def test_el_mensaje_de_denial_no_lo_define_la_clase_de_permiso():
    """El mensaje público del 403 sale del catálogo, no de la puerta."""
    from core.exceptions import PUBLIC_ERROR_MESSAGES

    # La puerta decide SI se permite; NO redacta el mensaje público: no
    # declara un `message` propio.
    assert "message" not in RequireAdmin.__dict__
    assert PUBLIC_ERROR_MESSAGES["ACTION_NOT_ALLOWED"] == (
        "No tienes autorización para realizar esta acción."
    )
