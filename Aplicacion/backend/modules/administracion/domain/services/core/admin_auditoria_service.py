"""`AdminAuditoriaService` — la escritura del ACTA transversal.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

El servicio es el ÚNICO que escribe el acta. Hace tres cosas y ninguna más:

1. **Exige el motivo.** Un comando sensible sin motivo no se ejecuta: la
   ausencia de motivo es un 422, no un acta con el motivo vacío.
2. **Sanea el contexto.** Las claves prohibidas no se guardan NUNCA y los
   valores se acotan. El acta no es un volcado del cuerpo de la petición.
3. **Congela la identidad del actor.** Se guarda la FOTO del actor (su nombre)
   para que el acta siga siendo legible aunque la cuenta se dé de baja.

Contrato: `contract/django-app-architecture-contract.md` §10 — las respuestas
públicas nunca exponen texto crudo, y el acta tampoco guarda secretos.
"""

from typing import Any, Dict, Optional

from core.exceptions import UnprocessableEntityError
from modules.administracion.domain.models import AccionAuditada

#: Claves cuyo contenido NUNCA se guarda en el acta.
CLAVES_PROHIBIDAS = frozenset(
    {
        "password",
        "contrasena",
        "token",
        "secret",
        "secreto",
        "authorization",
        "cookie",
        "apikey",
        "clave",
        "signature",
        "cvv",
        "tarjeta",
        "pin",
        "session",
        "bearer",
    }
)

#: Longitud máxima de un valor del contexto auditable.
MAX_LEN_VALOR = 200


def _normalizar(clave: str) -> str:
    """La clave sin mayúsculas ni separadores, para comparar de forma estable."""
    return "".join(caracter for caracter in clave.lower() if caracter.isalnum())


def sanear_datos(datos: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """El contexto auditable, sin secretos y acotado.

    Una clave prohibida NO SE ELIMINA en silencio del lado del llamador: se
    descarta del acta y el resto viaja. El ACTA dice lo que pasó, no lo que se
    mandó.
    """
    if not datos:
        return {}

    limpio: Dict[str, Any] = {}

    for clave, valor in datos.items():
        if _normalizar(str(clave)) in CLAVES_PROHIBIDAS:
            continue

        if valor is None or isinstance(valor, (bool, int, float)):
            limpio[str(clave)] = valor
            continue

        texto = str(valor)
        limpio[str(clave)] = texto[:MAX_LEN_VALOR]

    return limpio


class AdminAuditoriaService:
    """La escritura del acta de auditoría."""

    def registrar(
        self,
        actor,
        accion: str,
        entidad: str,
        motivo: str,
        edicion_id=None,
        entidad_id: str = "",
        datos: Optional[Dict[str, Any]] = None,
    ) -> AccionAuditada:
        """Registra el acta de una acción sensible.

        Exige el motivo: sin motivo la acción no es auditable y no se
        registra. El motivo vacío es un 422 (`VALIDATION_ERROR`).
        """
        texto_motivo = (motivo or "").strip()

        if not texto_motivo:
            raise UnprocessableEntityError(
                "La acción requiere un motivo.",
                code="MOTIVO_REQUERIDO",
            )

        return AccionAuditada.objects.create(
            edicion_id=edicion_id,
            actor_usuario=actor if getattr(actor, "is_authenticated", False) else None,
            actor_nombre=self._nombre_del_actor(actor),
            accion=str(accion or "").strip(),
            entidad=str(entidad or "").strip(),
            entidad_id=str(entidad_id or ""),
            motivo=texto_motivo,
            datos=sanear_datos(datos),
        )

    @staticmethod
    def _nombre_del_actor(actor) -> str:
        """La foto legible del actor. Nunca su identificador interno."""
        if actor is None:
            return "Sistema"

        for atributo in ("get_username", "get_full_name"):
            metodo = getattr(actor, atributo, None)

            if callable(metodo):
                try:
                    valor = str(metodo() or "").strip()
                except Exception:  # pragma: no cover - defensivo
                    valor = ""

                if valor:
                    return valor[:160]

        return "Sistema"


__all__ = ["AdminAuditoriaService", "CLAVES_PROHIBIDAS", "sanear_datos"]
