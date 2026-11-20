"""Public error catalog and the single HTTP error translation point.

Freeze: `FREEZE-ENV-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-01-envelope-error-pagination.md`
Contract: `contract/api-wrapper-presenter-contract.md` §8 ·
         `contract/django-app-architecture-contract.md` §10 (Exceptions)

Ownership (A0, paquete FND-01): this module is the ONLY place that turns an
exception into an HTTP response. Controllers never build error responses.

Two invariants travel with this module:

1. **The public message always comes from the catalog.** A domain exception
   declares a stable machine-readable `code`; the public Spanish prose lives in
   `PUBLIC_ERROR_MESSAGES`. A code that is not in the catalog falls back to a
   generic message derived from the HTTP status — never to `str(exc)`.
2. **Raw exception text never reaches the client.** UUIDs, internal ids,
   request ids, SQL constraints, traces, filesystem paths, provider payloads,
   credentials and raw exception messages are logged server-side and never
   serialized into the response.

Field-level errors travel in `error.field_errors` (the ONLY field-error
channel). `error.details` carries non-field context only.
"""

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
from .utils import humanize_validation_errors
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
    # ── Transversales del contrato de wrappers (§8) ─────────────────────────
    # Categorías HTTP congeladas en FR-01 §4.4. Son el fallback de cualquier
    # excepción cuyo código no esté en el catálogo: el mensaje es genérico
    # pero SIEMPRE es prosa pública segura.
    "AUTHENTICATION_REQUIRED": (
        "Debes iniciar sesión para acceder a este recurso."
    ),
    "AUTH_ERROR": (
        "No se pudieron validar las credenciales."
    ),
    "ACTION_NOT_ALLOWED": (
        "No tienes autorización para realizar esta acción."
    ),
    "PERMISSION_DENIED": (
        "No tienes autorización para realizar esta acción."
    ),
    "ADMIN_REQUIRED": (
        "Esta acción está reservada para los administradores del evento."
    ),
    "RESOURCE_NOT_FOUND": (
        "No se encontró el recurso solicitado."
    ),
    "NOT_FOUND": (
        "No se encontró el recurso solicitado."
    ),
    "CIP_NOT_FOUND": (
        "No se encontró la información solicitada."
    ),
    "VALIDATION_ERROR": (
        "La solicitud no es válida."
    ),
    "INVALID_REQUEST": (
        "La solicitud contiene parámetros no válidos."
    ),
    "BUSINESS_ERROR": (
        "La solicitud no es válida."
    ),
    "CONFLICT": (
        "Conflicto con el estado actual del recurso."
    ),
    "INTERNAL_ERROR": (
        "Ocurrió un error inesperado. Inténtalo nuevamente."
    ),
    # ── Multimedia (FREEZE-MD-1.0.0 · FR-06 §2.3, §2.4) ───────────────────
    # Códigos estables del contrato de media. La firma de contenido que no
    # corresponde al MIME declarado se rechaza con MEDIA_TIPO_NO_PERMITIDO
    # (FR-06 §2.3), no con un código propio.
    "MEDIA_TIPO_NO_PERMITIDO": (
        "El tipo de archivo enviado no está permitido."
    ),
    "MEDIA_TAMANO_EXCEDIDO": (
        "El archivo enviado excede el tamaño permitido."
    ),
    "MEDIA_TOKEN_NO_RESUELTO": (
        "La referencia de archivo no se encontró en la petición."
    ),
    "MEDIA_ARCHIVO_HUERFANO": (
        "La petición incluye archivos que no fueron referenciados."
    ),
    "MEDIA_TOKEN_DUPLICADO": (
        "La petición incluye archivos duplicados."
    ),
    "MEDIA_DIMENSIONES_INVALIDAS": (
        "Las dimensiones del archivo enviado no están permitidas."
    ),
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
    # ── Alcance de edición (FND-02 · FREEZE-ED-1.0.0) ───────────────────────
    # A0-01 del paquete FND-02. Los códigos ya viajan estables en `error.code`;
    # aquí sólo se les da la prosa pública segura. Ninguna de estas prosa
    # interpola slugs, UUIDs, nombres ni años: la lista de candidatas de
    # `EDICION_AMBIGUA` viaja en la excepción del dominio (`candidatas`), no
    # en el texto público (decisión `D-FND-02-08`, ver la evidencia de FND-01).
    # 404 — no existe / no se puede resolver la edición pedida.
    "EDICION_NO_ENCONTRADA": (
        "No se encontró la edición solicitada."
    ),
    "EDICION_NO_PUBLICADA": (
        "La edición solicitada no está publicada."
    ),
    "EDICION_NO_RESUELTA": (
        "No se pudo resolver una edición para el alcance solicitado."
    ),
    "EVENTO_NO_ENCONTRADO": (
        "No se encontró el evento solicitado."
    ),
    # 409 — conflicto de negocio con la edición.
    "EDICION_AMBIGUA": (
        "Hay más de una edición posible para el alcance solicitado."
    ),
    "EDICION_SLUG_DUPLICADO": (
        "Ya existe una edición con ese identificador en el evento."
    ),
    "EDICION_PUBLICADA_DUPLICADA": (
        "El evento ya tiene una edición publicada."
    ),
    "MODULO_NO_HABILITADO": (
        "Esta funcionalidad no está habilitada en la edición."
    ),
    # ── Identidad / fuente externa (FND-03 · FREEZE-ID-1.0.0) ───────────────
    # A0-01 del paquete FND-03. 503/504 son RECUPERABLES: el cliente puede
    # reintentar. El mensaje nunca dice si el documento existe.
    "FUENTE_EXTERNA_NO_DISPONIBLE": (
        "La fuente externa de documentos no está disponible. Inténtalo nuevamente."
    ),
    "FUENTE_EXTERNA_TIMEOUT": (
        "La fuente externa de documentos no respondió a tiempo. Inténtalo nuevamente."
    ),
    # 422 — la fuente externa no devolvió datos suficientes.
    "PERSONA_DATOS_INCOMPLETOS": (
        "La fuente externa no devolvió datos suficientes para esa identidad."
    ),
    # 409 — el documento ya está vinculado a una cuenta.
    "PERSONA_DUPLICADA": (
        "Ese documento ya está vinculado a una cuenta."
    ),
    # ── Idempotencia y confirmación de pago (FND-04 · FREEZE-CM-1.0.0) ──────
    # A0-04 del paquete FND-04. 409 — la clave identifica UNA intención: reused
    # con otro payload es un error del cliente, no una repetición tolerada.
    "IDEMPOTENCY_KEY_REUTILIZADA": (
        "La clave de idempotencia ya se usó con una operación diferente."
    ),
    "IDEMPOTENCY_KEY_INVALIDA": (
        "La clave de idempotencia no es válida."
    ),
    # 409 — la orden no admite una confirmación en su estado actual.
    "ORDEN_PAGO_NO_PAGABLE": (
        "La orden de pago no admite una confirmación en su estado actual."
    ),
    # 422 — el total declarado no coincide con el total derivado de las líneas.
    "COMPRA_TOTAL_INCOHERENTE": (
        "El total de la compra no coincide con sus líneas."
    ),
    "COMPRA_REFERENCIA_INVALIDA": (
        "La referencia de la compra no es válida."
    ),
    # 404 — la compra referenciada no existe.
    "COMPRA_NO_ENCONTRADA": (
        "No se encontró la compra solicitada."
    ),
    # ── Inscripciones / catálogo de inscripción (DOM-01 · FREEZE-PS-1.0.0) ──
    # A0-03 del paquete DOM-01. Los códigos viajan estables en `error.code`;
    # aquí sólo se les da la prosa pública segura. Ninguna prosa interpola
    # slugs, UUIDs, ids internos, precios ni nombres de personas.
    # 409 — el paquete no es comprable en el alcance pedido (no existe, está
    # retirado o no tiene precio vigente). No se inventa un precio de reserva.
    "PAQUETE_NO_VIGENTE": (
        "El paquete seleccionado no está disponible para esta edición."
    ),
    # 422 — la disciplina no pertenece a la edición o no está incluida en el
    # paquete. El padrón NO lo elige el cliente.
    "DISCIPLINA_NO_PERMITIDA": (
        "La disciplina seleccionada no está permitida para este paquete."
    ),
    # 422 — la inscripción declara dos equipos para la misma disciplina.
    "EQUIPO_DUPLICADO": (
        "No puede declarar dos equipos para la misma disciplina."
    ),
    # 404 — la inscripción solicitada no existe.
    "INSCRIPCION_NO_ENCONTRADA": (
        "No se encontró la inscripción solicitada."
    ),
    # 403 — el actor no es el responsable de la inscripción. Ser
    # administrador NO sustituye la titularidad.
    "INSCRIPCION_NO_AUTORIZADA": (
        "No tienes autorización para gestionar esta inscripción."
    ),
    # 422 — la cuenta autenticada no tiene una persona vinculada: una cuenta
    # técnica no puede ser responsable de una inscripción.
    "COMPRADOR_SIN_PERSONA": (
        "La cuenta no tiene una persona vinculada."
    ),
    # ── Marketplace / catálogo de productos (DOM-04 · FREEZE-MD-1.0.0) ─────
    # A0-06 del paquete DOM-04. Prosa FIJA propuesta por el propio paquete:
    # no expone slugs, ids, rutas de disco ni montos.
    # 404 — el producto no existe dentro del alcance de edición.
    "PRODUCTO_NO_ENCONTRADO": (
        "No se encontró el producto solicitado."
    ),
    # 409 — ya existe un producto con el mismo slug en la misma edición.
    "PRODUCTO_SLUG_DUPLICADO": (
        "Ya existe un producto con ese identificador en la edición."
    ),
    # 409 — el producto no está disponible para la operación solicitada.
    "PRODUCTO_NO_DISPONIBLE": (
        "El producto seleccionado no está disponible."
    ),
    # 422 — la categoría indicada pertenece a OTRA edición que el producto.
    "PRODUCTO_CATEGORIA_INCOHERENTE": (
        "La categoría indicada pertenece a otra edición."
    ),
    # 404 — la categoría de producto solicitada no existe en el alcance.
    "CATEGORIA_PRODUCTO_NO_ENCONTRADA": (
        "No se encontró la categoría de producto solicitada."
    ),
    # 409 — ya existe una categoría con el mismo slug en la misma edición.
    "CATEGORIA_PRODUCTO_SLUG_DUPLICADO": (
        "Ya existe una categoría con ese identificador en la edición."
    ),
    # 404 — la imagen indicada no pertenece al producto del alcance.
    "PRODUCTO_IMAGEN_NO_ENCONTRADA": (
        "No se encontró la imagen de producto solicitada."
    ),
    # 422 — la oferta no es coherente (precio negativo o ventana invertida).
    "OFERTA_INVALIDA": (
        "La oferta indicada no es válida."
    ),
    # 422 — la galería no es coherente (más de una imagen principal).
    "GALERIA_INVALIDA": (
        "La galería del producto no es válida."
    ),
    # ── DOM-03 · Pases, beneficiarios y cortesía (A0-03 / A0-04) ────────────
    # Reconciliación A0 de 2026-11-19 del paquete DOM-03. Los códigos viajan
    # estables en `error.code`; aquí sólo se les da la prosa pública segura.
    # Ninguna prosa interpola UUIDs, ids internos, slugs, precios, rutas de
    # disco, restricciones SQL, payloads de proveedor ni credenciales.
    #
    # CUATRO códigos de este paquete YA estaban catalogados y NO se duplican:
    # `PASE_NO_DISPONIBLE` (409), `PASE_NO_ENCONTRADO` (404),
    # `PASE_NO_TRANSFERIBLE` (409) y `PASE_BENEFICIARIO_NO_ENCONTRADO` (404).
    # Los cuatro están CONGELADOS por el ledger `FR-07` §3.3 para `RT-CM-02` y
    # `RT-RT-03`, y su status coincide con la clase de dominio.
    # 422 — la cantidad de pases solicitados no es válida. CÓDIGO CONGELADO
    # por el ledger `FR-07` §3.3 para `RT-CM-02`.
    "CANTIDAD_INVALIDA": (
        "La cantidad de pases solicitados no es válida."
    ),
    # 404 — la compra de pases solicitada no existe.
    "COMPRA_PASE_NO_ENCONTRADA": (
        "No se encontró la compra de pases solicitada."
    ),
    # 409 — la persona ya tiene un derecho activo de ese pase. La no
    # duplicación la impone la base de datos: es UNA sola regla para los dos
    # orígenes (compra y cortesía).
    "PASE_DUPLICADO": (
        "La persona ya tiene un pase activo de este tipo en la edición."
    ),
    # 409 — el lote no tiene capacidad pagada libre para asignar.
    "SIN_PASES_DISPONIBLES": (
        "No hay pases disponibles para asignar en esta compra."
    ),
    # 409 — una compra pendiente NO habilita ningún pase (`RN-P02`).
    "COMPRA_PASE_NO_PAGADA": (
        "La compra de pases todavía no está pagada."
    ),
    # 401 — el enlace de gestión no es válido: la credencial está ausente,
    # expirada o revocada. Es un fallo de AUTENTICACIÓN, no de autorización.
    "TOKEN_PASE_INVALIDO": (
        "El enlace de gestión del pase no es válido."
    ),
    # 401 — la operación exige una cuenta autenticada: una cortesía sin actor
    # no es auditable (`RN-P05`).
    "ACTOR_REQUERIDO": (
        "Debes iniciar sesión para realizar esta operación."
    ),
    # 403 — el actor no es el titular de la compra. Ser administrador NO
    # sustituye la titularidad (`FR-03` §2.1).
    "COMPRA_PASE_NO_AUTORIZADA": (
        "No tiene autorización para gestionar esta compra de pases."
    ),
    # 422 — el motivo de la cortesía es obligatorio: sin motivo no es
    # auditable (`RN-P05`).
    "CORTESIA_MOTIVO_INVALIDO": (
        "El motivo de la cortesía es obligatorio."
    ),
    # 404 — la cortesía solicitada no existe.
    "CORTESIA_NO_ENCONTRADA": (
        "No se encontró la cortesía solicitada."
    ),
    # ── DOM-02 · Pool de cupos, asignación y ampliación (A0-DOM02-03) ────────
    # Petición de A0 del paquete DOM-02 que quedó PENDIENTE y se mergea aquí:
    # la misma raíz compartida (`salesianos_fest`) y la misma dependencia del
    # catálogo. `CUPO_INVALIDO` está CONGELADO por el ledger `FR-07` §3.3
    # para `RT-CM-01`, que es una ruta VIVA: sin prosa pública el mensaje cae
    # al genérico del status.
    # 422 — la cantidad de cupos solicitados no es válida. CÓDIGO CONGELADO
    # por el ledger `FR-07` §3.3 para `RT-CM-01`.
    "CUPO_INVALIDO": (
        "La cantidad de cupos solicitados no es válida."
    ),
    # 409 — la inscripción no tiene cupos pagados disponibles.
    "SIN_CUPOS_DISPONIBLES": (
        "No hay cupos pagados disponibles en esta inscripción."
    ),
    # 422 — la persona no cumple las reglas de elegibilidad: disciplina
    # activa, pertenencia a la edición, compatibilidad de modalidad o
    # solapamiento. El servidor decide, el cliente no lo sortea.
    "PARTICIPANTE_NO_ELEGIBLE": (
        "La persona no cumple las condiciones de elegibilidad para este equipo."
    ),
    # 422 — la persona ya participa activamente en esta inscripción.
    "PARTICIPANTE_DUPLICADO": (
        "La persona ya participa activamente en esta inscripción."
    ),
    # 409 — el equipo alcanzó el máximo de participantes de su disciplina.
    "EQUIPO_COMPLETO": (
        "El equipo alcanzó el máximo de participantes permitido."
    ),
    # 404 — la participación solicitada no existe o no pertenece a la
    # inscripción.
    "PARTICIPANTE_NO_ENCONTRADO": (
        "No se encontró la participación solicitada."
    ),
    # 404 — el equipo solicitado no existe o no pertenece a la inscripción.
    "EQUIPO_NO_ENCONTRADO": (
        "No se encontró el equipo solicitado."
    ),
    # `PERSONA_NO_ENCONTRADA` (404) ya estaba catalogado por FND-03: no se
    # duplicó.
    # ── DOM-05 · Pedido de marketplace (A0 · cierre del cableado) ────────────
    # Códigos estables del módulo `modules.marketplace` (DOM-05). El status lo
    # fija la CLASE de excepción del dominio; aquí sólo se les da la prosa
    # pública segura. Ninguna prosa interpola tokens, ids, slugs, precios,
    # rutas de disco ni texto crudo (`contract/api-wrapper-presenter-contract.md`
    # §8).
    # 404 — el pedido no existe dentro del alcance. La denegación es NEUTRAL:
    # un token desconocido y un pedido de otra persona se responden igual.
    "PEDIDO_NO_ENCONTRADO": (
        "No se encontró el pedido solicitado."
    ),
    # 403 — el actor autenticado NO es el comprador del pedido. Ser
    # administrador NO sustituye la titularidad (`RN-U02`).
    "PEDIDO_NO_AUTORIZADO": (
        "No tienes autorización para consultar este pedido."
    ),
    # 422 — el pedido mezcla artículos de distintos orígenes (`RN-C01`).
    "PEDIDO_ITEMS_MIXTOS": (
        "No se pueden combinar artículos de distintos orígenes."
    ),
    # 409 — el pedido declara un artículo que no pertenece a la tienda.
    "PEDIDO_ITEM_NO_PERMITIDO": (
        "El pedido sólo puede incluir productos de la tienda."
    ),
    # 422 — la cantidad declarada de un artículo no es válida.
    "PEDIDO_CANTIDAD_INVALIDA": (
        "La cantidad solicitada no es válida."
    ),
    # ── DOM-06 · Inventario, reserva y entrega (A0 · cierre del cableado) ────
    # 409 — no hay existencias suficientes para la cantidad pedida (`RN-M06`).
    # CÓDIGO CONGELADO por el ledger `FR-07` §3.3 para `RT-CM-03`.
    "STOCK_INSUFICIENTE": (
        "No hay existencias suficientes para la cantidad solicitada."
    ),
    # 404 — el movimiento de inventario indicado no existe.
    "MOVIMIENTO_INVENTARIO_NO_ENCONTRADO": (
        "No se encontró el movimiento de inventario solicitado."
    ),
    # 422 — el movimiento declarado no es coherente con su naturaleza (`RN-M04`).
    "MOVIMIENTO_INVENTARIO_INVALIDO": (
        "El movimiento de inventario no es válido."
    ),
    # 409 — un movimiento ya registrado no se puede modificar: la bitácora es
    # INMUTABLE y la corrección es un movimiento compensatorio.
    "MOVIMIENTO_INVENTARIO_INMUTABLE": (
        "El movimiento de inventario no se puede modificar."
    ),
    # 409 — el pedido todavía no está pagado: no se puede entregar (`RN-M07`).
    "PEDIDO_NO_PAGADO": (
        "El pedido todavía no está pagado."
    ),
    # 409 — el pedido no se puede entregar en su estado actual.
    "PEDIDO_NO_ENTREGABLE": (
        "El pedido no se puede entregar."
    ),
    # 409 — el pedido no tiene existencias reservadas (`RN-M06`).
    "PEDIDO_SIN_RESERVA": (
        "El pedido no tiene existencias reservadas."
    ),
    # 409 — la reserva del pedido fue liberada: su venta ya no se puede
    # confirmar (`RN-C08`).
    "RESERVA_NO_CONFIRMABLE": (
        "Las existencias del pedido ya no están reservadas."
    ),
    # ── DOM-07 · Competencias, cuadro y agenda (A0 · cierre del cableado) ────
    # Códigos estables del módulo `modules.competencias` (DOM-07). Los códigos
    # ya catalogados por A0 (`COMPETENCIA_DUPLICADA`, `COMPETENCIA_NOT_FOUND`,
    # `RONDA_NOT_FOUND`, `ENCUENTRO_NOT_FOUND`, `COMPETENCIA_EQUIPO_NOT_FOUND`,
    # `EQUIPO_NO_ELEGIBLE`, `EQUIPO_SOLAPADO`, `SLOT_OCUPADO`,
    # `DESTINO_BLOQUEADO`, `INVALID_STATE_TRANSITION`, `INVALID_SCHEDULE`,
    # `INVALID_WINNER`, `INVALID_LINK`, `REASON_REQUIRED`, `DELETE_NOT_ALLOWED`,
    # `RESOURCE_CHANGED`) NO se duplican.
    # 404 — el recurso no existe dentro del alcance de la edición.
    "COMPETENCIA_NO_ENCONTRADA": (
        "No se encontró la competencia solicitada."
    ),
    "COMPETENCIA_EQUIPO_NO_ENCONTRADA": (
        "No se encontró la participación del equipo en la competencia."
    ),
    "RONDA_NO_ENCONTRADA": (
        "No se encontró la ronda solicitada."
    ),
    "ENCUENTRO_NO_ENCONTRADO": (
        "No se encontró el encuentro solicitado."
    ),
    "DISCIPLINA_NO_ENCONTRADA": (
        "No se encontró la disciplina solicitada."
    ),
    # 404 — la categoría es un hecho del DUEÑO (`salesianos_fest`) que
    # `competencias` sólo REFERENCIA: si no existe —o es de otra edición— no
    # se puede usar en una competencia. El código lo declara el módulo que lo
    # usa; la PROSA es de A0.
    "CATEGORIA_NO_ENCONTRADA": (
        "No se encontró la categoría solicitada."
    ),
    # 409 — el equipo ya está incorporado a la competencia.
    "COMPETENCIA_EQUIPO_DUPLICADO": (
        "El equipo ya está incorporado a esta competencia."
    ),
    # 409 — el orden ya está ocupado por otra entrada activa.
    "ORDEN_DUPLICADO": (
        "Ese orden ya está ocupado."
    ),
    # 409 — ya existe una ronda con esa etiqueta o ese orden.
    "RONDA_DUPLICADA": (
        "Ya existe una ronda con esa etiqueta o ese orden."
    ),
    # 409 — el equipo ya juega en esa franja horaria (`RN-K03`).
    "SOLAPAMIENTO_HORARIO": (
        "Uno de los equipos ya tiene un encuentro en esa franja horaria."
    ),
    # 422 — el horario no es un intervalo positivo del día de la competencia.
    "HORARIO_INVALIDO": (
        "El horario debe ser un intervalo positivo dentro del día de la competencia."
    ),
    # 422 — la operación protegida exige un motivo auditado.
    "MOTIVO_REQUERIDO": (
        "Debes indicar el motivo del cambio."
    ),
    # 409 — el estado actual del encuentro no admite la operación.
    "TRANSICION_INVALIDA": (
        "El estado actual del encuentro no admite esta operación."
    ),
    # 422 — el ganador propuesto no ocupa ninguno de los dos slots.
    "GANADOR_INVALIDO": (
        "El ganador debe ser uno de los participantes del encuentro."
    ),
    # 422 — el enlace al siguiente encuentro no es válido.
    "ENLACE_INVALIDO": (
        "El enlace al siguiente encuentro no es válido."
    ),
    # 422 — un bye manual exige exactamente un equipo.
    "BYE_INVALIDO": (
        "Un bye manual requiere exactamente un equipo en el encuentro."
    ),
    # 422 — el participante propuesto no pertenece a la competencia.
    "PARTICIPANTE_INVALIDO": (
        "El participante no pertenece a esta competencia."
    ),
    # ── DOM-08 · Patrocinadores, logo y galería (A0 · cierre del cableado) ────
    # Códigos estables del módulo `modules.patrocinadores` (DOM-08).
    # 404 — el patrocinador no existe dentro del alcance de edición.
    "PATROCINADOR_NO_ENCONTRADO": (
        "No se encontró el patrocinador solicitado."
    ),
    # 409 — ya existe un patrocinador con el mismo identificador en la edición.
    "PATROCINADOR_SLUG_DUPLICADO": (
        "Ya existe un patrocinador con ese identificador en la edición."
    ),
    # 404 — la imagen indicada no pertenece al patrocinador del alcance.
    "PATROCINADOR_IMAGEN_NO_ENCONTRADA": (
        "No se encontró la imagen de patrocinador solicitada."
    ),
    # 422 — la galería no es coherente con el tope declarado del carrusel.
    "GALERIA_PATROCINADOR_INVALIDA": (
        "La galería del patrocinador no es válida."
    ),
    # ── XCT-01 · Validaciones (A0 · cierre del cableado) ─────────────────────
    # Códigos estables del módulo `modules.validaciones`. El catálogo es
    # GLOBAL: un código declarado por un módulo existente va aquí, esté
    # registrado o no.
    # `IDEMPOTENCY_KEY_REUTILIZADA` (409) ya estaba catalogado por FND-04: no
    # se duplicó.
    # 404 — la credencial no existe en el alcance. La credencial es un
    # SECRETO: la respuesta nunca dice qué códigos existen ni qué derechos hay.
    "TICKET_NO_ENCONTRADO": (
        "No se encontró la credencial solicitada."
    ),
    # 409 — la credencial ya se canjeó por completo (`FL-10` paso 5).
    "TICKET_YA_CONSUMIDO": (
        "La credencial ya fue utilizada."
    ),
    # 409 — la cantidad pedida no se puede confirmar (`FR-05` §2.2).
    "CANTIDAD_EXCEDIDA": (
        "La cantidad solicitada no se puede confirmar."
    ),
    # 409 — el derecho no está vigente para esta operación (`RN-P08`).
    "DERECHO_REVOCADO": (
        "El derecho no está vigente para esta operación."
    ),
    # 500 — no hay adaptador para ese tipo de derecho: es una FALLA DE
    # CONFIGURACIÓN, no un problema del cliente. La prosa es la del status 500
    # (genérica): nunca explica qué tipo de derecho falló.
    "VERIFICADOR_NO_DISPONIBLE": (
        "Ocurrió un error inesperado. Inténtalo nuevamente."
    ),
    # ── Promociones, categorías y cotización (A0 · solicitud del dueño) ─────
    # Códigos estables del módulo `modules.salesianos_fest`. El módulo los
    # declara y REQUIERE su prosa pública ("Código REQUESTED a A0").
    # `CANTIDAD_INVALIDA` ya existía (lo declaró DOM-03 para los pases) y NO
    # se reutiliza aquí: `CANTIDAD_INSUFICIENTE` es un hecho DISTINTO y tiene
    # su propio código, porque su prosa habla de participantes y de paquete,
    # no de pases.
    # 404 — la promoción indicada no existe o no está activa.
    "PROMOCION_NO_ENCONTRADA": (
        "No se encontró la promoción solicitada."
    ),
    # 422 — la promoción de la inscripción no cae en ninguna categoría activa
    # de la edición: la inscripción no tiene banda con la que competir.
    "CATEGORIA_NO_RESUELTA": (
        "La promoción seleccionada no corresponde a ninguna categoría de esta edición."
    ),
    # 422 — la promoción fusionada es la MISMA que la principal.
    "FUSION_PROMOCION_INVALIDA": (
        "La promoción fusionada debe ser distinta de la promoción principal."
    ),
    # 422 — la cantidad de participantes no alcanza el mínimo comercial del
    # paquete.
    "CANTIDAD_INSUFICIENTE": (
        "La cantidad de participantes no alcanza el mínimo de compra del paquete."
    ),
    # 422 — los equipos declarados no cumplen la regla de disciplinas del
    # paquete (`FIJO` exige exactamente las vinculadas; `ELEGIBLE` admite hasta
    # el número declarado por el paquete).
    "EQUIPOS_FUERA_DE_PAQUETE": (
        "Los equipos declarados no cumplen las disciplinas del paquete."
    ),
    # 409 — el precio del catálogo se movió entre la cotización y el alta
    # (`RN-C02`). Es la regla de CONCURRENCIA de la cotización: el comprador
    # devuelve el token `cotizacion_version` y, si el catálogo ya no está en
    # la versión cotizada, el alta se rechaza en vez de cobrar una cantidad
    # que nadie vio. La prosa NO interpola el precio ni su importe: la
    # siguiente acción segura (volver a cotizar) es lo que el cliente necesita.
    "PRECIO_CAMBIADO": (
        "El precio del paquete cambió desde la cotización. Vuelve a cotizar."
    ),
    # ── Identidad y pagos (A0 · cierre del cableado) ─────────────────────────
    # 403 — la cuenta está desactivada: la contraseña es correcta pero la
    # cuenta no puede operar. Es un estado DISTINTO de "credenciales
    # inválidas" (401).
    "CUENTA_INACTIVA": (
        "La cuenta está desactivada."
    ),
    # 400 — la petición de pago es malformada o no verificable. La clase base
    # `ErrorPago400` la lanzan los errores tipados de pago que reutilizan su
    # status de ledger (`FR-07` §3.3).
    "PAGO_INVALIDO": (
        "La solicitud de pago no es válida."
    ),
    # ── Sala de proyección (cambio `public-video-streaming-crud`) ───────────
    # Códigos estables del módulo `modules.videos`. La prosa es FIJA y no
    # interpola URLs, UUIDs ni identificadores: un `javascript:` o un `data:`
    # rechazados no se leen de vuelta en la respuesta.
    # 404 — el video solicitado no existe.
    "VIDEO_NO_ENCONTRADO": (
        "No se encontró el video solicitado."
    ),
    # 422 — la URL no es una dirección `http`/`https` válida.
    "VIDEO_URL_INVALIDA": (
        "La URL del video no es válida."
    ),
}

