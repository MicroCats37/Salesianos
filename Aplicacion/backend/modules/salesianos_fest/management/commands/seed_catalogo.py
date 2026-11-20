"""`seed_catalogo` — siembra de ARRANQUE del catálogo de inscripción.

Change: `backend-integration-closeout` · Batch: B
Change: `restore-registration-promotion-catalog-flow` (2026-11-20)
Contract: `contract/django-app-architecture-contract.md` §3 (carpetas del
módulo) y §6 (modelos planos y anémicos)

QUÉ DEJA

    Evento → Edición PUBLICADA → Promociones (GLOBALES)
                                   → Categorías (de la edición)
                                   → Disciplinas → Paquetes
                                   → Precios → Vínculos → Beneficios

El catálogo es el OFICIAL del FEST: las cuatro categorías con su rango de
promociones, las cuatro disciplinas y los ocho paquetes con sus precios
unitarios y sus mínimos comerciales.

GARANTÍAS (todas verificadas por los tests de este módulo)

1. **IDEMPOTENTE**: reejecutarlo NO duplica ni una fila. Cada entidad se
   crea con `get_or_create` sobre su clave natural y lo que ya existe se
   REUTILIZA tal cual.
2. **NUNCA borra ni resetea**: no hay `--clear`, no hay `delete()` y no hay
   `update_or_create`. Los vínculos disciplina↔paquete que el operador haya
   añadido se conservan. Las categorías obsoletas que el legacy borraba
   (Sub-14, Sub-16, Sub-18, Sub-20) NO se borran: se conservan y el
   operador puede retirarlas con `estado = INACTIVA`.
3. **NUNCA pisa la configuración del operador**: si un paquete ya tiene
   precios, el seed NO crea un precio nuevo NI modifica el existente.
4. **NUNCA corre en el arranque del servidor**: es un comando de gestión
   explícito. `docker/entrypoint.sh` no lo invoca.
5. **NUNCA exige que el frontend elija la edición**: la edición sembrada
   queda `PUBLICADA` y con el módulo `inscripciones` habilitado, que es lo
   que exige el orden congelado de alcance (`FR-02` §2.2) cuando el cliente
   no manda `edicion_id`.
6. **SIEMPRE siembra promociones y categorías**: son el catálogo de la
   COHORTE y de la BANDA competitiva. Sin ellos la inscripción no puede
   derivar la categoría con la que compite su equipo (`D-CAT-05`), así que
   su ausencia no es una decisión de alcance: es un catálogo incompleto.

PATRÓN QUE SIGUE

Reproduce el patrón de `modules/eventos/management/commands/
crear_edicion_inicial.py`: la identidad del evento y de la edición se pide
por parámetro (nunca por constante de settings), el alta se hace por el
CAMINO DE ESCRITURA del módulo `eventos` (flujo → core service → selector)
y el comando es idempotente.

USO

    python manage.py seed_catalogo
    python manage.py seed_catalogo --edicion-slug 2027 --edicion-nombre "Salesianos FEST 2027" --anio 2027
    python manage.py seed_catalogo --dry-run

`--dry-run` ejecuta la siembra completa dentro de una transacción que se
deshace al final: informa de lo que haría sin dejar una sola fila escrita.
"""

from datetime import date
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.eventos.domain.constants import MODULOS_HABILITABLES, EstadoEdicion
from modules.eventos.domain.models import Evento
from modules.eventos.domain.schemas.edicion_schemas import EdicionCreateData, EdicionUpdateData
from modules.eventos.domain.selectors.edicion_selector import EdicionSelector
from modules.eventos.domain.selectors.evento_selector import EventoSelector
from modules.eventos.domain.services.core.edicion_core_service import EdicionCoreService
from modules.eventos.domain.services.core.edicion_scope_service import EdicionScopeService
from modules.eventos.domain.services.flujos.edicion_flujo import EdicionFlujo
from modules.eventos.domain.services.orchestrators.edicion_orchestrator import (
    EdicionOrchestrator,
)
from modules.salesianos_fest.domain.constants import (
    EstadoCategoria,
    EstadoDisciplina,
    EstadoPaquete,
    EstadoPromocion,
    ModalidadDisciplina,
    ModoDisciplinas,
    TipoBeneficioPaquete,
    TipoPaquete,
)
from modules.salesianos_fest.domain.models import (
    Categoria,
    Disciplina,
    Paquete,
    PaqueteBeneficio,
    PaqueteDisciplina,
    PaquetePrecio,
    Promocion,
)

