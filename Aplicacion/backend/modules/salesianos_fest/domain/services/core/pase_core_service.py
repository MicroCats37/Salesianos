"""`PaseCoreService` — la escritura del LOTE de pases y su token de gestión.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio (la aporta el flujo).

Este servicio NO abre la compra: la compra de `commerce` la crea el
`CompraFlujo` con su interfaz CONGELADA (`FREEZE-CM-1.0.0`). Este servicio
crea el LOTE de pases —el hecho de dominio— y lo REFERENCIA a esa compra.

**El token de gestión es una CREDENCIAL.** Se genera con `secrets` (no con
`uuid4` ni con un contador): es la única forma de abrir la compra sin
cuenta, así que su aleatoriedad es el control de acceso. Viaja en la
cabecera `X-Pase-Token`, nunca en la query string, y nunca en un listado.
"""

import secrets
from datetime import datetime, timedelta

from django.db.models import F
from django.utils import timezone

from modules.salesianos_fest.domain.constants import (
    EstadoCompraPase,
    MAX_LEN_TOKEN_PASE,
    VIGENCIA_TOKEN_PASE_DIAS,
)
from modules.salesianos_fest.domain.models import CompraPase


class PaseCoreService:
    """Operaciones de persistencia de los lotes de pases."""

    @staticmethod
    def generar_token() -> str:
        """Un token privado de gestión, aleatorio y URL-safe.

        Es una credencial: se genera con `secrets` para que NO sea
        adivinable. Nunca se registra en logs ni se publica en un listado.
        """
        return secrets.token_urlsafe(32)[:MAX_LEN_TOKEN_PASE]

    @staticmethod
    def vencimiento_token() -> datetime:
        """El instante en que expira el token de gestión.

        La POLÍTICA exacta de expiración sigue ABIERTA (`GOV-01-OPEN-05`):
        el MECANISMO (vencimiento) está congelado y el número concreto es un
        valor declarado, conservador y explícito.
        """
        return timezone.now() + timedelta(days=VIGENCIA_TOKEN_PASE_DIAS)

    def crear_compra_pase(
        self,
        *,
        edicion_id,
        pase_id,
        comprador_id,
        cantidad: int,
        precio_unitario,
        total,
        moneda: str,
        referencia: str,
        contacto_email: str = "",
        compra_id=None,
    ) -> CompraPase:
        """Crea el lote de pases comprado.

        El lote nace **PENDIENTE**: no habilita ningún derecho. Lo cambia
        la ACTIVACIÓN de derechos cuando el pago está confirmado (`RN-P02`).

        Args:
            edicion_id: edición del alcance.
            pase_id: pase del catálogo comprado.
            comprador_id: persona que COMPRA (puede no tener cuenta).
            cantidad: número de pases del lote.
            precio_unitario: precio unitario CONGELADO por el servidor.
            total: total CONGELADO por el servidor.
            moneda: código ISO-4217 del total.
            referencia: referencia estable de la intención de compra.
            contacto_email: correo que dejó el visitante.
            compra_id: compra de `commerce` que financia el lote.

        Returns:
            El lote creado.
        """
        return CompraPase.objects.create(
            edicion_id=edicion_id,
            pase_id=pase_id,
            comprador_id=comprador_id,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            total=total,
            moneda=moneda,
            referencia=referencia,
            contacto_email=contacto_email or "",
            compra_id=compra_id,
            estado=EstadoCompraPase.PENDIENTE,
            token=self.generar_token(),
            token_expira_en=self.vencimiento_token(),
        )

    @staticmethod
    def reservar_pase(compra_pase_id) -> bool:
        """Reserva UNA unidad del lote, si hay disponibilidad.

        Es un único `UPDATE` condicional: la condición `asignados <
        cantidad` viaja DENTRO de la sentencia, así que dos asignaciones
        simultáneas NO pueden sobre-asignar el lote. La segunda simplemente
        no actualiza ninguna fila y devuelve `False`.

        Es el mismo patrón que `CapacidadCoreService.reservar_cupo` de
        `DOM-02`: la condición la decide la BASE DE DATOS, no la
        aplicación.

        Args:
            compra_pase_id: identificador del lote.

        Returns:
            `True` si la unidad quedó reservada; `False` si no había
            disponibilidad.
        """
        actualizadas = CompraPase.objects.filter(
            id=compra_pase_id,
            asignados__lt=F("cantidad"),
        ).update(asignados=F("asignados") + 1)
        return actualizadas == 1

    @staticmethod
    def marcar_pagada(compra_pase_id) -> int:
        """Marca el lote como `PAGADA`.

        Sólo lo llama la ACTIVACIÓN de derechos: una compra pendiente NO
        habilita ningún pase (`RN-P02`, `QA-P01`).

        Args:
            compra_pase_id: identificador del lote.

        Returns:
            Cuántas filas se actualizaron (0 o 1).
        """
        actualizadas = CompraPase.objects.filter(
            id=compra_pase_id,
            estado=EstadoCompraPase.PENDIENTE,
        ).update(estado=EstadoCompraPase.PAGADA)
        return actualizadas

    @staticmethod
    def revocar_token(compra_pase_id) -> int:
        """Revoca el token de gestión del lote.

        La revocabilidad del enlace está CONGELADA (`contratos/02` §5): el
        enlace puede invalidarse sin borrar el hecho de la compra.

        Returns:
            Cuántas filas se actualizaron (0 o 1).
        """
        actualizadas = CompraPase.objects.filter(
            id=compra_pase_id,
            token_revocado_en__isnull=True,
        ).update(token_revocado_en=timezone.now())
        return actualizadas


__all__ = ["PaseCoreService"]
