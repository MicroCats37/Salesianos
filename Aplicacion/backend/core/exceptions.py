import logging
from django.db import IntegrityError
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
    PermissionDenied,
    ObjectDoesNotExist,
)
from ninja.errors import (
    AuthenticationError as NinjaAuthenticationError,
    HttpError,
    ValidationError as NinjaValidationError,
)
from ninja_extra.exceptions import (
    AuthenticationFailed as NinjaExtraAuthenticationFailed,
    PermissionDenied as NinjaExtraPermissionDenied,
)
from pydantic import ValidationError as PydanticValidationError
from django.http import HttpRequest
from .utils import format_errors, humanize_validation_errors
from .responses import error_response

# Configuración del logger para errores internos inesperados
logger = logging.getLogger(__name__)

# --- 1. Clases de Excepción Personalizadas ---

# Catálogo público de errores.
#
# El código de una excepción de dominio es estable y legible por máquina; el
# mensaje que ve el usuario sale SIEMPRE de este catálogo. Así la respuesta
# HTTP nunca expone identificadores internos, UUIDs, payloads de proveedores,
# secretos ni texto crudo de excepciones: el detalle técnico se queda en los
# logs del servidor.
PUBLIC_ERROR_MESSAGES = {
    # ── Pagos / Izipay ─────────────────────────────────────────────────────────
    "PAGO_NO_AUTORIZADO": (
        "No tiene autorización para realizar esta acción."
    ),
    "TRANSACCION_PAGO_NO_ENCONTRADA": (
        "No se encontró la transacción de pago solicitada."
    ),
    "ORDEN_PAGO_NO_ENCONTRADA": (
        "No se encontró la orden de pago solicitada."
    ),
    "PAGO_DATOS_INCONSISTENTES": (
        "Los datos del pago no coinciden con la orden registrada."
    ),
    "PAGO_FIRMA_INVALIDA": (
        "No se pudo verificar la firma del pago."
    ),
    "PAGO_NOTIFICACION_NO_VERIFICABLE": (
        "La notificación del pago no pudo ser verificada."
    ),
    # ── Compras / Recuperación comercial manual ───────────────────────────────
    "COMPRA_NO_AUTORIZADA": (
        "No tiene autorización para realizar esta acción."
    ),
    "COMPRA_SIN_COMPRADOR": (
        "La compra no tiene un comprador asignado."
    ),
    "COMPRA_CON_APROBACION_MANUAL": (
        "La compra tiene una aprobación manual activa y sólo puede anularla "
        "un administrador."
    ),
    # ── Aprobación manual de pago (administrador) ─────────────────────────────
    # Categoría "Payment" (409). Los mensajes explican la condición del pago
    # sin exponer identificadores, montos internos ni payloads del proveedor.
    "PAGO_NO_VERIFICADO": (
        "El pago no cuenta con evidencia verificable."
    ),
    "MONTO_NO_COINCIDE": (
        "El monto y la moneda no coinciden con la orden de pago."
    ),
    "ORDEN_YA_PAGADA_CON_IZIPAY": (
        "La orden de pago ya fue pagada mediante el proveedor."
    ),
    "COMPRA_YA_CANCELADA": (
        "La compra asociada ya se encuentra cancelada."
    ),
    "PAGO_MANUAL_APROBACION_DESHABILITADA": (
        "La aprobación manual de pagos no está habilitada."
    ),
    "APROBACION_PAGO_MANUAL_NO_ENCONTRADA": (
        "No se encontró la aprobación de pago manual solicitada."
    ),
    # ── Pool primero (alta de participantes) ──────────────────────────────────
    "PARTICIPANTE_DEBE_PREREGISTRARSE": (
        "Los participantes se pre-registran en el pool y luego se asignan a un equipo."
    ),
    # ── Compatibilidad género / modalidad de la disciplina ───────────────────
    # Categoría "Business conflict" (409). El mensaje explica la condición de
    # negocio sin exponer identificadores, nombres, UUIDs ni los valores
    # concretos de género/modalidad que la provocaron.
    "GENERO_NO_PERMITIDO": (
        "La disciplina seleccionada no es compatible con el género de la persona."
    ),
    # ── Autenticación / autorización ─────────────────────────────────────────
    # Categorías transversales del contrato de wrappers (§8). Los mensajes son
    # prosa fija: nunca interpolan ids, UUIDs ni texto crudo de excepciones.
    "AUTHENTICATION_REQUIRED": (
        "Debes iniciar sesión para acceder a este recurso."
    ),
    "ACTION_NOT_ALLOWED": (
        "No tienes autorización para realizar esta acción."
    ),
    "ADMIN_REQUIRED": (
        "Esta acción está reservada para los administradores del evento."
    ),
    "RESOURCE_NOT_FOUND": (
        "No se encontró el recurso solicitado."
    ),
    # ── Identidad / personas ──────────────────────────────────────────────────
    # 404 — el documento consultado NO corresponde a una `Persona` registrada.
    # El mensaje no confirma ni desmiente datos de cuentas, contactos ni
    # credenciales: sólo dice que no hay una persona con ese documento.
    "PERSONA_NO_ENCONTRADA": (
        "No se encontró una persona registrada con ese documento."
    ),
    # 422 — el tipo de documento consultado NO pertenece al vocabulario
    # cerrado del módulo de identidad (DNI, CE, PAS).
    "TIPO_DOCUMENTO_INVALIDO": (
        "El tipo de documento no es válido."
    ),
    # ── Petición inválida (parámetros de consulta) ───────────────────────────
    # Categoría "Validation" (422). Cubre los rechazos del contrato de
    # paginación/ordenamiento del área de administración: `ordering` fuera de
    # la lista blanca, `page`/`page_size` con valores no numéricos, etc.
    "INVALID_REQUEST": (
        "La solicitud contiene parámetros no válidos."
    ),
    # ── Evento activo ausente (404) ─────────────────────────────────────────
    # El área de administración opera SIEMPRE sobre el evento activo del
    # servidor. Sin una edición activa no existe un alcance que consultar.
    "EVENTO_ACTIVO_NO_ENCONTRADO": (
        "No hay un evento activo configurado para consultar."
    ),
    # ── Competencias / cuadro de eliminatorias ─────────────────────────────
    # Catálogo del módulo `modules.competencias` (códigos del diseño).
    # 404 — el recurso no existe (o está fuera del alcance del lector: la
    # superficie nunca confirma la existencia de un recurso que no puede ver).
    "COMPETENCIA_NOT_FOUND": (
        "No se encontró la competencia solicitada."
    ),
    "RONDA_NOT_FOUND": (
        "No se encontró la ronda solicitada."
    ),
    "ENCUENTRO_NOT_FOUND": (
        "No se encontró el encuentro solicitado."
    ),
    "COMPETENCIA_EQUIPO_NOT_FOUND": (
        "No se encontró la participación del equipo en la competencia."
    ),
    # 409 — conflicto de negocio.
    "COMPETENCIA_DUPLICADA": (
        "Ya existe un elemento con esos datos en la competencia."
    ),
    "EQUIPO_NO_ELEGIBLE": (
        "El equipo no cumple las condiciones para incorporarse a la "
        "competencia."
    ),
    "EQUIPO_SOLAPADO": (
        "El equipo ya tiene un encuentro programado en ese horario."
    ),
    "SLOT_OCUPADO": (
        "El slot de destino del encuentro ya está ocupado."
    ),
    "DESTINO_BLOQUEADO": (
        "El encuentro de destino ya comenzó, finalizó o fue cancelado y no "
        "puede reescribirse sin una decisión administrativa explícita."
    ),
    "INVALID_STATE_TRANSITION": (
        "La transición de estado no es válida para este recurso."
    ),
    "DELETE_NOT_ALLOWED": (
        "El recurso ya está en uso en el cuadro y solo puede cancelarse o "
        "invalidarse."
    ),
    "RESOURCE_CHANGED": (
        "El recurso cambió mientras lo editabas. Actualiza tus datos e "
        "inténtalo nuevamente."
    ),
    # 422 — la petición es válida en forma pero su contenido no lo es.
    "INVALID_SCHEDULE": (
        "El horario del encuentro no es válido."
    ),
    "INVALID_WINNER": (
        "El ganador no es válido para este encuentro."
    ),
    "INVALID_LINK": (
        "El vínculo del encuentro no es válido."
    ),
    "REASON_REQUIRED": (
        "Debes indicar el motivo del cambio."
    ),
    # ── Pases de fiesta (catálogo independiente) ───────────────────────────────
    # Categorías transversales del contrato de wrappers (§8). Los mensajes son
    # prosa fija: nunca interpolan ids, UUIDs, nombres ni montos internos.
    # 409 — la capacidad está apagada o la condición de negocio no se cumple.
    "PASES_FIESTA_DESHABILITADO": (
        "La compra de pases no está habilitada en este momento."
    ),
    "PASE_NO_DISPONIBLE": (
        "El pase seleccionado no está disponible para la compra."
    ),
    "PASE_PRECIO_NO_VIGENTE": (
        "El pase seleccionado no tiene un precio vigente."
    ),
    "PASE_INVENTARIO_AGOTADO": (
        "No hay disponibilidad suficiente de ese pase."
    ),
    # 404 — el recurso no existe.
    "PASE_NO_ENCONTRADO": (
        "No se encontró el pase solicitado."
    ),
    "PASE_COMPRA_NO_ENCONTRADA": (
        "No se encontró la compra de pases solicitada."
    ),
    # 403 — el actor está autenticado pero no es el titular.
    "PASE_COMPRA_NO_AUTORIZADA": (
        "No tienes autorización para consultar esta compra de pases."
    ),
    # 400 — el usuario autenticado no tiene una Persona vinculada.
    "PASE_COMPRADOR_SIN_PERSONA": (
        "Usuario sin persona vinculada. Complete su registro."
    ),
    # 422 — la cantidad de pases solicitada no es válida.
    "PASE_CANTIDAD_INVALIDA": (
        "La cantidad de pases solicitada no es válida."
    ),
    # ── Pases de fiesta: derechos nominativos ─────────────────────────────────
    # 409 — el estado comercial o la capacidad del lote no lo permiten.
    "PASE_COMPRA_NO_PAGADA": (
        "La compra de pases aún no está pagada."
    ),
    "PASE_BENEFICIARIOS_EXCEDIDOS": (
        "No hay pases suficientes para los beneficiarios indicados."
    ),
    "PASE_BENEFICIARIO_DUPLICADO": (
        "Esa persona ya tiene un pase activo en este evento."
    ),
    "PASE_NO_TRANSFERIBLE": (
        "Ese pase no es transferible a otra persona."
    ),
    # 404 — la persona indicada no existe o no tiene derecho en la compra.
    "PASE_BENEFICIARIO_NO_ENCONTRADO": (
        "No se encontró el beneficiario indicado."
    ),
    # 403 — la cancelación de una compra de pases es una decisión
    # administrativa: el comprador no puede tomarla.
    "PASE_CANCELACION_REQUIERE_ADMINISTRACION": (
        "La cancelación de una compra de pases la realiza un administrador."
    ),
}


