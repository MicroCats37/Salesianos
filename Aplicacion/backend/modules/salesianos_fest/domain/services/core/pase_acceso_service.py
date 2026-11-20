"""`PaseAccesoService` — quién puede abrir un lote de pases.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio.

El acceso a la compra de un lote tiene TRES credenciales posibles, y sólo
una basta:

| Credencial | Cuándo | Autoridad |
|---|---|---|
| **Administrador** | siempre | `core.capacidades.es_admin` — la ÚNICA mapa de permisos del proyecto (FND-01) |
| **Titular autenticado** | con cuenta | el actor es la persona COMPRADORA del lote (`FR-03` §2.1) |
| **Token privado** | sin cuenta | el enlace de gestión, de ÁMBITO POR COMPRA (`contratos/02` §5) |

**El DNI NUNCA es una credencial** (`RN-U04`, `contratos/02` §5 regla 6): un
invitado nunca puede consultar la compra de otra persona únicamente por
documento. El token es lo que abre el enlace, y el token se entrega EN EL
MOMENTO DE LA COMPRA, sólo a quien compró.

**401 antes que 403**: si no hay ninguna credencial (ni cuenta ni token) la
respuesta es 401 —falta autenticación—; si hay una credencial pero no
autoriza, es 403. Un token inválido, expirado o revocado es un fallo de
AUTENTICACIÓN de esa credencial: 401.
"""

import secrets

from django.utils import timezone
from injector import inject

from core.capacidades import es_admin
from modules.salesianos_fest.domain.exceptions import (
    CompraPaseNoAutorizadaError,
    TokenPaseInvalidoError,
)
from modules.salesianos_fest.domain.ports import ITitularidadService


class PaseAccesoService:
    """La comprobación de acceso a un lote de pases."""

    @inject
    def __init__(self, titularidad: ITitularidadService | None = None):
        from modules.salesianos_fest.infrastructure.services import (
            TitularidadAdapter,
        )

        self.titularidad = titularidad or TitularidadAdapter()

    def verificar(
        self,
        *,
        actor,
        token: str | None,
        compra_pase,
    ) -> None:
        """Verifica que el actor puede abrir el lote.

        Args:
            actor: la cuenta autenticada, o `None` si la petición es
                anónima.
            token: el token privado de gestión, o `None`.
            compra_pase: el lote que se quiere abrir.

        Raises:
            TokenPaseInvalidoError: no hay credencial válida (401).
            CompraPaseNoAutorizadaError: hay credencial pero no autoriza
                (403).
        """
        if actor is not None and getattr(actor, "is_authenticated", False):
            if es_admin(actor):
                return
            persona_id = self.titularidad.persona_id_del_actor(actor)
            if persona_id and str(persona_id) == str(compra_pase.comprador_id):
                return
            raise CompraPaseNoAutorizadaError()

        # Sin cuenta, la credencial es el TOKEN del enlace.
        if not self._token_valido(compra_pase, token):
            raise TokenPaseInvalidoError()

    @staticmethod
    def _token_valido(compra_pase, token: str | None) -> bool:
        """Si el token abre ESTE lote y sigue vivo.

        El token es de ÁMBITO POR COMPRA: el token de otro lote no abre
        éste. La comparación es en TIEMPO CONSTANTE (`secrets.compare_digest`)
        para no filtrar información por el tiempo de respuesta.
        """
        if not token:
            return False
        if compra_pase.token_revocado_en is not None:
            return False
        if (
            compra_pase.token_expira_en is not None
            and compra_pase.token_expira_en <= timezone.now()
        ):
            return False
        return secrets.compare_digest(
            str(compra_pase.token or ""),
            str(token),
        )


__all__ = ["PaseAccesoService"]
