"""`IdempotenciaPagoService` — la clave de idempotencia del borde HTTP.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.2)

Contrato congelado:

| Aspecto | Regla |
|---|---|
| Transporte | Header `Idempotency-Key` (string opaco, ≤ 128 caracteres) |
| Formato | UUID v4 o equivalente aleatorio, generado por el cliente **en cada intención de negocio**, no por intento de red |
| Ámbito | Por endpoint + actor. Dos claves distintas ⇒ dos operaciones distintas |
| Reutilización | **Prohibido** reutilizar la misma clave para dos operaciones distintas: la clave identifica una intención, no una sesión |
| Repetición | La operación devuelve el **mismo resultado** (mismo `data`, mismo `success`) con el status HTTP de la primera ejecución. Nunca 500 |
| Conflicto | Misma clave, payload distinto → `409 IDEMPOTENCY_KEY_REUTILIZADA` |

Lo que este servicio **no** hace: guardar el payload. Guarda su **huella**
(SHA-256 de la petición normalizada), de modo que ni el secreto del proveedor
ni un dato personal del comprador queda en la tabla de idempotencia.
"""

import hashlib
import json
import re

from django.db import IntegrityError

from modules.pagos.domain.constants import MAX_LEN_CLAVE_IDEMPOTENCIA
from modules.pagos.domain.exceptions import (
    IdempotencyKeyInvalidaError,
    IdempotencyKeyReutilizadaError,
)
from modules.pagos.domain.models import RegistroIdempotencia

#: Caracteres admitidos en una clave de idempotencia.
RE_CLAVE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


class IdempotenciaPagoService:
    """Registro y consulta de las claves de idempotencia."""

    # ── Validación y huella ─────────────────────────────────────────────────

    @staticmethod
    def normalizar_clave(clave: str | None) -> str:
        """Valida la clave y devuelve su forma canónica.

        Args:
            clave: la clave cruda que llegó en el header.

        Returns:
            La clave validada.

        Raises:
            IdempotencyKeyInvalidaError: si está vacía, excede la longitud
                admitida o trae caracteres no permitidos.
        """
        if clave is None:
            return ""
        texto = str(clave).strip()
        if not texto:
            return ""
        if len(texto) > MAX_LEN_CLAVE_IDEMPOTENCIA:
            raise IdempotencyKeyInvalidaError()
        if not RE_CLAVE.match(texto):
            raise IdempotencyKeyInvalidaError()
        return texto

    @staticmethod
    def huella(peticion) -> str:
        """Huella SHA-256 de una petición normalizada.

        La normalización ordena las claves y separa los valores de forma
        estable, de modo que el mismo contenido produce siempre la misma
        huella y dos contenidos distintos producen huellas distintas.

        Args:
            peticion: la petición (diccionario, lista o escalar).

        Returns:
            La huella hexadecimal de 64 caracteres.
        """
        texto = json.dumps(
            peticion,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    # ── Registro ────────────────────────────────────────────────────────────

    def obtener(self, ambito: str, clave: str) -> RegistroIdempotencia | None:
        """El registro de una clave en un ámbito, si existe."""
        if not clave:
            return None
        return (
            RegistroIdempotencia.objects.filter(ambito=ambito, clave=clave).first()
        )

    def registrar(
        self,
        *,
        ambito: str,
        clave: str,
        huella: str,
        respuesta: dict | None = None,
        codigo_estado: int = 200,
    ) -> tuple[RegistroIdempotencia, bool]:
        """Registra la ejecución de una operación idempotente.

        Si la clave ya existe en el ámbito:

        - con la **misma** huella → se devuelve el registro previo y `False`
          (la operación ya se ejecutó: hay que devolver su respuesta, no
          repetirla);
        - con **otra** huella → se lanza `IdempotencyKeyReutilizadaError`.

        Returns:
            La tupla `(registro, repetida)`.
        """
        if not clave:
            raise IdempotencyKeyInvalidaError()

        existente = self.obtener(ambito, clave)
        if existente is not None:
            if existente.huella != huella:
                raise IdempotencyKeyReutilizadaError()
            return existente, True

        try:
            registro = RegistroIdempotencia.objects.create(
                ambito=ambito,
                clave=clave,
                huella=huella,
                respuesta=respuesta or {},
                codigo_estado=codigo_estado,
            )
        except IntegrityError:
            # Otra ejecución con la misma clave ganó la carrera: se relee y se
            # decide con la huella.
            existente = self.obtener(ambito, clave)
            if existente is None:
                raise
            if existente.huella != huella:
                raise IdempotencyKeyReutilizadaError()
            return existente, True

        return registro, False

    def actualizar_respuesta(
        self,
        registro: RegistroIdempotencia,
        *,
        respuesta: dict,
        codigo_estado: int = 200,
    ) -> RegistroIdempotencia:
        """Guarda el resultado de la primera ejecución de la clave.

        Así la repetición devuelve exactamente la misma respuesta, con el
        status HTTP de la primera vez (FR-04 §2.2).
        """
        registro.respuesta = respuesta or {}
        registro.codigo_estado = codigo_estado
        registro.save(update_fields=["respuesta", "codigo_estado", "updated_at"])
        return registro


__all__ = ["IdempotenciaPagoService"]