# Fallback genérico por status HTTP (FR-01 §4.4). Se usa cuando el código de
# la excepción NO está en el catálogo público: la respuesta sigue siendo
# segura y tipada, pero el mensaje es genérico y el detalle técnico queda
# únicamente en los logs del servidor.
GENERIC_PUBLIC_MESSAGES = {
    400: "La solicitud no es válida.",
    401: "Debes iniciar sesión para acceder a este recurso.",
    403: "No tienes autorización para realizar esta acción.",
    404: "No se encontró el recurso solicitado.",
    405: "El método no está permitido para este recurso.",
    409: "Conflicto con el estado actual del recurso.",
    413: "El archivo enviado excede el tamaño permitido.",
    415: "El tipo de contenido enviado no es compatible.",
    422: "La solicitud no es válida.",
    # 503/504 — dependencia externa no disponible o lenta: el mensaje es
    # genérico y recuperable, nunca dice qué dependencia falló (A0-05, FND-04).
    503: "Un servicio externo no está disponible. Inténtalo nuevamente.",
    504: "Un servicio externo no respondió a tiempo. Inténtalo nuevamente.",
    500: "Ocurrió un error inesperado. Inténtalo nuevamente.",
}

# Mensaje genérico para un error de campo cuyo texto original no se puede
# exponer de forma segura.
GENERIC_FIELD_MESSAGE = "Revisa el valor de este campo."

