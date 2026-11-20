"""Los selectores de la CAPA OPERATIVA del panel de administración.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

Un selector hace UNA cosa: **preguntar a la base de datos**. No proyecta a
HTTP, no conoce la forma del panel, no decide nada.

## La regla que gobierna este archivo

Este módulo **NO es dueño de ningún dato**. Lee los modelos de los módulos
DUEÑOS a través de su capa `domain/models` y **nunca** importa su capa
`presentation/` (`contract/api-wrapper-presenter-contract.md` §1). Las reglas
que el panel necesita —qué es una inscripción viva, qué es una plantilla
completa, cuál es el veredicto de un pago— las siguen declarando los dueños.

Lo que este archivo hace es **contar y filtrar** sobre hechos ya publicados.

## Los filtros del drilldown

El resumen (`RT-ADM-01`) declara un filtro por incidencia. Cada filtro se
atiende aquí, en el listado que lo consume:

| Filtro | Listado | Hecho del dueño |
|---|---|---|
| `estado_pago` | inscripciones | `Inscripcion.cupos_pagados` frente a `cupos_solicitados` |
| `plantilla` | equipos | `Disciplina.minimo_por_equipo` frente a las participaciones activas |
| `estado_operativo` | pagos | `EstadoOperativoPagoService` (dueño `pagos`) |
"""

from django.db.models import F, Q

from modules.administracion.domain.constants import (
    ValorEstadoPago,
    ValorPlantilla,
)
from modules.commerce.domain.constants import OrigenCompra
from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.constants import EstadoParticipacion
from modules.salesianos_fest.domain.models import (
    Equipo,
    Inscripcion,
    Participacion,
)
from modules.usuarios.domain.models import Persona


#: Los ORDENES permitidos de la lista de inscripciones.
ORDENES_INSCRIPCIONES = {
    "created_at": "created_at",
    "estado": "estado",
    "responsable": "responsable__nombres",
    "paquete": "paquete__nombre",
}

#: Los ORDENES permitidos de la lista de equipos.
ORDENES_EQUIPOS = {
    "created_at": "created_at",
    "nombre": "nombre",
    "disciplina": "disciplina__nombre",
}

#: Los ORDENES permitidos de la lista de pagos.
ORDENES_PAGOS = {
    "created_at": "created_at",
    "estado": "estado",
    "monto": "total",
}


class AdminInscripcionSelector:
    """Lectura de las inscripciones de UNA edición."""

    def listar(
        self,
        edicion_id,
        q: str = "",
        ordering: str = "",
        estado_pago: str = "",
    ):
        """El queryset de las inscripciones de la edición, con sus filtros.

        `estado_pago` es el filtro DECLARADO por el resumen (`PENDIENTE` /
        `PAGADO`). Se aplica sobre los campos del DUEÑO de la inscripción:
        `cupos_pagados` frente a `cupos_solicitados`. Es un hecho de la
        inscripción, no una regla de este módulo.
        """
        queryset = (
            Inscripcion.objects.filter(edicion_id=edicion_id)
            .select_related("responsable", "paquete", "edicion")
            .prefetch_related("equipos__disciplina", "participaciones__persona")
        )

        if q:
            filtro = Q()
            for campo in ("responsable__nombres", "responsable__apellidos", "paquete__nombre", "referencia"):
                filtro |= Q(**{campo: q})
            queryset = queryset.filter(filtro)

        if estado_pago == ValorEstadoPago.PENDIENTE:
            queryset = queryset.filter(cupos_pagados__lt=F("cupos_solicitados"))
        elif estado_pago == ValorEstadoPago.PAGADO:
            queryset = queryset.filter(cupos_pagados__gte=F("cupos_solicitados"))

        return queryset.order_by(*self._orden(queryset, ordering, ORDENES_INSCRIPCIONES))

    @staticmethod
    def _orden(queryset, ordering: str, permitidos: dict):
        """El orden pedido, o el orden por defecto.

        Un orden que NO está en la lista blanca se IGNORA: el panel no puede
        pedir una columna que el servidor no publica.
        """
        if ordering in permitidos:
            return [permitidos[ordering]]

        return ["-created_at"]

    def obtener(self, inscripcion_id):
        """La inscripción con sus relaciones, o `None`."""
        return (
            Inscripcion.objects.filter(id=inscripcion_id)
            .select_related("responsable", "paquete", "edicion")
            .first()
        )

    def equipos_de(self, inscripcion_id):
        """Los equipos de la inscripción, con su disciplina."""
        return list(
            Equipo.objects.filter(inscripcion_id=inscripcion_id)
            .select_related("disciplina", "inscripcion__responsable", "inscripcion__edicion")
            .prefetch_related("participaciones__persona")
        )

    def participaciones_de(self, inscripcion_id):
        """Las participaciones de la inscripción, con su persona y su equipo."""
        return list(
            Participacion.objects.filter(inscripcion_id=inscripcion_id)
            .select_related("persona", "equipo__disciplina", "edicion")
        )

    def personas_de(self, inscripcion_id):
        """Cuántas personas distintas participan en la inscripción."""
        return (
            Participacion.objects.filter(inscripcion_id=inscripcion_id)
            .values("persona_id")
            .distinct()
            .count()
        )


