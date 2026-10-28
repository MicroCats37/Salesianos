"""Domain exceptions for salesianos_fest module."""

from ninja.errors import HttpError

from core.exceptions import (
    BusinessError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
)


class DisciplinaNotFoundError(NotFoundError):
    """Excepción cuando una disciplina no es encontrada."""

    code: str = "DISCIPLINA_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Disciplina", code=self.code)


class PromocionNotFoundError(NotFoundError):
    """Excepción cuando una promoción no es encontrada."""

    code: str = "PROMOCION_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Promoción", code=self.code)


class CategoriaNotFoundError(NotFoundError):
    """Excepción cuando una categoría no es encontrada."""

    code: str = "CATEGORIA_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Categoría", code=self.code)


class PaqueteNotFoundError(NotFoundError):
    """Excepción cuando un paquete no es encontrado."""

    code: str = "PAQUETE_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Paquete", code=self.code)


class InscripcionNotFoundError(NotFoundError):
    """Excepción cuando una inscripción no es encontrada."""

    code: str = "INSCRIPCION_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Inscripción", code=self.code)


class EquipoNotFoundError(NotFoundError):
    """Excepción cuando un equipo no es encontrado."""

    code: str = "EQUIPO_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Equipo", code=self.code)


class ParticipacionNotFoundError(NotFoundError):
    """Excepción cuando una participación no es encontrada."""

    code: str = "PARTICIPACION_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Participación", code=self.code)


class R11ViolationError(ConflictError):
    """R11: una persona ya participa activamente en esa disciplina del evento.

    Mapeado a mensaje público sin exponer IDs internos ni constraints.
    """

    code: str = "R11_DUPLICATE_PARTICIPATION"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Esta persona ya está registrada en la misma disciplina de este evento.",
            code=self.code,
        )


class GeneroNoPermitidoError(ConflictError):
    """El género de la persona es incompatible con la modalidad de la disciplina.

    Regla de negocio: una persona sólo puede tener una participación ACTIVA en
    una disciplina cuya modalidad admita su género (M/M, M/X, F/F, F/X). La
    regla falla cerrada: cualquier par fuera de la lista se rechaza.

    Mapeado a 409 con el código estable `GENERO_NO_PERMITIDO`. El mensaje
    público sale del catálogo de `core/exceptions.py`; esta excepción nunca
    interpola identificadores, nombres ni UUIDs.
    """

    code: str = "GENERO_NO_PERMITIDO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message=(
                "La modalidad de la disciplina no es compatible con el género "
                "de la persona."
            ),
            code=self.code,
        )


class EquipoDeOtraInscripcionError(ConflictError):
    """El equipo destino pertenece a otra inscripción.

    Una `Participacion` vincula a una persona inscrita con un equipo. Si el
    equipo pertenece a otra inscripción, la fila apuntaría a un cupo pagado de
    una inscripción distinta — el roster quedaría inconsistente con el derecho
    comercial que lo respalda.
    """

    code: str = "EQUIPO_DE_OTRA_INSCRIPCION"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El equipo destino pertenece a otra inscripcion.",
            code=self.code,
        )


class ParticipanteRetiradoError(ConflictError):
    """El vínculo persona-inscripción está retirado: no puede entrar a un equipo.

    Una persona retirada conserva su cupo pagado, pero su registro en la
    inscripción quedó en estado RETIRADO. Para volver a jugar hay que
    reingresar primero; asignarla directamente a un equipo dejaría el roster
    apuntando a un vínculo retirado.
    """

    code: str = "PARTICIPANTE_RETIRADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message=(
                "Esta persona fue retirada de la inscripcion. "
                "Debe reingresar antes de asignarse a un equipo."
            ),
            code=self.code,
        )


class DisciplinaNotInPaqueteError(ConflictError):
    """La disciplina no pertenece al paquete de la inscripción."""

    code: str = "DISCIPLINA_NOT_IN_PAQUETE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="La disciplina seleccionada no está incluida en el paquete.",
            code=self.code,
        )


class PaqueteEventoMismatchError(ConflictError):
    """El paquete no pertenece al evento de la inscripción."""

    code: str = "PAQUETE_EVENTO_MISMATCH"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El paquete no corresponde al evento seleccionado.",
            code=self.code,
        )


class RosterCompletoError(ConflictError):
    """El equipo ya alcanzó el máximo de jugadores para esa disciplina."""

    code: str = "ROSTER_COMPLETO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El equipo alcanzó el número máximo de jugadores para esta disciplina.",
            code=self.code,
        )


class CompraNotFoundError(NotFoundError):
    """Excepción cuando una compra no es encontrada."""

    code: str = "COMPRA_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Compra", code=self.code)