# Códigos de error de campo derivados de los tipos de error de Pydantic.
FIELD_ERROR_CODES = {
    "missing": "REQUIRED",
    "extra_forbidden": "UNEXPECTED_FIELD",
}

# Códigos de error de Django traducidos a prosa pública segura. El mensaje
# original de Django puede interpolar el valor que falló, así que NUNCA se
# expone: se usa el código del error para elegir una prosa fija.
DJANGO_VALIDATION_MESSAGES = {
    "required": "Este campo es obligatorio.",
    "null": "Este campo no admite un valor vacío.",
    "blank": "Este campo es obligatorio.",
    "unique": "Ya existe un registro con este valor.",
    "unique_together": "Ya existe un registro con esta combinación de valores.",
    "invalid_choice": "El valor seleccionado no es válido.",
    "invalid": "El valor indicado no es válido.",
    "min_value": "El valor indicado es menor al permitido.",
    "max_value": "El valor indicado es mayor al permitido.",
    "min_length": "El texto indicado es más corto de lo permitido.",
    "max_length": "El texto indicado es más largo de lo permitido.",
}

# Prefijos de ubicación que Pydantic/Ninja anteponen al `loc` de un error.
# Se descartan para que la ruta del campo sea la del payload (FR-01 §4.2).
_LOCATION_PREFIXES = ("body", "query", "path", "header", "cookie", "files")