class AdminEquipoSelector:
    """Lectura de los equipos de UNA edición."""

    def listar(
        self,
        edicion_id,
        q: str = "",
        ordering: str = "",
        plantilla: str = "",
    ):
        """El queryset de los equipos de la edición, con sus filtros.

        `plantilla` es el filtro DECLARADO por el resumen (`INCOMPLETA` /
        `COMPLETA`). La regla de "plantilla completa" la publica la
        DISCIPLINA del dueño (`minimo_por_equipo`): aquí sólo se compara el
        número de participaciones activas contra ese mínimo publicado.
        """
        queryset = (
            Equipo.objects.filter(inscripcion__edicion_id=edicion_id)
            .select_related(
                "disciplina",
                "inscripcion__responsable",
                "inscripcion__edicion",
                "inscripcion__paquete",
            )
            .prefetch_related("participaciones__persona")
        )

        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q)
                | Q(disciplina__nombre__icontains=q)
                | Q(inscripcion__responsable__nombres__icontains=q)
                | Q(inscripcion__responsable__apellidos__icontains=q)
            )

        if plantilla:
            incompletos = self._ids_incompletos(edicion_id)
            if plantilla == ValorPlantilla.INCOMPLETA:
                queryset = queryset.filter(id__in=incompletos)
            elif plantilla == ValorPlantilla.COMPLETA:
                queryset = queryset.exclude(id__in=incompletos)

        if ordering in ORDENES_EQUIPOS:
            return queryset.order_by(ORDENES_EQUIPOS[ordering])

        return queryset.order_by("-created_at")

    def _ids_incompletos(self, edicion_id) -> set:
        """Los equipos cuya plantilla NO llega al mínimo de su disciplina.

        El mínimo es del dueño (`Disciplina.minimo_por_equipo`). Este módulo
        compara; no decide qué es una plantilla completa.
        """
        incompletos = set()

        for equipo in (
            Equipo.objects.filter(inscripcion__edicion_id=edicion_id)
            .select_related("disciplina")
            .prefetch_related("participaciones")
        ):
            activos = self.activos_de(equipo)

            if activos < (equipo.disciplina.minimo_por_equipo or 0):
                incompletos.add(equipo.id)

        return incompletos

    @staticmethod
    def activos_de(equipo) -> int:
        """Cuántas participaciones ACTIVAS tiene el equipo."""
        return sum(
            1
            for participacion in equipo.participaciones.all()
            if participacion.estado == EstadoParticipacion.ACTIVA
        )

    def obtener(self, equipo_id):
        """El equipo con sus relaciones, o `None`."""
        return (
            Equipo.objects.filter(id=equipo_id)
            .select_related(
                "disciplina",
                "inscripcion__responsable",
                "inscripcion__edicion",
                "inscripcion__paquete",
            )
            .prefetch_related("participaciones__persona")
            .first()
        )


class AdminParticipanteSelector:
    """Lectura de las personas que participan en UNA edición."""

    def listar(self, edicion_id, q: str = ""):
        """Las personas con participaciones en la edición."""
        queryset = Persona.objects.filter(
            participaciones_inscripcion__edicion_id=edicion_id
        ).distinct()

        if q:
            queryset = queryset.filter(
                Q(nombres__icontains=q)
                | Q(apellidos__icontains=q)
                | Q(numero_documento__icontains=q)
            )

        return queryset.order_by("apellidos", "nombres")

    def participaciones_de(self, persona_id, edicion_id=None):
        """Las participaciones de una persona, con su edición y su disciplina."""
        queryset = Participacion.objects.filter(persona_id=persona_id).select_related(
            "edicion", "equipo__disciplina", "equipo"
        )

        if edicion_id:
            queryset = queryset.filter(edicion_id=edicion_id)

        return list(queryset)

    def conflictos_de(self, participaciones) -> dict:
        """Los CONFLICTOS de una persona, por participación.

        El conflicto es un hecho CRUZE entre dos participaciones publicadas
        por el dueño: la misma persona activa dos veces en la misma
        disciplina de la misma edición (`RN-I05`). El módulo no decide que
        una participación sea válida: cuenta y publica el solapamiento.
        """
        por_clave: dict = {}

        for participacion in participaciones:
            if participacion.estado != EstadoParticipacion.ACTIVA:
                continue

            clave = (str(participacion.edicion_id), str(participacion.disciplina_id))
            por_clave.setdefault(clave, []).append(participacion)

        conflictos: dict = {}

        for participaciones_activas in por_clave.values():
            if len(participaciones_activas) < 2:
                continue

            for participacion in participaciones_activas:
                conflictos[str(participacion.id)] = participaciones_activas

        return conflictos