class NotFoundError(HttpError):
    """Excepción para recursos no encontrados (404)."""

    code: str = "NOT_FOUND"

    def __init__(self, resource: str, detail: str = "", code: str | None = None):
        msg = f"{resource} no encontrado"
        if detail:
            msg += f": {detail}"
        self.code = code or self.code
        super().__init__(404, msg)


class ConflictError(HttpError):
    """Excepción para conflictos de recursos, como duplicados (409)."""

    code: str = "CONFLICT"

    def __init__(
        self,
        message: str = "Conflicto con el estado actual del recurso",
        code: str | None = None,
    ):
        self.code = code or self.code
        super().__init__(409, message)


class BusinessError(HttpError):
    """Excepción para errores de lógica de negocio (400)."""

    code: str = "BUSINESS_ERROR"

    def __init__(self, message: str, code: str | None = None):
        self.code = code or self.code
        super().__init__(400, message)


class ForbiddenError(HttpError):
    """Excepción para acceso denegado a un recurso (403).

    El código público es estable (`ACTION_NOT_ALLOWED`) y el mensaje que ve el
    usuario sale del catálogo `PUBLIC_ERROR_MESSAGES`, nunca de esta clase.
    """

    code: str = "ACTION_NOT_ALLOWED"

    def __init__(self, message: str = "No tienes permisos para realizar esta acción."):
        self.code = self.code
        super().__init__(403, message)