# ── Helpers de traducción (A0) ───────────────────────────────────────────────


def public_message_for(code: str, status: int) -> str:
    """The public message for a stable error code.

    Never returns raw exception text: the catalog wins, and a code that is not
    catalogued falls back to the generic message of the HTTP status.
    """
    message = PUBLIC_ERROR_MESSAGES.get(code)
    if message:
        return message
    return GENERIC_PUBLIC_MESSAGES.get(status, GENERIC_PUBLIC_MESSAGES[500])


def _field_path(loc) -> str:
    """Build the dotted field path of a validation error.

    `beneficiarios.0.documento` — the location prefix (`body`, `query`, …) is
    dropped because it describes the transport, not the payload.
    """
    parts = [str(part) for part in (loc or ()) if part is not None]
    if parts and parts[0] in _LOCATION_PREFIXES:
        parts = parts[1:]
    if not parts:
        return "non_field_errors"
    return ".".join(parts)


def field_errors_from_pydantic(errors: list) -> list[dict]:
    """Convert Pydantic errors into the frozen `field_errors` shape.

    The `input` value is never requested (`include_input=False` upstream), so
    no user value can be echoed back.
    """
    entries: list[dict] = []
    for error in errors or []:
        if not isinstance(error, dict):
            continue
        path = _field_path(error.get("loc"))
        if path == "non_field_errors":
            continue
        entries.append(
            {
                "field": path,
                "code": FIELD_ERROR_CODES.get(error.get("type"), "INVALID_VALUE"),
                "message": str(error.get("msg") or GENERIC_FIELD_MESSAGE),
            }
        )
    return entries


