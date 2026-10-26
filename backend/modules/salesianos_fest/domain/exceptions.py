"""Domain exceptions for salesianos_fest module."""

from ninja.errors import HttpError

from core.exceptions import ConflictError, NotFoundError, UnprocessableEntityError


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


class CompraNoCobrableError(ConflictError):
    """La compra no está en estado Pendiente y no puede ser cobrada."""

    code: str = "COMPRA_NOT_PAYABLE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            message="La compra no puede ser cobrada en su estado actual.",
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