#: Módulos lógicos que este seed SIEMPRE habilita. La edición de desarrollo
#: debe exponer toda funcionalidad implementada y declarada por el dominio.
#: Los módulos que el operador pase con `--modulo` se suman.
MODULOS_IMPLICITOS = MODULOS_HABILITABLES

#: Moneda del catálogo sembrado (ISO-4217).
MONEDA_CATALOGO = "PEN"

#: Inicio de vigencia de los precios sembrados.
#:
#: Es una fecha FIJA y anterior a cualquier edición: el precio sembrado tiene
#: que ser el vigente HOY y también mañana. Calcularla con `date.today()`
#: haría que cada ejecución del comando crease una fila de precio NUEVA (la
#: clave natural es `paquete + vigente_desde`) y rompería la idempotencia.
VIGENCIA_INICIAL_PRECIO = date(2020, 1, 1)

#: Fin de la etapa de PREVENTA del catálogo oficial.
#:
#: Es una fecha FIJA por la misma razón que `VIGENCIA_INICIAL_PRECIO`: el
#: precio REGULAR empieza aquí y la pareja de precios sembrada tiene que ser
#: la MISMA en cada ejecución.
FIN_PREVENTA_PRECIO = date(2026, 10, 31)

#: Año de cohorte más antiguo del catálogo oficial de promociones.
ANIO_MINIMO_PROMOCION = 1970

#: Año de cohorte más reciente del catálogo oficial de promociones.
ANIO_MAXIMO_PROMOCION = 2025

#: Las CATEGORÍAS OFICIALES del FEST.
#:
#: Cada una declara el RANGO de promociones (años de cohorte) que contiene.
#: El rango es el mecanismo de derivación cohorte → banda competitiva: no
#: hace falta un JOIN con `Promocion` para saber a qué categoría pertenece
#: una inscripción (`D-CAT-05`).
CATEGORIAS_OFICIALES = (
    {
        "nombre": "Junior",
        "promocion_desde": 2012,
        "promocion_hasta": 2025,
    },
    {
        "nombre": "Senior",
        "promocion_desde": 1998,
        "promocion_hasta": 2011,
    },
    {
        "nombre": "Master",
        "promocion_desde": 1985,
        "promocion_hasta": 1997,
    },
    {
        "nombre": "Super Master",
        "promocion_desde": 1970,
        "promocion_hasta": 1984,
    },
)

#: Disciplinas OFICIALES del FEST.
DISCIPLINAS_OFICIALES = (
    {
        "nombre": "Fútbol 7 Masculino",
        "slug": "futbol-7-masculino",
        "modalidad": ModalidadDisciplina.MASCULINO,
        "minimo_por_equipo": 7,
        "maximo_por_equipo": 10,
    },
    {
        "nombre": "Fútbol 7 Femenino",
        "slug": "futbol-7-femenino",
        "modalidad": ModalidadDisciplina.FEMENINO,
        "minimo_por_equipo": 7,
        "maximo_por_equipo": 10,
    },
    {
        "nombre": "Vóley Mixto",
        "slug": "voley-mixto",
        "modalidad": ModalidadDisciplina.MIXTO,
        "minimo_por_equipo": 6,
        "maximo_por_equipo": 8,
    },
    {
        "nombre": "Básquet Masculino",
        "slug": "basquet-masculino",
        "modalidad": ModalidadDisciplina.MASCULINO,
        "minimo_por_equipo": 5,
        "maximo_por_equipo": 10,
    },
)