def field_errors_from_django(exc: DjangoValidationError) -> list[dict]:
    """Convert a Django `ValidationError` into the frozen `field_errors` shape.

    Django interpolates the offending value into its default messages, so the
    original text is never exposed: the public message is chosen from the
    error CODE.
    """
    entries: list[dict] = []
    error_dict = getattr(exc, "error_dict", None)
    if not error_dict:
        return entries
    for field, errors in error_dict.items():
        for error in errors:
            code = getattr(error, "code", None)
            entries.append(
                {
                    "field": str(field),
                    "code": str(code) if code else "INVALID_VALUE",
                    "message": DJANGO_VALIDATION_MESSAGES.get(
                        code, GENERIC_FIELD_MESSAGE
                    ),
                }
            )
    return entries


def _split_details(details: dict | None) -> tuple[dict | None, list[dict]]:
    """Split a flat `{field: message}` mapping into (details, field_errors).

    `non_field_errors` stays in `details`; every other key becomes a field
    error. This is the conversion FR-01 §4.2 assigns to the error boundary.
    """
    if not details:
        return None, []

    non_field = details.get("non_field_errors")
    remaining = {k: v for k, v in details.items() if k != "non_field_errors"}

    details_out = {"non_field_errors": non_field} if non_field else None
    field_errors = [
        {
            "field": str(key),
            "code": "INVALID_VALUE",
            "message": str(value),
        }
        for key, value in remaining.items()
    ]
    return details_out, field_errors