class CompraNoAutorizadoError(HttpError):
    """El llamador no es el responsable de la compra ni un administrador.

    Se usa para las operaciones comerciales que exigen autorización: la
    recuperación manual de una compra sólo puede realizarla el responsable de
    la inscripción vinculada o un administrador de Django.

    El mensaje público sale del catálogo de `core/exceptions.py`; esta
    excepción nunca interpola identificadores internos.
    """

    code: str = "COMPRA_NO_AUTORIZADA"

    def __init__(self):
        self.code = self.code
        super().__init__(403, "No tiene autorización para confirmar esta compra.")


class CompraConAprobacionManualError(HttpError):
    """La compra tiene una aprobación manual activa y no puede anularse aquí.

    Una compra financiada por una aprobación manual activa sólo se revoca
    mediante la anulación administrativa auditada
    (`POST /api/administracion/pagos/{orden_pago_id}/anular-manual`): la
    anulación del comprador no es una decisión auditada.

    El mensaje público sale del catálogo de `core/exceptions.py`; esta
    excepción nunca interpola identificadores internos.
    """

    code: str = "COMPRA_CON_APROBACION_MANUAL"

    def __init__(self):
        self.code = self.code
        super().__init__(
            403,
            "La compra tiene una aprobación manual activa y sólo puede "
            "anularla un administrador.",
        )


class CompraNoCobrableError(ConflictError):
    """La compra no está en estado Pendiente y no puede ser cobrada."""

    code: str = "COMPRA_NOT_PAYABLE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="La compra no puede ser cobrada en su estado actual.",
            code=self.code,
        )


class CompraSinCompradorError(ConflictError):
    """La compra no tiene comprador y no se puede iniciar el pago.

    El comprador de una compra deportiva es el responsable de su inscripción
    y el de una compra de pases es el `Compra.responsable` genérico. Una
    compra sin ninguno de los dos no tiene a quién cobrarle: se rechaza en
    lugar de adivinar.
    """

    code: str = "COMPRA_SIN_COMPRADOR"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="La compra no tiene un comprador asignado.",
            code=self.code,
        )


class PrecioNoEncontradoError(ConflictError):
    """No se encontró un precio vigente para el paquete."""

    code: str = "PRECIO_NO_ENCONTRADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="No existe un precio vigente para el paquete seleccionado.",
            code=self.code,
        )


class CantidadInsuficienteError(ConflictError):
    """La cantidad de cupos no alcanza el minimo inicial."""

    code: str = "CANTIDAD_INSUFICIENTE"

    def __init__(self, minimo: int = 0, received: int = 0):
        self.code = self.code
        super().__init__(
            message=f"La cantidad debe ser al menos {minimo} (recibido: {received}).",
            code=self.code,
        )


# ─── AsignacionCupo / Acreditacion ──────────────────────────────────────────────


class CupoAgotadoError(ConflictError):
    """No hay cupos pagados disponibles para asignar."""

    code: str = "CUPO_AGOTADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="No hay cupos pagados disponibles para asignar.",
            code=self.code,
        )


class CupoNoAsignadoError(ConflictError):
    """El participante no tiene un cupo activo para unirse a un equipo.

    Regla de negocio: toda Participacion ACTIVA requiere AsignacionCupo.ACTIVA
    vinculada a la inscripcion del participante. Sin cupo activo, la persona
    solo puede estar en el pool de pre-registro sin derecho a equipo.
    """

    code: str = "CUPO_NO_ASIGNADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Esta persona no tiene un cupo activo asignado. Complete el pago para habilitar la inclusion en equipos.",
            code=self.code,
        )


class CupoContratadoExcedidoError(ConflictError):
    """Se supero la capacidad contratada para pre-registrar participantes."""

    code: str = "CUPO_CONTRATADO_EXCEDIDO"

    def __init__(self, maximo: int):
        self.code = self.code
        super().__init__(
            message=f"No es posible pre-registrar mas participantes. Se supero la capacidad contratada ({maximo} lugares).",
            code=self.code,
        )


class PersonaNoAsignadaError(NotFoundError):
    """La persona no tiene una asignacion de cupo activa."""

    code: str = "PERSONA_NO_ASIGNADA"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="AsignacionCupo", code=self.code)


class AcreditacionNotFoundError(NotFoundError):
    """No se encontro una acreditacion para ese evento y persona."""

    code: str = "ACREDITACION_NOT_FOUND"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Acreditacion", code=self.code)


class AccesoDenegadoError(ConflictError):
    """El acceso fue denegado (QR no valido o ya usado)."""

    code: str = "ACCESO_DENEGADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Acceso denegado. El codigo QR no es valido o ya fue utilizado.",
            code=self.code,
        )


