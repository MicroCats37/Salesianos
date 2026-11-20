"""`PatrocinadorController` — superficie HTTP del módulo `patrocinadores`.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/django-app-architecture-contract.md` §4.8 ·
          `contract/api-wrapper-presenter-contract.md` §2, §8

Controller DELGADO: hidrata la entrada, llama al orquestador y devuelve el
éxito formateado por el presenter. Cero `if` de negocio, cero ORM, cero
respuestas de error manuales (los errores los construye el catálogo de
`core/exceptions.py` a partir del código estable de la excepción).

Rutas (ledger FR-07 §3.3):

| Ruta | Método | Scope | Permiso | Errores |
|---|---|---|---|---|
| `/patrocinadores` | POST | implícito | `Administrador` | `MEDIA_TIPO_NO_PERMITIDO` 400 · `MEDIA_ARCHIVO_HUERFANO` 400 · `MEDIA_TOKEN_NO_RESUELTO` 400 · `MEDIA_TOKEN_DUPLICADO` 400 · `MEDIA_TAMANO_EXCEDIDO` 413 · `PATROCINADOR_SLUG_DUPLICADO` 409 |

**La superficie HTTP de este módulo es la ÚNICA que declara el ledger**
(FR-07 §3.3, fila `RT-MD-02`). El resto de las capacidades —actualizar la
ficha, cambiar la visibilidad, reordenar la galería, reemplazar el logo o una
imagen, y eliminar— existen como CAPACIDADES DE DOMINIO (`PatrocinadorFlujo`),
con sus tipos y sus pruebas, pero NO se exponen por HTTP: inventar rutas que
el ledger no declara es decisión de A0 (petición A0-04 de la evidencia de
DOM-08). Los shapes de lectura (`PatrocinadorOut` y sus bloques) quedan
CONGELADOS para que API-05 pueda espejarlos.

NOTA DE REGISTRO: una ruta no existe hasta que su controller está registrado
en `config/api.py` (FR-07 §3.1 regla 2). Ese registro es de A0 y este paquete
NO edita `config/api.py`: lo pide como evidencia (petición A0-02).
"""

from injector import inject
from ninja_extra import api_controller, route

from core.permissions import RequireAdmin
from core.responses import ApiResponse, success_response
from modules.patrocinadores.domain.services.orchestrators.patrocinador_orchestrator import (
    PatrocinadorOrchestrator,
)
from modules.patrocinadores.presentation.hydration.patrocinadores_hydrator import (
    PatrocinadorHydrator,
)
from modules.patrocinadores.presentation.presenters.patrocinadores_presenter import (
    PatrocinadorPresenter,
)
from modules.patrocinadores.presentation.schemas.patrocinadores_schemas import (
    CrearPatrocinadorIn,  # noqa: F401  (schema de entrada del ledger, documentado)
    PatrocinadorOut,
)


@api_controller("/patrocinadores", tags=["Patrocinadores"])
class PatrocinadorController:
    """Superficie HTTP de los patrocinadores."""

    @inject
    def __init__(self, orchestrator: PatrocinadorOrchestrator):
        self.orchestrator = orchestrator

    # ── RT-MD-02 · POST /patrocinadores ────────────────────────────────────

    @route.post(
        "",
        response={200: ApiResponse[PatrocinadorOut]},
        summary="Alta de un patrocinador con su logo y su galería ordenada",
        permissions=[RequireAdmin],
    )
    async def crear_patrocinador(self, request):
        """Alta de un patrocinador.

        Route: POST /api/patrocinadores

        Acepta el protocolo multipart congelado (FR-06 §2.4): el campo `data`
        con el JSON del payload y el campo `files` con las partes
        `<token>___<realname>`. También acepta JSON para el alta SIN
        imágenes.

        El alcance (edición) lo resuelve el servidor; el cliente no lo
        elige.

        El logo viaja como un token (`"logo": "file_<uuid>"`) y la galería
        como una lista ordenada de objetos con su token y su texto
        alternativo. Cada token aparece EXACTAMENTE UNA VEZ en el payload.
        """
        data = PatrocinadorHydrator.hydrate(request)
        result = await self.orchestrator.crear_patrocinador(data)
        return success_response(PatrocinadorPresenter.present(result))


__all__ = ["PatrocinadorController"]