def _safe_field_errors_from_mapping(message) -> list[dict]:
    """Field errors for an `HttpError` whose message is a mapping or a list.

    Used when the exception code is NOT catalogued: the per-field prose is
    replaced by the generic safe message so nothing authored ad-hoc escapes.
    """
    entries: list[dict] = []
    if isinstance(message, dict):
        for key, value in message.items():
            if key == "non_field_errors":
                continue
            entries.append(
                {"field": str(key), "code": "INVALID_VALUE", "message": GENERIC_FIELD_MESSAGE}
            )
    elif isinstance(message, list):
        for item in message:
            if isinstance(item, dict):
                field = item.get("loc") or item.get("field")
                entries.append(
                    {
                        "field": _field_path(field if isinstance(field, (list, tuple)) else None),
                        "code": str(item.get("type") or "INVALID_VALUE"),
                        "message": GENERIC_FIELD_MESSAGE,
                    }
                )
    return entries


class NotFoundError(HttpError):
    """Excepción para recursos no encontrados (404).

    El texto que se construye aquí es SOLO técnico: la respuesta pública la
    decide el catálogo a partir de `code`. `resource` y `detail` nunca salen
    al cliente.
    """

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


# ── Multimedia (FREEZE-MD-1.0.0) ─────────────────────────────────────────────


