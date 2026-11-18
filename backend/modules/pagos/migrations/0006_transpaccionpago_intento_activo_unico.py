"""
Install the one-live-attempt guard of the payment attempts.

A live attempt is a PENDIENTE TransaccionPago: it records that a provider
session was opened for an order. The unique partial index installed here
REFUSES a second live attempt of the same order — the hard backstop of the
atomic attempt lifecycle of the flow (the flow retires the live attempt
before it creates the fresh one, inside ONE transaction).

The index is installed ONLY when the deployment data is clean: the guard below
reads the live attempts and refuses the installation when an order already
carries more than one of them. Nothing is ever mutated automatically — a
payment attempt is an audit record and it may be money in flight: the
operator resolves the unsafe rows explicitly (see
`backend/modules/pagos/docs/despliegue_intento_unico.md`).

Reversal removes the index and touches NO data: the attempts of every order
stay exactly as they are.
"""
from django.db import migrations, models
from django.db.models import Count

ESTADO_INTENTO_VIVO = "PENDIENTE"

NOMBRE_RESTRICCION = "uniq_transpago_activo_orden"

MENSAJE_DATOS_INSEGUROS = (
    "No se puede instalar la restricción de intento único: hay órdenes con "
    "más de un intento vivo (PENDIENTE). Ejecuta "
    "'python manage.py verificar_intentos_pago' para listarlas y resuélvelas "
    "explícitamente antes de volver a aplicar la migración."
)


def exigir_datos_limpios(apps, schema_editor):
    """
    Refuse the installation of the guard when the data is not clean.

    The check is READ-ONLY: it counts the live attempts of every order and
    raises when one of them carries more than one. The migration is then
    rolled back and the database keeps its current shape.
    """
    TransaccionPago = apps.get_model("pagos", "TransaccionPago")

    inseguras = (
        TransaccionPago.objects
        .filter(status=ESTADO_INTENTO_VIVO)
        .values("orden_pago_id")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .count()
    )

    if inseguras:
        raise RuntimeError(MENSAJE_DATOS_INSEGUROS)


class Migration(migrations.Migration):

    dependencies = [
        ("pagos", "0005_aprobacion_pago_manual"),
    ]

    operations = [
        # The gate: the guard is installed only when the data is clean.
        migrations.RunPython(exigir_datos_limpios, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="transaccionpago",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", ESTADO_INTENTO_VIVO)),
                fields=("orden_pago",),
                name=NOMBRE_RESTRICCION,
            ),
        ),
    ]