class AdminPagoSelector:
    """Lectura de los pagos de UNA edición.

    El alcance llega a `commerce.Compra` por sus dos composiciones reales:
    `CompraPase.edicion` para pases y la referencia canónica de inscripción
    para compras de cupos. La inscripción no tiene una FK de compra: su
    referencia es el vínculo que consume también su activador de derechos.
    """

    def listar(
        self,
        edicion_id,
        q: str = "",
        ordering: str = "",
        estado_operativo: str = "",
        estado_compra: str = "",
        estado_orden: str = "",
        tipo: str = "",
        desde=None,
        hasta=None,
    ):
        """Las compras de pases e inscripciones de la edición."""
        queryset = self._de_edicion(edicion_id)

        if q:
            queryset = queryset.filter(
                Q(referencia__icontains=q)
                | Q(persona__nombres__icontains=q)
                | Q(persona__apellidos__icontains=q)
                | Q(compra_de_pases__pase__nombre__icontains=q)
            )

        if estado_compra:
            queryset = queryset.filter(estado=estado_compra)

        if estado_orden:
            queryset = queryset.filter(orden_pago__estado=estado_orden)

        if tipo:
            queryset = queryset.filter(origen=tipo)

        if desde:
            queryset = queryset.filter(created_at__gte=desde)

        if hasta:
            queryset = queryset.filter(created_at__lte=hasta)

        return queryset.order_by(*self._orden(queryset, ordering))

    @staticmethod
    def _orden(queryset, ordering: str):
        """El orden pedido, o el orden por defecto."""
        if ordering in ORDENES_PAGOS:
            return [ORDENES_PAGOS[ordering]]

        return ["-created_at"]

    @staticmethod
    def _de_edicion(edicion_id):
        """Compras comerciales que pertenecen a la edición solicitada.

        Las compras de inscripción no conservan una FK directa. La referencia
        `INSCRIPCION:{id}:...` es el contrato estable que enlaza compra,
        activación y la inscripción; se construye el alcance desde las
        inscripciones de la edición antes de consultar `commerce.Compra`.
        """
        referencias_inscripcion = Q()
        for inscripcion_id in Inscripcion.objects.filter(
            edicion_id=edicion_id
        ).values_list("id", flat=True):
            referencias_inscripcion |= Q(
                referencia__startswith=f"INSCRIPCION:{inscripcion_id}:"
            )

        alcance = Q(
            origen=OrigenCompra.PASE,
            compra_de_pases__edicion_id=edicion_id,
        )
        if referencias_inscripcion:
            alcance |= Q(
                origen=OrigenCompra.INSCRIPCION,
            ) & referencias_inscripcion

        return Compra.objects.filter(alcance).select_related(
            "orden_pago",
            "persona",
            "compra_de_pases__pase",
        )

    def obtener(self, compra_id):
        """La compra comercial publicada por el panel, o `None`."""
        return (
            Compra.objects.filter(
                id=compra_id,
                origen__in=[OrigenCompra.INSCRIPCION, OrigenCompra.PASE],
            )
            .select_related(
                "orden_pago",
                "persona",
                "compra_de_pases__pase",
            )
            .first()
        )

    def obtener_por_orden(self, orden_pago_id):
        """La compra que financia una orden de pago, o ``None``."""
        return (
            Compra.objects.filter(
                orden_pago_id=orden_pago_id,
                origen__in=[OrigenCompra.INSCRIPCION, OrigenCompra.PASE],
            )
            .select_related(
                "orden_pago",
                "persona",
                "compra_de_pases__pase",
            )
            .first()
        )


class AdminPersonaSelector:
    """Lectura de las personas del sistema (búsqueda administrativa)."""

    def listar(self, q: str = "", edicion_id=None):
        """Las personas que casan con la búsqueda."""
        queryset = Persona.objects.all()

        if edicion_id:
            queryset = queryset.filter(
                participaciones_inscripcion__edicion_id=edicion_id
            ).distinct()

        if q:
            queryset = queryset.filter(
                Q(nombres__icontains=q)
                | Q(apellidos__icontains=q)
                | Q(numero_documento__icontains=q)
            )

        return queryset.order_by("apellidos", "nombres")

    def obtener(self, persona_id):
        """La persona con sus relaciones, o `None`."""
        return Persona.objects.filter(id=persona_id).first()


__all__ = [
    "AdminEquipoSelector",
    "AdminInscripcionSelector",
    "AdminParticipanteSelector",
    "AdminPagoSelector",
    "AdminPersonaSelector",
    "ORDENES_EQUIPOS",
    "ORDENES_INSCRIPCIONES",
    "ORDENES_PAGOS",
]