class MediaValidationError(HttpError):
    """Base de los errores de validación de multimedia (FR-06 §2.3, §2.4).

    El código público sale del catálogo; el detalle técnico (bytes leídos,
    nombre declarado, motivo exacto del rechazo) queda en los logs.
    """

    code: str = "MEDIA_TIPO_NO_PERMITIDO"
    status: int = 400

    def __init__(self, code: str | None = None, status: int | None = None):
        self.code = code or self.code
        self.status = status or self.status
        super().__init__(
            self.status,
            public_message_for(self.code, self.status),
        )


class MediaTipoNoPermitidoError(MediaValidationError):
    """MIME fuera de la allowlist o con firma de contenido que no corresponde."""

    code = "MEDIA_TIPO_NO_PERMITIDO"
    status = 400


class MediaTamanoExcedidoError(MediaValidationError):
    """El archivo supera el tamaño máximo permitido."""

    code = "MEDIA_TAMANO_EXCEDIDO"
    status = 413


class MediaTokenNoResueltoError(MediaValidationError):
    """El payload referencia un token de archivo que no llegó en la petición."""

    code = "MEDIA_TOKEN_NO_RESUELTO"
    status = 400


class MediaArchivoHuerfanoError(MediaValidationError):
    """La petición incluye un archivo que ningún campo del payload referencia."""

    code = "MEDIA_ARCHIVO_HUERFANO"
    status = 400


class MediaTokenDuplicadoError(MediaValidationError):
    """Dos archivos declaran el mismo token, o el token se repite en el payload."""

    code = "MEDIA_TOKEN_DUPLICADO"
    status = 400


class MediaDimensionesInvalidasError(MediaValidationError):
    """Las dimensiones del archivo están fuera de los límites configurados."""

    code = "MEDIA_DIMENSIONES_INVALIDAS"
    status = 400


# --- 2. Registro de Manejadores Globales ---


