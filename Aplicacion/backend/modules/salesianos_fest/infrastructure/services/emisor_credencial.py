"""El adaptador de EMISIÓN de credenciales del módulo `salesianos_fest`.

Change: `administracion-pases-alta-directa` · Apply C

Este adaptador es el PRODUCTOR del puerto `IEmisorCredencialService`: el
CONSUMIDOR (`validaciones`) declara el contrato y este módulo lo implementa,
porque es el DUEÑO de los derechos de ENTRADA (`PaseBeneficiario`).

**LA REGLA ES DE AQUÍ.** El tipo de la credencial lo decide el dueño del
derecho: una entrada de CORTESÍA es `ENTRADA_CORTESIA` y un pase COMPRADO es
`PASE`. El navegador NUNCA lo declara (`RN-U04`): declara QUIÉN tiene el
derecho, y el servidor dice QUÉ credencial corresponde.

**LA OPERACIÓN NO SE INVENTA.** La operación la publica el mapa único de
`validaciones` (`OPERACION_POR_TIPO_DERECHO`): un pase es `INGRESO` y un
producto es `ENTREGA`. Aquí no hay una segunda copia de esa regla.

**NO SE IMPORTA EL MODELO DE LA CREDENCIAL.** Este adaptador no conoce el
`Ticket`: sólo resuelve el DERECHO y devuelve su referencia. La credencial la
crea su dueño (`validaciones`).
"""

from modules.salesianos_fest.domain.constants import OrigenDerechoPase
from modules.salesianos_fest.domain.exceptions import (
    PaseBeneficiarioNoEncontradoError,
)
from modules.salesianos_fest.domain.models import PaseBeneficiario
from modules.validaciones.domain.constants import (
    OPERACION_POR_TIPO_DERECHO,
    TipoDerechoChoices,
)
from modules.validaciones.domain.ports.emisor_credencial import (
    IEmisorCredencialService,
    ReferenciaCredencial,
)


class EmisorCredencialService(IEmisorCredencialService):
    """Resuelve el derecho de entrada y deriva su tipo y su operación."""

    def resolver_referencia(self, derecho_id: str) -> ReferenciaCredencial:
        """La referencia al derecho de entrada indicado.

        Raises:
            PaseBeneficiarioNoEncontradoError: el derecho no existe (404).
        """
        derecho = (
            PaseBeneficiario.objects.filter(id=derecho_id)
            .select_related("edicion", "pase")
            .first()
        )
        if derecho is None:
            raise PaseBeneficiarioNoEncontradoError()

        tipo = (
            TipoDerechoChoices.ENTRADA_CORTESIA
            if derecho.origen == OrigenDerechoPase.CORTESIA
            else TipoDerechoChoices.PASE
        )
        return ReferenciaCredencial(
            derecho_id=str(derecho.id),
            edicion_id=str(derecho.edicion_id),
            tipo_derecho=tipo,
            operacion=OPERACION_POR_TIPO_DERECHO[tipo],
        )


__all__ = ["EmisorCredencialService"]