class PersonaYaAsignadaError(ConflictError):
    """La persona ya tiene una asignacion activa en esta inscripcion."""

    code: str = "PERSONA_YA_ASIGNADA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Esta persona ya tiene una asignacion de cupo activa en esta inscripcion.",
            code=self.code,
        )


class FechaLimiteExcedidaError(ConflictError):
    """Se intentó realizar una modificación después de la fecha límite del evento."""

    code: str = "FECHA_LIMITE_EXCEDIDA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="La fecha límite para modificaciones ha sido excedida. No se permiten cambios después de dicha fecha.",
            code=self.code,
        )


class InscripcionUniqueConstraintError(ConflictError):
    """Ya existe una inscripción para este responsable, paquete y evento."""

    code: str = "INSCRIPCION_DUPLICADA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Ya existe una inscripción para este responsable, paquete y evento.",
            code=self.code,
        )


class PrecioCambioError(ConflictError):
    """El precio del paquete cambió entre la cotización y la confirmación.

    The client sent a quoted price that no longer matches the current catalog.
    The response includes the new price and total so the UI can show the delta.
    """

    code: str = "PRECIO_CAMBIO"

    def __init__(self, precio_cotizado: float, precio_actual: float, cantidad: int):
        self.code = self.code
        self.precio_cotizado = precio_cotizado
        self.precio_actual = precio_actual
        self.cantidad = cantidad
        self.total_nuevo = round(precio_actual * cantidad, 2)
        super().__init__(
            message=(
                f"El precio cambió de S/{precio_cotizado:.2f} a S/{precio_actual:.2f} "
                f"por persona. Total nuevo: S/{self.total_nuevo:.2f}."
            ),
            code=self.code,
        )


class ParticipanteDebePreregistrarseError(UnprocessableEntityError):
    """No se puede dar de alta a una persona nueva dentro de un equipo.

    Regla "pool primero": el alta y el pre-registro de un participante ocurren
    en el pool (`POST /inscripciones/{id}/personas` **sin** `equipo_id`), que
    además reclama el cupo pagado disponible. La asignación a un equipo es una
    operación posterior y aparte (`POST /inscripciones/{id}/pool/asignar`).

    Enviar `persona_data` (persona nueva) junto con `equipo_id` intentaría
    saltarse el pool: crearía la persona, el vínculo con la inscripción y la
    participación en un solo paso, sin pasar por la cola de pre-registro ni por
    el reparto FIFO de cupos.

    Es un error de VALIDACIÓN (422) con código estable
    `PARTICIPANTE_DEBE_PREREGISTRARSE`; el mensaje público sale del catálogo de
    `core/exceptions.py` y no interpola identificadores.
    """

    code: str = "PARTICIPANTE_DEBE_PREREGISTRARSE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message=(
                "Los participantes se pre-registran en el pool y luego se "
                "asignan a un equipo."
            ),
            code=self.code,
        )


class PersonaDataRequiredError(HttpError):
    """El cliente debe proporcionar exactamente `persona_id` o `persona_data`.

    Usado por `AgregarPersonaFlujo` para rechazar payloads que no referencian
    a una persona existente ni aportan los datos para crearla inline.
    Hereda directamente de `HttpError` con status 422 para alinearse con la
    convención del proyecto de tratar los errores de validación del cliente
    como `VALIDATION`-class (`422`) en vez de `BUSINESS_ERROR` (`400`).
    """

    code: str = "PERSONA_REQUIRED"

    def __init__(self):
        self.code = self.code
        super().__init__(422, "Debes proporcionar persona_id o persona_data")


# ─── Pases de fiesta (catálogo independiente) ─────────────────────────────────
#
# Los mensajes públicos de estos códigos salen del catálogo de
# `core/exceptions.py`: estas excepciones nunca interpolan identificadores,
# nombres, UUIDs ni montos internos.


class PasesFiestaDeshabilitadoError(ConflictError):
    """La capacidad de pases de fiesta no está habilitada.

    El interruptor de despliegue `PASES_FIESTA_ENABLED` está apagado: la
    superficie de compra no existe y nada se escribe en la base de datos.
    """

    code: str = "PASES_FIESTA_DESHABILITADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="La compra de pases no está habilitada en este momento.",
            code=self.code,
        )


class PaseNoEncontradoError(NotFoundError):
    """El pase solicitado no existe."""

    code: str = "PASE_NO_ENCONTRADO"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Pase", code=self.code)


class PaseNoDisponibleError(ConflictError):
    """El pase no se puede comprar ahora mismo.

    O bien está inactivo, o bien pertenece a una edición que no es la activa.
    """

    code: str = "PASE_NO_DISPONIBLE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El pase seleccionado no está disponible para la compra.",
            code=self.code,
        )