class AdminRequiredError(ForbiddenError):
    """La acción está reservada a los administradores del evento (403).

    Se usa cuando el permiso no depende de la propiedad de un recurso sino
    del rol del actor (por ejemplo: override de acceso a fiesta o
    regeneración del código QR).
    """

    code: str = "ADMIN_REQUIRED"

    def __init__(self):
        self.code = self.code
        super().__init__(
            "Esta acción está reservada para los administradores del evento."
        )


class UnprocessableEntityError(HttpError):
    """Excepción para requests válidos en forma pero inválidos en contenido (422).

    Es la categoría "Validation" del catálogo público: el estado del recurso es
    correcto, lo que el cliente envió no lo es. El mensaje público sale del
    catálogo `PUBLIC_ERROR_MESSAGES`; esta clase sólo declara el código estable
    y el status.
    """

    code: str = "VALIDATION_ERROR"

    def __init__(
        self,
        message: str = "La solicitud no es válida.",
        code: str | None = None,
    ):
        self.code = code or self.code
        super().__init__(422, message)



class CipNotFoundError(HttpError):
    """Excepción cuando un CIP no es encontrado en la API externa (404)."""

    code: str = "CIP_NOT_FOUND"

    def __init__(self, cip: str):
        self.code = self.code
        super().__init__(404, f"CIP {cip} no encontrado")


