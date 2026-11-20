"""`AdminOperacionService` — la COMPOSICIÓN del modelo de lectura del panel.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

Este servicio es sync (`contract/django-app-architecture-contract.md` §4.3) y
NO abre `transaction.atomic()`: la transacción la abre el flujo que la
necesita.

## Lo que hace

Proyecta los HECHOS que los módulos DUEÑOS publican a las formas que el
panel lee. No consulta la regla: la pide.

| Hecho | Dueño | Cómo se obtiene |
|---|---|---|
| el veredicto del pago | `pagos` | `EstadoOperativoPagoService.calcular_para_orden` |
| los intentos del proveedor | `pagos` | `TransaccionPagoSelector.listar_por_orden` |
| el pool y sus impedimentos | `salesianos_fest` | `PoolFlujo.obtener_pool` (lo llama el orquestador) |
| el mínimo de la plantilla | `salesianos_fest` | `Disciplina.minimo_por_equipo` |
| los estados de la inscripción | `salesianos_fest` | `EstadoInscripcion` |

## Lo que NO hace

- **No reimplementa ninguna regla.** El "estado operativo" de un pago lo
  calcula el dueño; aquí sólo se copia su resultado.
- **No calcula importes.** El total y la moneda son los que la compra
  congeló (`FR-04`).
- **No inventa relaciones.** Lo que el objetivo no relaciona no se publica.
"""

from injector import inject

from modules.administracion.domain.constants import (
    CodigoAccionOperativa,
    CodigoAlertaAdmin,
    DESCRIPCIONES_ESTADO_ADMIN,
    MENSAJES_ACCION_ADMIN,
    MENSAJES_ALERTA_ADMIN,
    ValorEstadoPago,
    ValorPlantilla,
)
from modules.administracion.domain.results.admin_operacion_results import (
    AccionOperativaAdminResultado,
    AdminEquipoDetalleAdminResultado,
    AdminEquipoListItemAdminResultado,
    AdminInscripcionDetalleAdminResultado,
    AdminInscripcionListItemAdminResultado,
    AdminPagoDetalleAdminResultado,
    AdminPagoListItemAdminResultado,
    AdminPersonaDetalleAdminResultado,
    CausaAdminResultado,
    CompraAdminResultado,
    CompradorAdminResultado,
    CuposOperativosAdminResultado,
    EntregaDerechosAdminResultado,
    EquipoDeInscripcionAdminResultado,
    EventoHistorialAdminResultado,
    IntentoPagoAdminResultado,
    OperacionManualAdminResultado,
    ParticipacionAdminResultado,
    ParticipacionPoolAdminResultado,
    ParticipanteAdminResultado,
    ParticipanteDeEquipoAdminResultado,
    PersonaAdminResultado,
    PlantillaEquipoAdminResultado,
    PoolAdminResultado,
    ReferenciaAdminResultado,
    EstadoOperativoAdminResultado,
)
from modules.administracion.domain.selectors.admin_operacion_selector import (
    AdminEquipoSelector,
    AdminInscripcionSelector,
    AdminParticipanteSelector,
    AdminPagoSelector,
    AdminPersonaSelector,
)
from modules.administracion.domain.models import AccionAuditada
from modules.pagos.domain.constants import EstadoTransaccionPago, OrigenPago
from modules.pagos.domain.models import AprobacionPagoManual
from modules.pagos.domain.services.core.estado_operativo_pago_service import (
    EstadoOperativoPagoService,
)
from modules.salesianos_fest.domain.referencia import parsear_referencia
from modules.salesianos_fest.domain.constants import (
    EstadoInscripcion,
    EstadoParticipacion,
)


#: La vista operativa a la que apunta la acción de una fila.
VISTA_PAGOS = "/administracion/pagos"
VISTA_EQUIPOS = "/administracion/equipos"