#: Paquetes OFICIALES del FEST.
#:
#: - `minimo_compra_inicial` es el MÍNIMO COMERCIAL de participantes. El
#:   comprador declara la cantidad; el servidor la contrasta contra este
#:   mínimo (`D-CAT-01`). No hay un máximo global de participantes.
#: - `cupos_incluidos` (DEPRECADO) se siembra con el mismo valor: es el
#:   hecho DECLARADO de la oferta, no la cantidad que se compra.
#: - `precio_preventa` y `precio_regular` son PRECIOS UNITARIOS: el precio
#:   de UNA persona. El total lo deriva el servidor como
#:   `cantidad × precio_unitario` (`RN-C02`).
#: - `beneficios` es una tupla de `(codigo, nombre, tipo, cantidad)`. El
#:   beneficio se DECLARA aquí (`RN-P01`): su concesión es otro hecho.
PAQUETES_OFICIALES = (
    {
        "nombre": "Reencuentro + Fiesta",
        "slug": "reencuentro-fiesta",
        "descripcion": "Reencuentro con acceso a fiesta de cierre.",
        "tipo": TipoPaquete.PACK,
        "modo_disciplinas": ModoDisciplinas.ELEGIBLE,
        "cantidad_disciplinas": 1,
        "minimo_compra_inicial": 10,
        "precio_preventa": Decimal("40.00"),
        "precio_regular": Decimal("50.00"),
        "disciplinas": ("futbol-7-femenino", "voley-mixto", "basquet-masculino"),
        "beneficios": (
            (
                "FIESTA",
                "Acceso a la fiesta de cierre",
                TipoBeneficioPaquete.FIJO_INICIAL,
                1,
            ),
        ),
    },
    {
        "nombre": "Pichanga + Fiesta",
        "slug": "pichanga-fiesta",
        "descripcion": "Pichanga competitiva con acceso a fiesta de cierre.",
        "tipo": TipoPaquete.PACK,
        "modo_disciplinas": ModoDisciplinas.FIJO,
        "cantidad_disciplinas": 1,
        "minimo_compra_inicial": 10,
        "precio_preventa": Decimal("45.00"),
        "precio_regular": Decimal("55.00"),
        "disciplinas": ("futbol-7-masculino",),
        "beneficios": (
            (
                "FIESTA",
                "Acceso a la fiesta de cierre",
                TipoBeneficioPaquete.FIJO_INICIAL,
                1,
            ),
        ),
    },
    {
        "nombre": "Dúo + Fiesta Box",
        "slug": "duo-fiesta-box",
        "descripcion": "Pack para dos personas con fiesta y box de bebidas.",
        "tipo": TipoPaquete.PACK,
        "modo_disciplinas": ModoDisciplinas.ELEGIBLE,
        "cantidad_disciplinas": 2,
        "minimo_compra_inicial": 15,
        "precio_preventa": Decimal("60.00"),
        "precio_regular": Decimal("70.00"),
        "disciplinas": ("voley-mixto", "basquet-masculino"),
        "beneficios": (
            (
                "FIESTA",
                "Acceso a la fiesta de cierre",
                TipoBeneficioPaquete.POR_CUPO,
                1,
            ),
            (
                "BOX_BEBIDAS",
                "Box de bebidas de la inscripción",
                TipoBeneficioPaquete.FIJO_INICIAL,
                1,
            ),
            (
                "CERVEZA",
                "Cerveza de la inscripción",
                TipoBeneficioPaquete.FIJO_INICIAL,
                6,
            ),
        ),
    },
    {
        "nombre": "Trío + Fiesta Box",
        "slug": "trio-fiesta-box",
        "descripcion": "Pack para tres personas con fiesta y box de bebidas.",
        "tipo": TipoPaquete.PACK,
        "modo_disciplinas": ModoDisciplinas.ELEGIBLE,
        "cantidad_disciplinas": 3,
        "minimo_compra_inicial": 20,
        "precio_preventa": Decimal("60.00"),
        "precio_regular": Decimal("70.00"),
        "disciplinas": ("futbol-7-masculino", "voley-mixto", "basquet-masculino"),
        "beneficios": (
            (
                "FIESTA",
                "Acceso a la fiesta de cierre",
                TipoBeneficioPaquete.POR_CUPO,
                1,
            ),
            (
                "BOX_BEBIDAS",
                "Box de bebidas de la inscripción",
                TipoBeneficioPaquete.FIJO_INICIAL,
                1,
            ),
            (
                "CERVEZA",
                "Cerveza de la inscripción",
                TipoBeneficioPaquete.FIJO_INICIAL,
                6,
            ),
        ),
    },
    {
        "nombre": "Fútbol 7 Masculino",
        "slug": "futbol-7-masculino",
        "descripcion": "Torneo de fútbol 7 masculino.",
        "tipo": TipoPaquete.DISCIPLINA,
        "modo_disciplinas": ModoDisciplinas.FIJO,
        "cantidad_disciplinas": 1,
        "minimo_compra_inicial": 7,
        "precio_preventa": Decimal("40.00"),
        "precio_regular": Decimal("50.00"),
        "disciplinas": ("futbol-7-masculino",),
        "beneficios": (),
    },
    {
        "nombre": "Fútbol 7 Femenino",
        "slug": "futbol-7-femenino",
        "descripcion": "Torneo de fútbol 7 femenino.",
        "tipo": TipoPaquete.DISCIPLINA,
        "modo_disciplinas": ModoDisciplinas.FIJO,
        "cantidad_disciplinas": 1,
        "minimo_compra_inicial": 7,
        "precio_preventa": Decimal("40.00"),
        "precio_regular": Decimal("50.00"),
        "disciplinas": ("futbol-7-femenino",),
        "beneficios": (),
    },
    {
        "nombre": "Vóley Mixto",
        "slug": "voley-mixto",
        "descripcion": "Torneo de vóley mixto.",
        "tipo": TipoPaquete.DISCIPLINA,
        "modo_disciplinas": ModoDisciplinas.FIJO,
        "cantidad_disciplinas": 1,
        "minimo_compra_inicial": 6,
        "precio_preventa": Decimal("40.00"),
        "precio_regular": Decimal("50.00"),
        "disciplinas": ("voley-mixto",),
        "beneficios": (),
    },
    {
        "nombre": "Básquet Masculino",
        "slug": "basquet-masculino",
        "descripcion": "Torneo de básquet masculino.",
        "tipo": TipoPaquete.DISCIPLINA,
        "modo_disciplinas": ModoDisciplinas.FIJO,
        "cantidad_disciplinas": 1,
        "minimo_compra_inicial": 5,
        "precio_preventa": Decimal("40.00"),
        "precio_regular": Decimal("50.00"),
        "disciplinas": ("basquet-masculino",),
        "beneficios": (),
    },
)


