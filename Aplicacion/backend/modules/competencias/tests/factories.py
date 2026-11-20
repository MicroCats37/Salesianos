"""Factories puras del módulo `competencias`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.2 · §5

Una función por payload del módulo. Cada función devuelve un `dict` PURO:
no toca la base de datos, no importa modelos y no depende del orden de los
tests. Los tests integration las usan para construir el `data` de las
llamadas al dominio.

`NO se usa factory_boy`: las factories son funciones puras.
"""

from datetime import date, datetime


def competencia_crear_payload(
    *,
    edicion_id: str,
    disciplina_id: str,
    categoria_id: str,
    nombre: str = "Vóley Mixto 2027",
    fecha: date = date(2027, 3, 14),
) -> dict:
    """El payload del alta de una competencia.

    La `categoria_id` es OBLIGATORIA: la identidad de una competencia es
    (edición, disciplina, categoría, nombre).
    """
    return {
        "edicion_id": edicion_id,
        "disciplina_id": disciplina_id,
        "categoria_id": categoria_id,
        "nombre": nombre,
        "fecha": fecha,
    }


def equipo_incorporar_payload(
    *,
    equipo_id: str,
    orden: int = 1,
) -> dict:
    """El payload de la incorporación de un equipo al cuadro."""
    return {
        "equipo_id": equipo_id,
        "orden": orden,
    }


def equipo_editar_payload(
    *,
    orden: int | None = None,
    estado: str | None = None,
) -> dict:
    """El payload de la edición de la participación de un equipo."""
    return {
        "orden": orden,
        "estado": estado,
    }


def ronda_crear_payload(
    *,
    etiqueta: str = "Cuartos de final",
    orden: int = 1,
) -> dict:
    """El payload del alta de una ronda."""
    return {
        "etiqueta": etiqueta,
        "orden": orden,
    }


def encuentro_crear_payload(*, orden: int = 1) -> dict:
    """El payload del alta de un encuentro."""
    return {"orden": orden}


def encuentro_actualizar_payload(
    *,
    participante_1_id: str | None = None,
    participante_2_id: str | None = None,
    inicio_programado: datetime | None = None,
    fin_programado: datetime | None = None,
    siguiente_encuentro_id: str | None = None,
    slot_destino: str | None = None,
    es_bye: bool | None = None,
    estado: str | None = None,
    motivo: str | None = None,
) -> dict:
    """El payload de la edición de un encuentro.

    Los campos con valor `None` NO se incluyen: un campo ausente significa
    "no tocar".
    """
    payload = {
        "participante_1_id": participante_1_id,
        "participante_2_id": participante_2_id,
        "inicio_programado": inicio_programado,
        "fin_programado": fin_programado,
        "siguiente_encuentro_id": siguiente_encuentro_id,
        "slot_destino": slot_destino,
        "es_bye": es_bye,
        "estado": estado,
        "motivo": motivo,
    }
    return {clave: valor for clave, valor in payload.items() if valor is not None}


def resultado_registrar_payload(
    *,
    ganador_id: str,
    puntaje_1: int | None = None,
    puntaje_2: int | None = None,
    marcador_detalle: str | None = None,
    motivo: str | None = "Registro del resultado",
) -> dict:
    """El payload del registro del resultado autoritativo."""
    return {
        "ganador_id": ganador_id,
        "puntaje_1": puntaje_1,
        "puntaje_2": puntaje_2,
        "marcador_detalle": marcador_detalle,
        "motivo": motivo,
    }


def correccion_payload(
    *,
    ganador_id: str,
    motivo: str | None = "Corrección del resultado",
    override: bool = False,
    acepta_impacto: bool = False,
) -> dict:
    """El payload de la corrección del ganador."""
    return {
        "ganador_id": ganador_id,
        "motivo": motivo,
        "override": override,
        "acepta_impacto": acepta_impacto,
    }


__all__ = [
    "competencia_crear_payload",
    "correccion_payload",
    "encuentro_actualizar_payload",
    "encuentro_crear_payload",
    "equipo_editar_payload",
    "equipo_incorporar_payload",
    "resultado_registrar_payload",
    "ronda_crear_payload",
]
