"""`CapacidadCoreService` — el saldo de cupos de una inscripción.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio (la aporta quien los usa).

Este servicio es el ÚNICO que mueve los contadores de capacidad, y los mueve
con **sentencias ATÓMICAS CONDICIONALES** (`UPDATE ... WHERE ...`), no con
lectura-modificación-escritura. Ésa es la razón por la que dos asignaciones
simultáneas NO pueden sobre-suscribir el pool (`QA-I05`, `RN-I03`).

| Operación | Sentencia | Garantía |
|---|---|---|
| `reservar_cupo` | `UPDATE ... WHERE cupos_asignados < cupos_pagados` | el saldo disponible nunca baja de cero y nunca hay sobre-suscripción |
| `liberar_cupo` | `UPDATE ... WHERE cupos_asignados > 0` | el contador nunca baja de cero |
| `habilitar_cupos_pagados` | `UPDATE ... SET cupos_pagados = cupos_pagados + n` | la capacidad pagada sólo crece por ACTIVACIÓN de derechos (`RN-I02`) |

La restricción `fest_inscripcion_asignados_no_superan_pagados` de la base de
datos es la segunda línea de defensa: aunque una escritura se colase, la
base de datos rechaza el saldo negativo.
"""

from django.db.models import F

from modules.salesianos_fest.domain.models import Inscripcion


class CapacidadCoreService:
    """Operaciones atómicas sobre el saldo de cupos de una inscripción."""

    def reservar_cupo(self, inscripcion_id) -> bool:
        """Reserva UN cupo de la inscripción, si hay disponibilidad.

        Es un único `UPDATE` condicional: la condición `cupos_asignados <
        cupos_pagados` viaja DENTRO de la sentencia, así que dos llamadas
        concurrentes no pueden sobre-suscribir el pool. La segunda simply no
        actualiza ninguna fila y devuelve `False`.

        Args:
            inscripcion_id: identificador de la inscripción.

        Returns:
            `True` si el cupo quedó reservado; `False` si no había
            disponibilidad.
        """
        actualizadas = Inscripcion.objects.filter(
            id=inscripcion_id,
            cupos_asignados__lt=F("cupos_pagados"),
        ).update(cupos_asignados=F("cupos_asignados") + 1)
        return actualizadas == 1

    def liberar_cupo(self, inscripcion_id) -> bool:
        """Libera UN cupo de la inscripción.

        Nunca deja el contador en negativo: la condición `cupos_asignados >
        0` viaja dentro de la sentencia.

        Args:
            inscripcion_id: identificador de la inscripción.

        Returns:
            `True` si el cupo quedó liberado.
        """
        actualizadas = Inscripcion.objects.filter(
            id=inscripcion_id,
            cupos_asignados__gt=0,
        ).update(cupos_asignados=F("cupos_asignados") - 1)
        return actualizadas == 1

    def habilitar_cupos_pagados(self, inscripcion_id, cantidad: int) -> None:
        """Suma `cantidad` cupos a la capacidad PAGADA de la inscripción.

        Sólo lo llama la ACTIVACIÓN de derechos: una compra pendiente no
        habilita ningún cupo (`RN-I02`, `QA-I01`).

        Args:
            inscripcion_id: identificador de la inscripción.
            cantidad: cupos que se habilitan. Siempre mayor que cero.
        """
        if cantidad <= 0:
            return
        Inscripcion.objects.filter(id=inscripcion_id).update(
            cupos_pagados=F("cupos_pagados") + cantidad
        )


__all__ = ["CapacidadCoreService"]