# --- 2. Registro de Manejadores Globales ---


def register_exception_handlers(api):
    """
    Configura cómo NinjaAPI debe responder ante excepciones de Django o Pydantic.
    """

    @api.exception_handler(ObjectDoesNotExist)
    def on_object_not_found(request: HttpRequest, exc: ObjectDoesNotExist):
        """Maneja cualquier .get() de Django que no encuentre resultados."""
        details = {"non_field_errors": "No se pudo encontrar el objeto solicitado."}
        body, status = error_response(
            code="NOT_FOUND",
            message=humanize_validation_errors(details),
            details=details,
            status=404,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(PermissionDenied)
    def on_permission_denied(request: HttpRequest, exc: PermissionDenied):
        """Maneja errores de permisos (403)."""
        details = {
            "non_field_errors": "No tienes autorización para realizar esta acción."
        }
        body, status = error_response(
            code="PERMISSION_DENIED",
            message=humanize_validation_errors(details),
            details=details,
            status=403,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(NinjaAuthenticationError)
    def on_ninja_authentication_error(
        request: HttpRequest, exc: NinjaAuthenticationError
    ):
        """401 — falta el token o el encabezado Authorization.

        La autenticación JWT responde antes que cualquier permiso: un cliente
        anónimo recibe 401 y nunca llega a la comprobación de autorización.
        El mensaje público sale del catálogo; el detalle técnico (token
        inválido, expirado, usuario inactivo) se queda en los logs.
        """
        public_message = PUBLIC_ERROR_MESSAGES["AUTHENTICATION_REQUIRED"]
        details = {"non_field_errors": public_message}
        body, status = error_response(
            code="AUTHENTICATION_REQUIRED",
            message=public_message,
            details=details,
            status=401,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(NinjaExtraAuthenticationFailed)
    def on_ninja_extra_authentication_failed(
        request: HttpRequest, exc: NinjaExtraAuthenticationFailed
    ):
        """401 — token inválido, expirado o revocado; usuario inactivo.

        `ninja_jwt.exceptions.InvalidToken` hereda de esta clase, así que el
        mismo catálogo cubre el token roto y el token vencido.

        Sólo se registra el TIPO de excepción: el detalle técnico (y el token)
        nunca se escribe en los logs ni sale en la respuesta.
        """
        logger.info("Authentication failed (%s).", type(exc).__name__)
        public_message = PUBLIC_ERROR_MESSAGES["AUTHENTICATION_REQUIRED"]
        details = {"non_field_errors": public_message}
        body, status = error_response(
            code="AUTHENTICATION_REQUIRED",
            message=public_message,
            details=details,
            status=401,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(NinjaExtraPermissionDenied)
    def on_ninja_extra_permission_denied(
        request: HttpRequest, exc: NinjaExtraPermissionDenied
    ):
        """403 — el actor está autenticado pero el permiso no lo autoriza.

        Es la respuesta de `RequireAdmin` y de cualquier clase de permisos
        que rechace la petición. El código público es estable
        (`ACTION_NOT_ALLOWED`) y no revela la regla interna de autorización.
        """
        logger.info(
            "Authorization denied on %s %s.",
            request.method,
            request.path,
        )
        public_message = PUBLIC_ERROR_MESSAGES["ACTION_NOT_ALLOWED"]
        details = {"non_field_errors": public_message}
        body, status = error_response(
            code="ACTION_NOT_ALLOWED",
            message=public_message,
            details=details,
            status=403,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(PydanticValidationError)
    def on_pydantic_validation_error(
        request: HttpRequest, exc: PydanticValidationError
    ):
        """
        Maneja errores de validación de Pydantic (esquemas).
        Estandariza los errores para el consumo directo por el frontend.
        """
        details = format_errors(exc.errors(include_input=False))
        body, status = error_response(
            code="VALIDATION_ERROR",
            message=humanize_validation_errors(details),
            details=details,
            status=422,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(NinjaValidationError)
    def on_ninja_validation_error(request: HttpRequest, exc: NinjaValidationError):
        """
        Maneja errores de validación en tiempo de ejecución inyectados por el router Ninja.
        """
        details = format_errors(exc.errors)
        body, status = error_response(
            code="VALIDATION_ERROR",
            message=humanize_validation_errors(details),
            details=details,
            status=422,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(HttpError)
    def on_http_error(request: HttpRequest, exc: HttpError):
        """Maneja errores explícitos del tipo HttpError o sus subclases."""
        code = getattr(exc, "code", "HTTP_ERROR")
        public_message = PUBLIC_ERROR_MESSAGES.get(code)
        if public_message:
            # El mensaje público sale del catálogo: la excepción nunca decide
            # lo que el usuario ve.
            details = {"non_field_errors": public_message}
            message = public_message
        else:
            if isinstance(exc.message, (list, dict)):
                details = exc.message
            else:
                details = {"non_field_errors": exc.message}
            message = (
                humanize_validation_errors(details) or "Error en la petición del API."
            )
        body, status = error_response(
            code=code,
            message=message,
            details=details,
            status=exc.status_code,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(DjangoValidationError)
    def on_django_validation_error(request: HttpRequest, exc: DjangoValidationError):
        """Maneja errores de validación internos de Django (ej: unique_together)."""
        details = (
            exc.message_dict
            if hasattr(exc, "message_dict")
            else {"non_field_errors": exc.messages}
        )
        body, status = error_response(
            code="VALIDATION_ERROR",
            message=humanize_validation_errors(details) or "Error de validación interna.",
            details=details,
            status=400,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(ValueError)
    def on_value_error(request: HttpRequest, exc: ValueError):
        """Maneja ValueError (ej: credenciales inválidas → 401."""
        details = {"non_field_errors": str(exc)}
        body, status = error_response(
            code="AUTH_ERROR",
            message=str(exc),
            details=details,
            status=401,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(IntegrityError)
    def on_integrity_error(request: HttpRequest, exc: IntegrityError):
        """Maneja conflictos de base de datos (Unique constraints, etc.).

        Este handler es el fallback genérico. Los flujos deberían atrapar
        IntegrityError y traducirlo a una excepción de dominio específica
        (ej: InscripcionUniqueConstraintError) ANTES de propagarse. Si llega
        aquí, es una violación de integridad no contemplada explícitamente
        por un flujo — la registramos en logs sin volcar traceback a stderr.
        """
        logger.exception("Unhandled IntegrityError: %s", exc)
        details = {
            "non_field_errors": "Un campo único ya existe o hay una violación de integridad."
        }
        body, status = error_response(
            code="CONFLICT",
            message=humanize_validation_errors(details),
            details=details,
            status=409,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(Exception)
    def on_unhandled_exception(request: HttpRequest, exc: Exception):
        """Atrapa-todo para errores inesperados del servidor (500)."""
        logger.exception("Unhandled exception: %s", exc)
        body, status = error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            status=500,
        )
        return api.create_response(request, body, status=status)
