"""El ACTA de cada operación protegida del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

`RN-K02`: los encuentros tienen "programación, participantes, resultado,
vencedor, estado y AUDITORÍA".

Este módulo registra su propia auditoría en una tabla explícita
(`AuditoriaOperacion`), en vez de delegar en un historial automático:

- el ACTA es un HECHO de negocio: existe aunque el dato que audita cambie
  después. Un historial automático describe el ESTADO; un acta describe la
  OPERACIÓN;
- el ACTA nunca se borra: una corrección posterior no borra la corrección
  anterior, la deja como antecedente (`frontend/05` §3);
- el `detalle` guarda el antes/después. Es contexto TÉCNICO del servidor:
  NUNCA se publica en una respuesta HTTP.

El `actor` es la cuenta que ejecutó la operación. Es opcional porque una
operación puede ejecutarse desde un proceso (una migración, un comando) sin
un actor autenticado.
"""

from modules.competencias.domain.models.auditoria import (
    AccionAuditada,
    AuditoriaOperacion,
)


class AuditoriaCoreService:
    """Escritura del acta de las operaciones protegidas.

    El servicio es SYNC y NO abre transacción: la escribe el flujo, dentro de
    la misma atomicidad que el cambio que audita.
    """

    def registrar(
        self,
        *,
        accion: str,
        motivo: str,
        competencia=None,
        encuentro=None,
        actor=None,
        detalle: dict | None = None,
    ) -> AuditoriaOperacion:
        """Registra el acta de la operación.

        Args:
            accion: código de `AccionAuditada`.
            motivo: motivo auditado (5..500 caracteres).
            competencia: competencia afectada, si la hay.
            encuentro: encuentro afectado, si lo hay.
            actor: cuenta que ejecutó la operación, si la hay.
            detalle: antes/después. Contexto técnico: nunca se publica.

        Returns:
            El acta registrada.
        """
        return AuditoriaOperacion.objects.create(
            competencia=competencia,
            encuentro=encuentro,
            accion=accion,
            actor=actor,
            motivo=motivo,
            detalle=detalle or {},
        )


__all__ = ["AccionAuditada", "AuditoriaCoreService"]