def _nombre_de_promocion(anio: int) -> str:
    """El nombre descriptivo de la promoción de un año de cohorte.

    Es el nombre de la banda competitiva que contiene ese año: la promoción
    lo ANUNCIA, la categoría la DECIDE (`D-CAT-01`).
    """
    for categoria in CATEGORIAS_OFICIALES:
        if categoria["promocion_desde"] <= anio <= categoria["promocion_hasta"]:
            return categoria["nombre"]
    return "Promoción"


class Command(BaseCommand):
    """Siembra (o reutiliza) el catálogo de inscripción de UNA edición."""

    help = (
        "Siembra de arranque del catálogo de inscripción (evento, edición "
        "publicada, promociones, categorías, disciplinas, paquetes, precios, "
        "vínculos y beneficios). Es idempotente: reejecutarlo no duplica ni "
        "borra nada."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--evento-nombre",
            default="Salesianos FEST",
            help="Nombre del evento raíz. Se ignora si el evento ya existe.",
        )
        parser.add_argument(
            "--evento-slug",
            default="salesianos-fest",
            help="Slug del evento raíz: es su clave natural de reutilización.",
        )
        parser.add_argument(
            "--edicion-nombre",
            default="Salesianos FEST 2026",
            help="Nombre de la edición. Se ignora si la edición ya existe.",
        )
        parser.add_argument(
            "--edicion-slug",
            default="2026",
            help="Slug de la edición: es su clave natural de reutilización.",
        )
        parser.add_argument(
            "--anio",
            type=int,
            default=2026,
            help="Año de la edición. Se ignora si la edición ya existe.",
        )
        parser.add_argument(
            "--modulo",
            action="append",
            default=[],
            choices=list(MODULOS_HABILITABLES),
            help=(
                "Módulo lógico adicional a habilitar en la edición "
                "(repetible). Todos los módulos declarados por el dominio "
                "se habilitan siempre."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Informa de lo que haría sin dejar ninguna fila escrita.",
        )

    # ── Orquestación ────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        """Siembra el catálogo dentro de UNA transacción."""
        if options["dry_run"]:
            with transaction.atomic():
                self._sembrar(options)
                transaction.set_rollback(True)
            self.stdout.write(
                self.style.WARNING("Dry-run: no se escribió ninguna fila.")
            )
            return

        with transaction.atomic():
            self._sembrar(options)

    def _sembrar(self, options):
        """Ejecuta la siembra completa. No decide: delega en los pasos."""
        modulos = self._modulos(options)
        evento = self._asegurar_evento(options)
        edicion = self._asegurar_edicion(evento, options, modulos)
        self._asegurar_modulos(edicion, modulos)
        self._asegurar_publicada(edicion)
        self._sembrar_promociones()
        self._sembrar_categorias(edicion)
        disciplinas = self._sembrar_disciplinas(edicion)
        self._sembrar_paquetes(edicion, disciplinas)
        self._resumen(edicion)

    # ── Evento y edición ────────────────────────────────────────────────────

    def _asegurar_evento(self, options) -> Evento:
        """Reutiliza el evento raíz o lo crea. Nunca lo modifica."""
        selector = EventoSelector()
        evento = selector.obtener_por_slug(options["evento_slug"])
        if evento is not None:
            self._info(f"Evento reutilizado: {evento.nombre} ({evento.slug}).")
            return evento

        evento = Evento.objects.create(
            nombre=options["evento_nombre"],
            slug=options["evento_slug"],
        )
        self._info(f"Evento creado: {evento.nombre} ({evento.slug}).")
        return evento

    def _asegurar_edicion(self, evento, options, modulos):
        """Reutiliza la edición o la crea por el camino de escritura."""
        selector = EdicionSelector()
        edicion = selector.obtener_por_slug(evento.id, options["edicion_slug"])
        if edicion is not None:
            self._info(f"Edición reutilizada: {edicion.nombre} ({edicion.slug}).")
            return edicion

        data = EdicionCreateData(
            evento_id=evento.id,
            nombre=options["edicion_nombre"],
            slug=options["edicion_slug"],
            anio=options["anio"],
            modulos_habilitados=modulos,
        )
        orchestrator = self._orchestrator_eventos()
        edicion = async_to_sync(orchestrator.crear_edicion)(data)
        self._info(f"Edición creada: {edicion.nombre} ({edicion.slug}).")
        return edicion

    def _asegurar_publicada(self, edicion) -> None:
        """Publica la edición objetivo si está en borrador.

        La edición `PUBLICADA` es la que resuelve el alcance cuando el
        cliente NO manda `edicion_id` (`FR-02` §2.2, nivel 3). El seed
        publica la suya, pero NO reabre una edición cerrada ni compite con
        otra edición publicada: en ese caso falla con un mensaje explícito,
        porque un catálogo ambiguo no es un catálogo servible.
        """
        if edicion.estado == EstadoEdicion.PUBLICADA:
            self._info("Edición ya publicada.")
            return

        if edicion.estado == EstadoEdicion.CERRADA:
            raise CommandError(
                f"La edición «{edicion.nombre}» está CERRADA y el seed no "
                "reabre una edición cerrada. Indica otra edición con "
                "--edicion-slug."
            )

        selector = EdicionSelector()
        publicadas = selector.listar_publicadas()
        if publicadas.exists():
            otra = publicadas.first()
            raise CommandError(
                f"Ya existe una edición PUBLICADA («{otra.nombre}», "
                f"slug «{otra.slug}»). El alcance se resuelve por la edición "
                "publicada ÚNICA: siembra esa edición con "
                f"--edicion-slug {otra.slug} o ciérrala antes de continuar."
            )

        orchestrator = self._orchestrator_eventos()
        async_to_sync(orchestrator.publicar_edicion)(edicion.id)
        # El flujo publica OTRA instancia de la edición: se recarga esta para
        # no trabajar después con un estado obsoleto.
        edicion.refresh_from_db()
        self._info("Edición publicada.")

    def _asegurar_modulos(self, edicion, modulos) -> None:
        """Habilita los módulos pedidos. Sólo AGREGA: nunca deshabilita."""
        actuales = list(edicion.modulos_habilitados or [])
        faltantes = [modulo for modulo in modulos if modulo not in actuales]
        if not faltantes:
            self._info(f"Módulos habilitados: {', '.join(actuales) or '(ninguno)'}.")
            return

        nuevos = actuales + faltantes
        # Se recarga antes de escribir: `actualizar()` guarda la instancia
        # completa y un `estado` obsoleto en memoria pisaría el estado real.
        edicion.refresh_from_db()
        core_service = EdicionCoreService()
        core_service.actualizar(
            edicion,
            EdicionUpdateData(modulos_habilitados=nuevos),
        )
        self._info(f"Módulos habilitados: {', '.join(nuevos)}.")

    # ── Promociones y categorías ────────────────────────────────────────────

    def _sembrar_promociones(self) -> None:
        """Siembra (o reutiliza) las promociones del catálogo GLOBAL.

        Una promoción por año de cohorte (1970-2025). Son GLOBALES: no
        cuelgan de ninguna edición, así que se siembran una sola vez.
        """
        for anio in range(ANIO_MINIMO_PROMOCION, ANIO_MAXIMO_PROMOCION + 1):
            _, creado = Promocion.objects.get_or_create(
                anio=anio,
                defaults={
                    "nombre": _nombre_de_promocion(anio),
                    "estado": EstadoPromocion.ACTIVA,
                },
            )
            if creado:
                self._info(f"Promoción creada: {anio}.")
        self._info(
            f"Promociones: {Promocion.objects.count()} "
            f"({ANIO_MINIMO_PROMOCION}-{ANIO_MAXIMO_PROMOCION})."
        )

    def _sembrar_categorias(self, edicion) -> None:
        """Siembra (o reutiliza) las categorías OFICIALES de la edición.

        El rango de promociones es la regla de derivación cohorte →
        categoría. Si una categoría ya existe con OTRO rango, se preserva y
        se avisa: el seed no pisa la configuración del operador.
        """
        for datos in CATEGORIAS_OFICIALES:
            categoria, creado = Categoria.objects.get_or_create(
                edicion=edicion,
                nombre=datos["nombre"],
                estado=EstadoCategoria.ACTIVA,
                defaults={
                    "promocion_desde": datos["promocion_desde"],
                    "promocion_hasta": datos["promocion_hasta"],
                },
            )
            if creado:
                self._info(
                    f"Categoría creada: {categoria.nombre} "
                    f"({categoria.promocion_desde}-{categoria.promocion_hasta})."
                )
                continue
            if (
                categoria.promocion_desde != datos["promocion_desde"]
                or categoria.promocion_hasta != datos["promocion_hasta"]
            ):
                self._aviso(
                    f"«{categoria.nombre}» ya existe con un rango distinto "
                    f"({categoria.promocion_desde}-"
                    f"{categoria.promocion_hasta}): se preserva."
                )

    # ── Catálogo ────────────────────────────────────────────────────────────

    def _sembrar_disciplinas(self, edicion) -> dict[str, Disciplina]:
        """Crea (o reutiliza) las disciplinas de la edición."""
        disciplinas = {}
        for datos in DISCIPLINAS_OFICIALES:
            disciplina, creado = Disciplina.objects.get_or_create(
                edicion=edicion,
                slug=datos["slug"],
                defaults={
                    "nombre": datos["nombre"],
                    "estado": EstadoDisciplina.ACTIVA,
                    "modalidad": datos["modalidad"],
                    "minimo_por_equipo": datos["minimo_por_equipo"],
                    "maximo_por_equipo": datos["maximo_por_equipo"],
                },
            )
            disciplinas[datos["slug"]] = disciplina
            self._info(
                f"Disciplina {'creada' if creado else 'reutilizada'}: "
                f"{disciplina.nombre}."
            )
        return disciplinas

    def _sembrar_paquetes(self, edicion, disciplinas) -> None:
        """Crea (o reutiliza) los paquetes con sus precios, beneficios y vínculos."""
        for datos in PAQUETES_OFICIALES:
            paquete, creado = Paquete.objects.get_or_create(
                edicion=edicion,
                slug=datos["slug"],
                defaults={
                    "nombre": datos["nombre"],
                    "descripcion": datos["descripcion"],
                    "estado": EstadoPaquete.VIGENTE,
                    "tipo": datos["tipo"],
                    "modo_disciplinas": datos["modo_disciplinas"],
                    "cantidad_disciplinas": datos["cantidad_disciplinas"],
                    "cupos_incluidos": datos["minimo_compra_inicial"],
                    "minimo_compra_inicial": datos["minimo_compra_inicial"],
                },
            )
            self._info(
                f"Paquete {'creado' if creado else 'reutilizado'}: {paquete.nombre}."
            )
            self._sembrar_precios(paquete, datos)
            self._sembrar_beneficios(paquete, datos)
            self._sembrar_vinculos(paquete, datos, disciplinas)

    def _sembrar_precios(self, paquete, datos) -> None:
        """Siembra los precios sólo si el paquete NO tiene ninguno.

        Un precio configurado por el operador es una decisión comercial: el
        seed la respeta y no la pisa ni la duplica.

        Los precios son UNITARIOS (el precio de UNA persona) y tienen DOS
        etapas, igual que el catálogo oficial: la PREVENTA y la REGULAR. Las
        dos ventanas tienen fechas FIJAS para que la siembra sea idempotente.
        """
        if paquete.precios.exists():
            self._aviso(
                f"«{paquete.nombre}» ya tiene precio configurado: se preserva."
            )
            return

        etapas = (
            ("preventa", datos["precio_preventa"], VIGENCIA_INICIAL_PRECIO, FIN_PREVENTA_PRECIO),
            ("regular", datos["precio_regular"], FIN_PREVENTA_PRECIO, None),
        )
        for nombre, monto, desde, hasta in etapas:
            PaquetePrecio.objects.create(
                paquete=paquete,
                monto=monto,
                moneda=MONEDA_CATALOGO,
                vigente_desde=desde,
                vigente_hasta=hasta,
            )
            self._info(
                f"Precio {nombre} creado: {monto} {MONEDA_CATALOGO} por persona."
            )

    def _sembrar_beneficios(self, paquete, datos) -> None:
        """Declara (o reutiliza) los beneficios OFRECIDOS por el paquete."""
        for codigo, nombre, tipo, cantidad in datos["beneficios"]:
            _, creado = PaqueteBeneficio.objects.get_or_create(
                paquete=paquete,
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "tipo": tipo,
                    "cantidad": cantidad,
                },
            )
            self._info(
                f"Beneficio {'declarado' if creado else 'reutilizado'}: "
                f"{codigo} en «{paquete.nombre}»."
            )

    def _sembrar_vinculos(self, paquete, datos, disciplinas) -> None:
        """Enlaza el paquete con sus disciplinas. Nunca borra vínculos."""
        for slug in datos["disciplinas"]:
            disciplina = disciplinas[slug]
            _, creado = PaqueteDisciplina.objects.get_or_create(
                paquete=paquete,
                disciplina=disciplina,
            )
            if creado:
                self._info(
                    f"Vínculo creado: «{paquete.nombre}» -> {disciplina.nombre}."
                )

    # ── Utilidades ─────────────────────────────────────────────────────────

    def _modulos(self, options) -> list[str]:
        """Los módulos a habilitar: los del catálogo base más los pedidos."""
        modulos = list(MODULOS_IMPLICITOS)
        for modulo in options["modulo"] or []:
            if modulo not in modulos:
                modulos.append(modulo)
        return modulos

    def _orchestrator_eventos(self) -> EdicionOrchestrator:
        """El camino de ESCRITURA de `eventos` (flujo → core → selector)."""
        evento_selector = EventoSelector()
        edicion_selector = EdicionSelector()
        core_service = EdicionCoreService(
            edicion_selector=edicion_selector,
            evento_selector=evento_selector,
        )
        scope_service = EdicionScopeService(selector=edicion_selector)
        flujo = EdicionFlujo(core_service=core_service, scope_service=scope_service)
        return EdicionOrchestrator(scope_service=scope_service, flujo=flujo)

    def _resumen(self, edicion) -> None:
        """Informa del estado final del catálogo sembrado."""
        self._escribir(self.style.SUCCESS("Catálogo de inscripción sembrado."))
        self._escribir(f"  Evento: {edicion.evento.nombre} ({edicion.evento.slug})")
        self._escribir(
            f"  Edición: {edicion.nombre} ({edicion.slug}) [{edicion.estado}]"
        )
        self._escribir(
            f"  Promociones: {Promocion.objects.count()} (catálogo global)"
        )
        self._escribir(
            f"  Categorías: {Categoria.objects.filter(edicion=edicion).count()}"
        )
        self._escribir(
            f"  Disciplinas: {Disciplina.objects.filter(edicion=edicion).count()}"
        )
        self._escribir(f"  Paquetes: {Paquete.objects.filter(edicion=edicion).count()}")
        self._escribir(
            f"  Precios: {PaquetePrecio.objects.filter(paquete__edicion=edicion).count()}"
        )
        self._escribir(
            f"  Vínculos: "
            f"{PaqueteDisciplina.objects.filter(paquete__edicion=edicion).count()}"
        )
        self._escribir(
            f"  Beneficios: "
            f"{PaqueteBeneficio.objects.filter(paquete__edicion=edicion).count()}"
        )

    def _escribir(self, mensaje: str) -> None:
        """Escribe en la salida de la consola sin romperla.

        La consola de Windows usa `cp1252` por defecto: un carácter fuera de
        esa repertoire (una flecha, por ejemplo) haría que el comando
        CRASHEARA al final de su trabajo, con la siembra ya escrita. Si la
        salida no puede representar el mensaje, se degrada a ASCII en lugar
        de abortar.
        """
        try:
            self.stdout.write(mensaje)
        except UnicodeEncodeError:
            self.stdout.write(
                mensaje.encode("ascii", "replace").decode("ascii")
            )

    def _info(self, mensaje: str) -> None:
        """Informa de un paso del seed."""
        self._escribir(mensaje)

    def _aviso(self, mensaje: str) -> None:
        """Informa de un dato que el seed preservó en lugar de escribir."""
        self._escribir(self.style.WARNING(mensaje))


__all__ = ["Command"]