def register_exception_handlers(api):
    """
    Configura cómo NinjaAPI debe responder ante excepciones de Django o Pydantic.
    """

    @api.exception_handler(ObjectDoesNotExist)
    def on_object_not_found(request: HttpRequest, exc: ObjectDoesNotExist):
        """Maneja cualquier .get() de Django que no encuentre resultados."""
        public_message = public_message_for("RESOURCE_NOT_FOUND", 404)
        details = {"non_field_errors": public_message}
        body, status = error_response(
            code="RESOURCE_NOT_FOUND",
            message=public_message,
            details=details,
            status=404,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(PermissionDenied)
    def on_permission_denied(request: HttpRequest, exc: PermissionDenied):
        """Maneja errores de permisos (403)."""
        public_message = public_message_for("ACTION_NOT_ALLOWED", 403)
        details = {"non_field_errors": public_message}
        body, status = error_response(
            code="ACTION_NOT_ALLOWED",
            message=public_message,
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
        public_message = public_message_for("AUTHENTICATION_REQUIRED", 401)
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
        public_message = public_message_for("AUTHENTICATION_REQUIRED", 401)
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
        public_message = public_message_for("ACTION_NOT_ALLOWED", 403)
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

        422 con `field_errors` como único canal de error por campo (FR-01 §4.2).
        """
        raw_errors = exc.errors(include_input=False)
        field_errors = field_errors_from_pydantic(raw_errors)
        public_message = public_message_for("VALIDATION_ERROR", 422)
        body, status = error_response(
            code="VALIDATION_ERROR",
            message=public_message,
            details={"non_field_errors": public_message},
            status=422,
            field_errors=field_errors,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(NinjaValidationError)
    def on_ninja_validation_error(request: HttpRequest, exc: NinjaValidationError):
        """
        Maneja errores de validación en tiempo de ejecución inyectados por el router Ninja.
        """
        field_errors = field_errors_from_pydantic(exc.errors)
        public_message = public_message_for("VALIDATION_ERROR", 422)
        body, status = error_response(
            code="VALIDATION_ERROR",
            message=public_message,
            details={"non_field_errors": public_message},
            status=422,
            field_errors=field_errors,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(HttpError)
    def on_http_error(request: HttpRequest, exc: HttpError):
        """Maneja errores explícitos del tipo HttpError o sus subclases.

        El mensaje público sale SIEMPRE del catálogo. Cuando el código no está
        catalogado, el mensaje es genérico según el status y el texto original
        de la excepción queda únicamente en los logs.
        """
        code = getattr(exc, "code", "HTTP_ERROR")
        status = exc.status_code
        catalogued = code in PUBLIC_ERROR_MESSAGES

        if catalogued:
            public_message = public_message_for(code, status)
            details = {"non_field_errors": public_message}
            field_errors = []
            if isinstance(exc.message, dict):
                details, field_errors = _split_details(exc.message)
            elif isinstance(exc.message, list):
                field_errors = field_errors_from_pydantic(exc.message)
        else:
            logger.warning(
                "HttpError no catalogado (code=%s status=%s) en %s %s: %s",
                code,
                status,
                request.method,
                request.path,
                exc.message,
            )
            public_message = public_message_for(code, status)
            details = {"non_field_errors": public_message}
            field_errors = _safe_field_errors_from_mapping(exc.message)

        body, status = error_response(
            code=code,
            message=public_message,
            details=details,
            status=status,
            field_errors=field_errors,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(DjangoValidationError)
    def on_django_validation_error(request: HttpRequest, exc: DjangoValidationError):
        """Maneja errores de validación internos de Django (ej: unique_together).

        422 con `field_errors`. El texto original de Django puede interpolar
        el valor que falló, así que la prosa pública se elige por el CÓDIGO del
        error y el valor nunca se expone.
        """
        field_errors = field_errors_from_django(exc)
        public_message = public_message_for("VALIDATION_ERROR", 422)
        details = {"non_field_errors": public_message}
        if not field_errors:
            message_dict = getattr(exc, "message_dict", None)
            if message_dict:
                details, field_errors = _split_details(message_dict)
        body, status = error_response(
            code="VALIDATION_ERROR",
            message=public_message,
            details=details,
            status=422,
            field_errors=field_errors,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(ValueError)
    def on_value_error(request: HttpRequest, exc: ValueError):
        """Maneja un `ValueError` no tipificado.

        `ValueError` NO es un mecanismo de control de flujo
        (`contract/django-app-architecture-contract.md` §10), así que su texto
        crudo NUNCA se expone: se traduce a la categoría "Validation" (422)
        con el mensaje del catálogo y el detalle técnico queda en el log.
        """
        logger.warning(
            "ValueError no tipificado en %s %s: %s",
            request.method,
            request.path,
            exc,
        )
        public_message = public_message_for("VALIDATION_ERROR", 422)
        body, status = error_response(
            code="VALIDATION_ERROR",
            message=public_message,
            details={"non_field_errors": public_message},
            status=422,
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
        public_message = public_message_for("CONFLICT", 409)
        details = {"non_field_errors": public_message}
        body, status = error_response(
            code="CONFLICT",
            message=public_message,
            details=details,
            status=409,
        )
        return api.create_response(request, body, status=status)

    @api.exception_handler(Exception)
    def on_unhandled_exception(request: HttpRequest, exc: Exception):
        """Atrapa-todo para errores inesperados del servidor (500).

        El detalle técnico (traza, mensaje crudo) se queda en el log. La
        respuesta es un mensaje genérico del catálogo (`INTERNAL_ERROR`).
        """
        logger.exception("Unhandled exception: %s", exc)
        public_message = public_message_for("INTERNAL_ERROR", 500)
        body, status = error_response(
            code="INTERNAL_ERROR",
            message=public_message,
            status=500,
        )
        return api.create_response(request, body, status=status)


__all__ = [
    "ADMIN_REQUIRED",
    "ACTION_NOT_ALLOWED",
    "AUTHENTICATION_REQUIRED",
    "GENERIC_PUBLIC_MESSAGES",
    "PUBLIC_ERROR_MESSAGES",
    "AdminRequiredError",
    "BusinessError",
    "ConflictError",
    "CipNotFoundError",
    "ForbiddenError",
    "MediaArchivoHuerfanoError",
    "MediaDimensionesInvalidasError",
    "MediaTamanoExcedidoError",
    "MediaTokenDuplicadoError",
    "MediaTokenNoResueltoError",
    "MediaTipoNoPermitidoError",
    "MediaValidationError",
    "NotFoundError",
    "UnprocessableEntityError",
    "field_errors_from_django",
    "field_errors_from_pydantic",
    "public_message_for",
    "register_exception_handlers",
]
