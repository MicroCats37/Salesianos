"""
Helpers to reproduce the LEGACY data of a deployment.

The database guard of the payment attempts refuses a SECOND live attempt of
the same order — exactly the state that a legacy deployment can carry: the
attempts of the old checkout flow piled up as PENDIENTE records.

To test the preflight (and the retirement of the legacy duplicates) that
state has to be reproduced with the guard temporarily removed. The helpers
below remove the partial unique index with the schema editor of Django and
restore it right after: the payment DATA is never modified.

The helpers are plain functions so they can be used from a synchronous test
and from an asynchronous one (`await sync_to_async(...)()`).
"""
from django.db import connection

from modules.pagos.domain.models import TransaccionPago

NOMBRE_RESTRICCION_INTENTO_ACTIVO = "uniq_transpago_activo_orden"


def restriccion_de_intento_activo():
    """Return the partial unique constraint of the live attempt."""
    for constraint in TransaccionPago._meta.constraints:
        if constraint.name == NOMBRE_RESTRICCION_INTENTO_ACTIVO:
            return constraint
    raise AssertionError(
        "La restricción de intento único no está declarada en el modelo "
        f"'{NOMBRE_RESTRICCION_INTENTO_ACTIVO}': el estado heredado no se "
        "puede reproducir."
    )


def quitar_guard_de_intento_activo() -> None:
    """Remove the partial unique index of the live attempt."""
    with connection.schema_editor() as editor:
        editor.remove_constraint(TransaccionPago, restriccion_de_intento_activo())


def restaurar_guard_de_intento_activo() -> None:
    """Restore the partial unique index of the live attempt."""
    with connection.schema_editor() as editor:
        editor.add_constraint(TransaccionPago, restriccion_de_intento_activo())