class AdminOperacionService:
    """Compone el modelo de lectura operativo del panel."""

    @inject
    def __init__(
        self,
        inscripcion_selector: AdminInscripcionSelector,
        equipo_selector: AdminEquipoSelector,
        participante_selector: AdminParticipanteSelector,
        pago_selector: AdminPagoSelector,
        persona_selector: AdminPersonaSelector,
        estado_operativo_pago: EstadoOperativoPagoService,
    ):
        self.inscripcion_selector = inscripcion_selector
        self.equipo_selector = equipo_selector
        self.participante_selector = participante_selector
        self.pago_selector = pago_selector
        self.persona_selector = persona_selector
        self.estado_operativo_pago = estado_operativo_pago

    # ── Inscripciones (RT-IN-07 · RT-IN-08) ──────────────────────────────────

    def listar_inscripciones(
        self,
        edicion_id,
        q: str = "",
        ordering: str = "",
        estado_pago: str = "",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Las inscripciones de la edición, paginadas.

        Devuelve `(items, total, page, page_size, total_pages)`: la forma de
        paginación del objetivo es UNA (`FREEZE-ENV-1.0.0` §4.3).
        """
        queryset = self.inscripcion_selector.listar(
            edicion_id, q=q, ordering=ordering, estado_pago=estado_pago
        )
        total = queryset.count()
        pagina, tamano, inicio = self._paginar(total, page, page_size)
        filas = list(queryset[inicio:inicio + tamano])

        return (
            [self._fila_inscripcion(fila) for fila in filas],
            total,
            pagina,
            tamano,
            self._paginas(total, tamano),
        )

    def obtener_inscripcion(self, inscripcion_id, pool=None) -> tuple:
        """El detalle de una inscripción, o `None` si no existe.

        `pool` es el `PoolResult` que publica el DUEÑO (`PoolFlujo`): este
        servicio no reconstruye el pool.
        """
        inscripcion = self.inscripcion_selector.obtener(inscripcion_id)

        if inscripcion is None:
            return None

        equipos = self.inscripcion_selector.equipos_de(inscripcion_id)
        participaciones = self.inscripcion_selector.participaciones_de(inscripcion_id)
        personas = self.inscripcion_selector.personas_de(inscripcion_id)

        return AdminInscripcionDetalleAdminResultado(
            item=self._fila_inscripcion(inscripcion, equipos=equipos, personas=personas),
            equipos_detalle=[
                self._equipo_de_inscripcion(equipo) for equipo in equipos
            ],
            pool=self.proyectar_pool(pool),
            compras=[],
            historial=self._historial("INSCRIPCION", str(inscripcion.id)),
        )

    # ── Equipos (RT-IN-09 · RT-IN-10) ────────────────────────────────────────

    def listar_equipos(
        self,
        edicion_id,
        q: str = "",
        ordering: str = "",
        plantilla: str = "",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Los equipos de la edición, paginados."""
        queryset = self.equipo_selector.listar(
            edicion_id, q=q, ordering=ordering, plantilla=plantilla
        )
        total = queryset.count()
        pagina, tamano, inicio = self._paginar(total, page, page_size)
        filas = list(queryset[inicio:inicio + tamano])

        return (
            [self._fila_equipo(fila) for fila in filas],
            total,
            pagina,
            tamano,
            self._paginas(total, tamano),
        )

    def obtener_equipo(self, equipo_id) -> tuple:
        """El detalle de un equipo, o `None` si no existe."""
        equipo = self.equipo_selector.obtener(equipo_id)

        if equipo is None:
            return None

        participantes = [
            self._participante_de_equipo(participacion)
            for participacion in equipo.participaciones.all()
            if participacion.estado == EstadoParticipacion.ACTIVA
        ]
        inscripcion = equipo.inscripcion

        return AdminEquipoDetalleAdminResultado(
            item=self._fila_equipo(equipo),
            participantes=participantes,
            cupos=self._cupos_de_inscripcion(inscripcion),
            inscripcion_detalle=ReferenciaAdminResultado(
                id=str(inscripcion.id),
                nombre=inscripcion.referencia,
            ),
            elegibilidad=[],
        )

    # ── Participantes (RT-IN-11) ─────────────────────────────────────────────

    def listar_participantes(
        self,
        edicion_id,
        q: str = "",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Las personas que participan en la edición, paginadas."""
        queryset = self.participante_selector.listar(edicion_id, q=q)
        total = queryset.count()
        pagina, tamano, inicio = self._paginar(total, page, page_size)
        filas = list(queryset[inicio:inicio + tamano])

        return (
            [
                self._participante_admin(persona, edicion_id)
                for persona in filas
            ],
            total,
            pagina,
            tamano,
            self._paginas(total, tamano),
        )

    # ── Pagos (RT-PG-04 · RT-PG-07) ──────────────────────────────────────────

    def listar_pagos(
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
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Los pagos de la edición, paginados.

        El filtro `estado_operativo` NO se aplica en la base de datos: el
        veredicto lo calcula el dueño cruzando tres hechos, y el dueño
        publica UN veredicto por orden. El filtro se aplica sobre el
        veredicto, que es la misma regla y la misma fuente.

        El ORDEN es FILTRAR y LUEGO PAGINAR: `total` y `total_pages` tienen que
        describir las filas DEVUELTAS. Filtrar después de recortar la página
        devolvía un `total` que contaba filas que la página no traía y una
        página VACÍA aunque quedaran filas que cumplían el filtro.
        """
        queryset = self.pago_selector.listar(
            edicion_id,
            q=q,
            ordering=ordering,
            estado_compra=estado_compra,
            estado_orden=estado_orden,
            tipo=tipo,
            desde=desde,
            hasta=hasta,
        )

        if estado_operativo:
            return self._listar_pagos_por_veredicto(
                queryset,
                estado_operativo,
                page,
                page_size,
            )

        total = queryset.count()
        pagina, tamano, inicio = self._paginar(total, page, page_size)
        filas = list(queryset[inicio:inicio + tamano])

        return (
            [self._fila_pago(fila) for fila in filas],
            total,
            pagina,
            tamano,
            self._paginas(total, tamano),
        )

    def _listar_pagos_por_veredicto(
        self,
        queryset,
        estado_operativo: str,
        page: int,
        page_size: int,
    ) -> tuple:
        """Los pagos cuyo VEREDICTO coincide, paginados SOBRE el filtro.

        El veredicto lo calcula el DUEÑO (`EstadoOperativoPagoService`)
        cruzando hechos que no son columnas: no se puede filtrar en SQL sin
        reimplementar sus reglas aquí, y este módulo no duplica reglas de
        otro dueño. Por eso el filtro se aplica ANTES de paginar y la página
        se recorta del conjunto YA filtrado.

        El coste es el del veredicto: se evalúa una vez por fila del conjunto
        filtrado. Es el precio de no reimplementar la regla del dueño.
        """
        coincidencias = [
            item
            for item in (self._fila_pago(fila) for fila in queryset)
            if item.estado_operativo.codigo == estado_operativo
        ]

        total = len(coincidencias)
        pagina, tamano, inicio = self._paginar(total, page, page_size)

        return (
            coincidencias[inicio:inicio + tamano],
            total,
            pagina,
            tamano,
            self._paginas(total, tamano),
        )

    def obtener_pago(self, compra_id) -> tuple:
        """El detalle comercial de un pago, o `None` si no existe."""
        compra = self.pago_selector.obtener(compra_id)

        if compra is None:
            return None

        orden = compra.orden_pago
        intentos = self._intentos(compra)

        return AdminPagoDetalleAdminResultado(
            item=self._fila_pago(compra),
            compra=CompraAdminResultado(
                id=str(compra.id),
                estado=compra.estado,
                total=str(compra.total),
                moneda=compra.moneda,
            )
            if compra
            else None,
            origen_pago=self._origen_pago(orden, intentos),
            intentos=intentos,
            operaciones_manuales=self._operaciones_manuales(orden),
            siguiente_accion=None,
        )

    def obtener_pago_por_orden(self, orden_pago_id):
        """La fila operativa actualizada después de un comando de pago."""
        compra = self.pago_selector.obtener_por_orden(orden_pago_id)
        return self._fila_pago(compra) if compra is not None else None

    # ── Personas (RT-ID-07 · RT-ID-08) ───────────────────────────────────────

    def listar_personas(
        self,
        q: str = "",
        edicion_id=None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple:
        """Las personas del sistema, paginadas."""
        queryset = self.persona_selector.listar(q=q, edicion_id=edicion_id)
        total = queryset.count()
        pagina, tamano, inicio = self._paginar(total, page, page_size)
        filas = list(queryset[inicio:inicio + tamano])

        return (
            [self._participante_admin(persona, edicion_id) for persona in filas],
            total,
            pagina,
            tamano,
            self._paginas(total, tamano),
        )

    def obtener_persona(self, persona_id, edicion_id=None) -> tuple:
        """El detalle de una persona, o `None` si no existe."""
        persona = self.persona_selector.obtener(persona_id)

        if persona is None:
            return None

        item = self._participante_admin(persona, edicion_id)

        return AdminPersonaDetalleAdminResultado(
            item=item,
            telefono=persona.telefono or "",
            whatsapp=persona.whatsapp or "",
            email="",
        )

    # ── Proyecciones internas ────────────────────────────────────────────────

    def _fila_inscripcion(self, inscripcion, equipos=None, personas=None) -> AdminInscripcionListItemAdminResultado:
        """La fila operativa de una inscripción."""
        if equipos is None:
            equipos = list(inscripcion.equipos.all())
        if personas is None:
            personas = inscripcion.participaciones.values("persona_id").distinct().count()

        cupos = self._cupos_de_inscripcion(inscripcion)
        pago = self._veredicto_de_pago_de_inscripcion(inscripcion)

        return AdminInscripcionListItemAdminResultado(
            id=str(inscripcion.id),
            responsable=PersonaAdminResultado(
                id=str(inscripcion.responsable_id),
                nombre=self._nombre_de_persona(inscripcion.responsable),
            ),
            paquete=ReferenciaAdminResultado(
                id=str(inscripcion.paquete_id),
                nombre=inscripcion.paquete.nombre,
            ),
            edicion=ReferenciaAdminResultado(
                id=str(inscripcion.edicion_id),
                nombre=inscripcion.edicion.nombre,
            ),
            equipos=len(equipos),
            personas=personas,
            estado=self._estado_de_inscripcion(inscripcion),
            cupos=cupos,
            pago=pago,
            alerta=self._alerta_de_inscripcion(inscripcion),
            siguiente_accion=self._accion_de_inscripcion(inscripcion),
        )

    def _equipo_de_inscripcion(self, equipo) -> EquipoDeInscripcionAdminResultado:
        """El equipo de una inscripción, con su plantilla."""
        participantes = [
            self._participante_de_equipo(participacion)
            for participacion in equipo.participaciones.all()
            if participacion.estado == EstadoParticipacion.ACTIVA
        ]
        registrados = len(participantes)

        return EquipoDeInscripcionAdminResultado(
            id=str(equipo.id),
            nombre=equipo.nombre,
            disciplina=ReferenciaAdminResultado(
                id=str(equipo.disciplina_id),
                nombre=equipo.disciplina.nombre,
            ),
            estado=equipo.estado,
            participantes=participantes,
            estado_operativo=self._estado_de_equipo(equipo, registrados),
        )

    def _fila_equipo(self, equipo) -> AdminEquipoListItemAdminResultado:
        """La fila operativa de un equipo."""
        registrados = self.equipo_selector.activos_de(equipo)
        incompleta = registrados < (equipo.disciplina.minimo_por_equipo or 0)
        inscripcion = equipo.inscripcion

        return AdminEquipoListItemAdminResultado(
            id=str(equipo.id),
            nombre=equipo.nombre,
            disciplina=ReferenciaAdminResultado(
                id=str(equipo.disciplina_id),
                nombre=equipo.disciplina.nombre,
            ),
            categoria=None,
            plantilla=PlantillaEquipoAdminResultado(
                registrados=registrados,
                minimo=equipo.disciplina.minimo_por_equipo or 0,
                maximo=equipo.disciplina.maximo_por_equipo or 0,
            ),
            estado_operativo=self._estado_de_equipo(equipo, registrados),
            acciones_disponibles=[CodigoAccionOperativa.REVISAR_PLANTILLA]
            if incompleta
            else [],
            responsable=ReferenciaAdminResultado(
                id=str(inscripcion.responsable_id),
                nombre=self._nombre_de_persona(inscripcion.responsable),
            ),
            inscripcion=ReferenciaAdminResultado(
                id=str(inscripcion.id),
                nombre=inscripcion.referencia,
            ),
        )

    def _participante_admin(self, persona, edicion_id=None) -> ParticipanteAdminResultado:
        """La persona con sus participaciones y su historial."""
        participaciones = self.participante_selector.participaciones_de(
            persona.id, edicion_id=edicion_id
        )
        conflictos = self.participante_selector.conflictos_de(participaciones)

        return ParticipanteAdminResultado(
            id=str(persona.id),
            nombre=self._nombre_de_persona(persona),
            documento=persona.numero_documento,
            participaciones=[
                self._participacion_admin(participacion, conflictos)
                for participacion in participaciones
            ],
            historial=self._historial("PERSONA", str(persona.id)),
        )

    def _participacion_admin(self, participacion, conflictos: dict) -> ParticipacionAdminResultado:
        """Una participación con su edición, su equipo y su conflicto."""
        solapamiento = conflictos.get(str(participacion.id))

        return ParticipacionAdminResultado(
            id=str(participacion.id),
            edicion=ReferenciaAdminResultado(
                id=str(participacion.edicion_id),
                nombre=participacion.edicion.nombre,
            ),
            equipo=ReferenciaAdminResultado(
                id=str(participacion.equipo_id),
                nombre=participacion.equipo.nombre,
            ),
            disciplina=ReferenciaAdminResultado(
                id=str(participacion.disciplina_id),
                nombre=participacion.disciplina.nombre,
            ),
            rol=participacion.rol,
            estado=participacion.estado,
            conflicto=CausaAdminResultado(
                codigo=CodigoAlertaAdmin.PARTICIPACION_DUPLICADA,
                mensaje=MENSAJES_ALERTA_ADMIN[CodigoAlertaAdmin.PARTICIPACION_DUPLICADA],
            )
            if solapamiento
            else None,
        )

    def _participante_de_equipo(self, participacion) -> ParticipanteDeEquipoAdminResultado:
        """Una persona de la plantilla de un equipo."""
        return ParticipanteDeEquipoAdminResultado(
            id=str(participacion.id),
            persona_id=str(participacion.persona_id),
            nombre=self._nombre_de_persona(participacion.persona),
            documento=participacion.persona.numero_documento,
            rol=participacion.rol,
            estado=participacion.estado,
        )

    def _fila_pago(self, compra) -> AdminPagoListItemAdminResultado:
        """La fila operativa de un pago."""
        from modules.commerce.domain.constants import OrigenCompra

        orden = compra.orden_pago
        veredicto = self._veredicto_de_pago(orden)
        lote_pase = getattr(compra, "compra_de_pases", None)
        inscripcion_id = self._inscripcion_id_de_compra(compra)

        return AdminPagoListItemAdminResultado(
            compra_id=str(compra.id),
            orden_pago_id=str(orden.id) if orden else None,
            inscripcion_id=inscripcion_id,
            tipo_compra=self._tipo_de_compra(compra),
            resumen_concepto=self._resumen_de_compra(compra),
            comprador=CompradorAdminResultado(
                persona_id=str(compra.persona_id),
                nombre=self._nombre_de_persona(compra.persona),
            ),
            monto=str(compra.total),
            moneda=compra.moneda,
            estado_operativo=veredicto,
            entrega_derechos=EntregaDerechosAdminResultado(
                codigo=compra.origen,
                etiqueta=(
                    lote_pase.pase.nombre
                    if lote_pase is not None
                    else (
                        "Pedido de tienda"
                        if compra.origen == OrigenCompra.MARKETPLACE
                        else "Cupos de inscripción"
                    )
                ),
            ),
            acciones_disponibles=(
                ["APROBACION_MANUAL"]
                if orden and veredicto.codigo == "PENDIENTE"
                else []
            ),
            fecha=compra.created_at,
        )

    def _intentos(self, compra) -> list:
        """Los intentos del proveedor, proyectados por el dueño.

        `referencia_proveedor`, `evidencia`, `metadata` y `mensaje_respuesta`
        NO viajan: son datos técnicos del proveedor
        (`FR-04` §1.3).
        """
        if compra is None or not compra.orden_pago_id:
            return []

        from modules.pagos.domain.selectors.pago_selector import TransaccionPagoSelector

        intentos = TransaccionPagoSelector().listar_por_orden(str(compra.orden_pago_id))

        return [
            IntentoPagoAdminResultado(
                id=str(intento.id),
                intento=intento.intento,
                estado=intento.estado,
                verificada=intento.verificada,
                codigo_respuesta=intento.codigo_respuesta,
                metodo_pago=intento.metodo_pago,
                creada_en=intento.creada_en,
            )
            for intento in intentos
        ]

    # ── Veredictos y hechos proyectados ──────────────────────────────────────

    def _estado_de_inscripcion(self, inscripcion) -> EstadoOperativoAdminResultado:
        """El veredicto del estado de la inscripción.

        El CÓDIGO es del dueño (`EstadoInscripcion`); lo que este módulo
        publica es su EXPLICACIÓN.
        """
        codigo = inscripcion.estado

        return EstadoOperativoAdminResultado(
            codigo=codigo,
            etiqueta=self._etiqueta(codigo, EstadoInscripcion),
            descripcion=DESCRIPCIONES_ESTADO_ADMIN.get(codigo, ""),
        )

    def _estado_de_equipo(self, equipo, registrados: int) -> EstadoOperativoAdminResultado:
        """El veredicto operativo de un equipo.

        El mínimo lo publica la disciplina del DUEÑO
        (`Disciplina.minimo_por_equipo`): aquí sólo se compara.
        """
        minimo = equipo.disciplina.minimo_por_equipo or 0
        codigo = (
            ValorPlantilla.COMPLETA if registrados >= minimo else ValorPlantilla.INCOMPLETA
        )

        return EstadoOperativoAdminResultado(
            codigo=codigo,
            etiqueta=self._etiqueta(codigo, ValorPlantilla),
            descripcion=DESCRIPCIONES_ESTADO_ADMIN.get(codigo, ""),
        )

    def _veredicto_de_pago_de_inscripcion(self, inscripcion):
        """El veredicto comercial del saldo de una inscripción.

        El saldo es un hecho del dueño: `cupos_pagados` frente a
        `cupos_solicitados`. La capacidad pagada sólo crece por ACTIVACIÓN
        de derechos (`RN-I02`).
        """
        if not inscripcion.cupos_solicitados:
            return None

        codigo = (
            ValorEstadoPago.PAGADO
            if inscripcion.cupos_pagados >= inscripcion.cupos_solicitados
            else ValorEstadoPago.PENDIENTE
        )

        return EstadoOperativoAdminResultado(
            codigo=codigo,
            etiqueta=self._etiqueta(codigo, ValorEstadoPago),
            descripcion=DESCRIPCIONES_ESTADO_ADMIN.get(codigo, ""),
        )

    def _veredicto_de_pago(self, orden) -> EstadoOperativoAdminResultado:
        """El veredicto operativo del pago, el del DUEÑO.

        `EstadoOperativoPagoService` es el ÚNICO dueño: este módulo copia su
        resultado y no vuelve a cruzar los tres hechos
        (`RN-C07`).
        """
        veredicto = self.estado_operativo_pago.calcular_para_orden(orden)

        return EstadoOperativoAdminResultado(
            codigo=veredicto.codigo,
            etiqueta=veredicto.etiqueta,
            descripcion=veredicto.descripcion,
        )

    def _origen_pago(self, orden, intentos) -> str:
        """La procedencia de la evidencia de la orden.

        Se deriva de los intentos del proveedor o de la evidencia manual
        persistida: ambas son fuentes de verdad auditables.
        """
        if orden is None:
            return OrigenPago.SIN_PAGO

        if AprobacionPagoManual.objects.filter(orden_pago_id=orden.id).exists():
            return OrigenPago.MANUAL

        for intento in intentos:
            if (
                intento.estado == EstadoTransaccionPago.EXITO
                and intento.verificada
            ):
                return OrigenPago.IZIPAY

        return OrigenPago.SIN_PAGO

    @staticmethod
    def _operaciones_manuales(orden) -> list[OperacionManualAdminResultado]:
        """La evidencia manual auditada, sólo en el detalle administrativo."""
        if orden is None:
            return []
        return [
            OperacionManualAdminResultado(
                id=str(aprobacion.id),
                canal=aprobacion.canal,
                monto=str(aprobacion.monto),
                moneda=aprobacion.moneda,
                motivo=aprobacion.motivo,
                registrada_en=aprobacion.created_at,
                actor=getattr(aprobacion.actor, "username", "") or "",
            )
            for aprobacion in AprobacionPagoManual.objects.filter(
                orden_pago_id=orden.id
            ).select_related("actor")
        ]

    def _alerta_de_inscripcion(self, inscripcion) -> CausaAdminResultado:
        """La alerta de la fila, si la hay."""
        if inscripcion.cupos_pagados >= inscripcion.cupos_solicitados:
            return None

        codigo = CodigoAlertaAdmin.INSCRIPCIONES_PENDIENTES_DE_PAGO

        return CausaAdminResultado(
            codigo=codigo,
            mensaje=MENSAJES_ALERTA_ADMIN[codigo],
        )

    def _accion_de_inscripcion(self, inscripcion) -> AccionOperativaAdminResultado:
        """La acción concreta que resuelve el problema de la fila."""
        if inscripcion.cupos_pagados >= inscripcion.cupos_solicitados:
            return None

        codigo = CodigoAccionOperativa.REVISAR_PAGO

        return AccionOperativaAdminResultado(
            codigo=codigo,
            etiqueta=MENSAJES_ACCION_ADMIN[codigo],
            href=f"{VISTA_PAGOS}?estado_operativo=PENDIENTE",
        )

    def _cupos_de_inscripcion(self, inscripcion) -> CuposOperativosAdminResultado:
        """Los tres cupos de una inscripción, como tres hechos.

        `disponibles` es la diferencia que el dueño ya publicó (`RN-I03`).
        """
        return CuposOperativosAdminResultado(
            adquiridos=inscripcion.cupos_pagados,
            asignados=inscripcion.cupos_asignados,
            disponibles=max(inscripcion.cupos_pagados - inscripcion.cupos_asignados, 0),
        )

    @staticmethod
    def proyectar_pool(pool) -> PoolAdminResultado:
        """El pool que publica el dueño, proyectado a la forma del panel."""
        if pool is None:
            return None

        return PoolAdminResultado(
            cupos_pagados=pool.cupos_pagados,
            cupos_asignados=pool.cupos_asignados,
            cupos_disponibles=pool.cupos_disponibles,
            participaciones=[
                ParticipacionPoolAdminResultado(
                    id=str(participacion.id),
                    persona_id=str(participacion.persona_id),
                    equipo_id=str(participacion.equipo_id),
                    equipo_nombre=participacion.equipo_nombre,
                    disciplina_nombre=participacion.disciplina_nombre,
                    rol=participacion.rol,
                    estado=participacion.estado,
                    ocupa_cupo=participacion.ocupa_cupo,
                )
                for participacion in pool.participaciones
            ],
            impedimentos=[
                CausaAdminResultado(codigo=impedimento.codigo, mensaje=impedimento.mensaje)
                for impedimento in pool.impedimentos
            ],
        )

    def _historial(self, entidad: str, entidad_id: str) -> list:
        """El historial del ACTA transversal de una entidad."""
        filas = AccionAuditada.objects.filter(
            entidad=entidad, entidad_id=entidad_id
        ).order_by("-created_at")

        return [
            EventoHistorialAdminResultado(
                occurred_at=fila.created_at,
                tipo=fila.accion,
                descripcion=fila.motivo,
                actor=fila.actor_nombre or "Sistema",
            )
            for fila in filas
        ]

    # ── Utilidades ───────────────────────────────────────────────────────────

    @staticmethod
    def _nombre_de_persona(persona) -> str:
        """El nombre legible de una persona.

        NUNCA su identificador: el panel muestra nombres.
        """
        if persona is None:
            return ""

        return f"{persona.nombres} {persona.apellidos}".strip()

    @staticmethod
    def _etiqueta(codigo: str, choices) -> str:
        """La etiqueta del dueño para un código, o el código mismo."""
        try:
            return choices(codigo).label
        except ValueError:
            return codigo

    @staticmethod
    def _tipo_de_compra(compra) -> str:
        """El origen de la compra, con la etiqueta del dueño."""
        if compra is None:
            return ""

        from modules.commerce.domain.constants import OrigenCompra

        return dict(OrigenCompra.choices).get(compra.origen, compra.origen)

    @staticmethod
    def _resumen_de_compra(compra) -> str:
        """El concepto de la primera línea del snapshot de la compra."""
        if compra is None:
            return ""

        lineas = compra.lineas_snapshot or []

        if not lineas or not isinstance(lineas[0], dict):
            return ""

        return str(lineas[0].get("concepto_nombre", ""))

    @staticmethod
    def _inscripcion_id_de_compra(compra) -> str | None:
        """El vínculo de inscripción publicado por su referencia canónica."""
        referencia = parsear_referencia(compra.referencia)
        return str(referencia.inscripcion_id) if referencia is not None else None

    @staticmethod
    def _paginar(total: int, page: int, page_size: int) -> tuple:
        """`(pagina, tamano, inicio)` de una página pedida."""
        pagina = max(int(page or 1), 1)
        tamano = max(int(page_size or 25), 1)
        return pagina, tamano, (pagina - 1) * tamano

    @staticmethod
    def _paginas(total: int, tamano: int) -> int:
        """El número de páginas de un conjunto."""
        if not total:
            return 0

        return (total + tamano - 1) // tamano


__all__ = ["AdminOperacionService", "VISTA_EQUIPOS", "VISTA_PAGOS"]