class PasePrecioNoVigenteError(ConflictError):
    """El pase no tiene ningún precio vigente.

    Sin precio vigente no hay monto que congelar, así que la compra se
    rechaza antes de crear cualquier fila comercial.
    """

    code: str = "PASE_PRECIO_NO_VIGENTE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="El pase seleccionado no tiene un precio vigente.",
            code=self.code,
        )


class PaseCantidadInvalidaError(UnprocessableEntityError):
    """La cantidad de pases solicitados no es válida.

    La cantidad es un entero positivo y no puede superar el tope comercial por
    compra. Es un error de VALIDACIÓN (422): el recurso está bien, lo que el
    cliente envió no.
    """

    code: str = "PASE_CANTIDAD_INVALIDA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="La cantidad de pases solicitada no es válida.",
            code=self.code,
        )


class PaseInventarioAgotadoError(ConflictError):
    """No quedan pases suficientes para esa compra.

    El tope lo fija `Pase.cantidad_maxima` (0 = sin límite) y se recalcula
    dentro de la transacción de compra sobre las compras no canceladas.
    """

    code: str = "PASE_INVENTARIO_AGOTADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="No hay disponibilidad suficiente de ese pase.",
            code=self.code,
        )


class PaseCompraNoEncontradaError(NotFoundError):
    """La compra de pases solicitada no existe."""

    code: str = "PASE_COMPRA_NO_ENCONTRADA"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Compra de pases", code=self.code)


class PaseCompraNoAutorizadaError(ForbiddenError):
    """El llamador no es el responsable de la compra de pases.

    La compra de pases sólo la consulta su responsable (`Compra.responsable`).
    """

    code: str = "PASE_COMPRA_NO_AUTORIZADA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            "No tienes autorización para consultar esta compra de pases."
        )


class PaseCompradorSinPersonaError(BusinessError):
    """El usuario autenticado no tiene una Persona vinculada.

    `Compra.responsable` es el titular de la compra: sin Persona no hay
    propietario y la compra no puede crearse.
    """

    code: str = "PASE_COMPRADOR_SIN_PERSONA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Usuario sin persona vinculada. Complete su registro.",
            code=self.code,
        )


# ─── Pases de fiesta: derechos nominativos ───────────────────────────────────


class PaseCompraNoPagadaError(ConflictError):
    """La compra de pases todavía no está pagada.

    Los derechos nominativos sólo existen sobre una compra pagada: sin
    evidencia de pago no hay derecho que repartir.
    """

    code: str = "PASE_COMPRA_NO_PAGADA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="La compra de pases aún no está pagada.",
            code=self.code,
        )


class PaseBeneficiarioNoEncontradoError(NotFoundError):
    """La Persona indicada no existe o no tiene derecho en esta compra.

    El identificador debe apuntar a una Persona existente: el flujo nunca
    crea personas a partir de datos libres del cliente.
    """

    code: str = "PASE_BENEFICIARIO_NO_ENCONTRADO"

    def __init__(self):
        self.code = self.code
        super().__init__(resource="Beneficiario del pase", code=self.code)


class PaseBeneficiariosExcedidosError(ConflictError):
    """No quedan slots libres para asignar todos los beneficiarios.

    El lote tiene una cantidad fija de pases y cada slot es inmutable: un slot
    revocado NO vuelve a estar disponible.
    """

    code: str = "PASE_BENEFICIARIOS_EXCEDIDOS"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="No hay pases suficientes para los beneficiarios indicados.",
            code=self.code,
        )


class PaseBeneficiarioDuplicadoError(ConflictError):
    """La persona ya tiene un pase activo en este evento.

    Como máximo existe un pase activo por persona y evento, entre todas las
    compras.
    """

    code: str = "PASE_BENEFICIARIO_DUPLICADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Esa persona ya tiene un pase activo en este evento.",
            code=self.code,
        )


class PaseNoTransferibleError(ConflictError):
    """El derecho de esa persona no puede transferirse a otra persona.

    En v1 un pase pagado es NOMINAL: revocar un derecho consume su slot de
    forma permanente y la persona no puede reutilizar ese lote.
    """

    code: str = "PASE_NO_TRANSFERIBLE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="Ese pase no es transferible a otra persona.",
            code=self.code,
        )


class PaseCancelacionRequiereAdministracionError(ForbiddenError):
    """Una compra de pases NO se cancela desde la operación del comprador.

    La cancelación de una compra de pases revoca derechos nominativos ya
    entregados: es una decisión ADMINISTRATIVA y auditada, no una operación del
    comprador. El endpoint ordinario del comprador la rechaza.
    """

    code: str = "PASE_CANCELACION_REQUIERE_ADMINISTRACION"

    def __init__(self):
        self.code = self.code
        super().__init__(
            "La cancelación de una compra de pases la realiza un administrador."
        )
