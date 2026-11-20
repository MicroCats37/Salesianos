"""Puertos (interfaces) del módulo `salesianos_fest`.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

El módulo cruza al DOMINIO en DOS puntos, y ambos cruzan por PUERTO:

1. **El alcance de edición** — lo resuelve `modules.eventos`, que es su
   dueño (`FREEZE-ED-1.0.0`, `FR-02` §2.2). El puerto reproduce el orden
   congelado sin duplicarlo.
2. **La titularidad** — la resuelve `modules.usuarios`, que es su dueño
   (`FREEZE-ID-1.0.0`, `FR-03` §2.1). El módulo dueño del recurso comprueba
   sobre SU recurso: ser `Administrador` no sustituye la titularidad.

3. **La resolución de una identidad** — la resuelve `modules.usuarios`, que
   es su dueño (`FREEZE-ID-1.0.0`, `FR-03` §3.2). `FL-05` paso 2 permite
   "agregar persona existente **o** resolverla por documento": este módulo
   CONSULTA el padrón a través del puerto y NO crea identidades.

4. **La OBTENCIÓN de una identidad** — la resuelve `modules.usuarios`, que
   es su dueño. La compra de pases puede ser INVITADA (`FL-06` paso 2), y un
   invitado es una identidad civil **sin cuenta**: este puerto registra la
   `Persona` que falte y **nunca** un `Usuario`.

La compra, en cambio, NO cruza por puerto: `commerce` es la INFRAESTRUCTURA
comercial compartida y su interfaz está CONGELADA (`FREEZE-CM-1.0.0`,
`RN-C01`). El flujo consume `CompraFlujo` directamente, que es el puerto de
hecho que `D-FND-04-06` describe ("los dominios crean su compra en proceso").
"""

from abc import ABC, abstractmethod


class IAlcanceEdicionService(ABC):
    """Resuelve la edición de alcance aplicando el orden congelado."""

    @abstractmethod
    def resolver_explicita(self, edicion_id, *, exigir_publicada: bool = False):
        """Nivel 1 del orden congelado: el `edicion_id` explícito.

        Args:
            edicion_id: identificador de la edición pedida.
            exigir_publicada: la edición devuelta debe estar `PUBLICADA`.

        Returns:
            La edición resuelta.

        Raises:
            `EdicionNoEncontradaError`: el identificador no existe.
            `EdicionNoPublicadaError`: existe pero no está `PUBLICADA`.
        """
        ...

    @abstractmethod
    def resolver_actual(
        self,
        *,
        ediciones_activas_actor=None,
        exigir_publicada: bool = False,
        permitir_publicada_por_defecto: bool = True,
    ):
        """Niveles 2, 3 y 4 del orden congelado.

        Se usa cuando la operación NO lleva la edición en el path: el
        catálogo público la resuelve por el orden congelado, nunca por
        defecto informal.

        Args:
            ediciones_activas_actor: candidatas del actor (nivel 2).
            exigir_publicada: la edición devuelta debe estar `PUBLICADA`.
            permitir_publicada_por_defecto: si es `False`, el nivel 3 no se
                aplica y la resolución termina en el nivel 4.

        Returns:
            La edición resuelta.
        """
        ...


class ITitularidadService(ABC):
    """Primitivas de titularidad sobre el recurso del módulo."""

    @abstractmethod
    def persona_id_del_actor(self, usuario) -> str | None:
        """El identificador de la persona vinculada al actor, o `None`.

        Éste es el ÚNICO origen admisible del sujeto de una titularidad: la
        cuenta autenticada. Un documento resuelto nunca es el sujeto
        (`FR-03` §3.2 regla 6).
        """
        ...

    @abstractmethod
    def es_responsable(self, persona_id: str | None, responsable_id: str) -> bool:
        """Si la persona es la responsable del recurso indicado."""
        ...


class IResolucionPersonaService(ABC):
    """Resuelve una identidad del padrón por documento.

    Es una consulta de SOLO LECTURA: `FL-05` paso 2 permite agregar al pool
    una persona ya existente o resolverla por documento, pero la CREACIÓN de
    identidades es de `usuarios` (`FR-03` §3.2). Este puerto no crea, no
    confirma y no devuelve credenciales: sólo dice si la identidad existe y
    cuál es su identificador.
    """

    @abstractmethod
    def resolver_por_documento(
        self,
        tipo_documento: str,
        numero_documento: str,
    ):
        """La persona con ese documento, o `None` si no existe en el padrón.

        Args:
            tipo_documento: tipo de documento (DNI, CE, Pasaporte…).
            numero_documento: número de documento.

        Returns:
            La `Persona` encontrada o `None`.
        """
        ...

    @abstractmethod
    def resolver_por_id(self, persona_id):
        """La persona con ese identificador, o `None` si no existe.

        Returns:
            La `Persona` encontrada o `None`.
        """
        ...


class IObtensionPersonaService(ABC):
    """Obtiene —o registra— la identidad civil de un comprador INVITADO.

    Es el puerto que permite la compra SIN CUENTA (`FL-06` paso 2):

    - Si el documento ya existe en el padrón, devuelve esa `Persona`.
    - Si NO existe, la REGISTRA como identidad civil **sin cuenta**: crea una
      `Persona`, y **nunca** un `Usuario` (`FR-03` §1.1 — "la `Persona`
      EXISTE SIN CUENTA"; `FR-03` §1.2 — "No crear cuenta automática").

    `usuarios` es el DUEÑO del padrón: este puerto no escribe identidades por
    su cuenta, traduce la intención del dominio a las primitivas de
    `usuarios`.

    La NO duplicación es autoritativa en la base de datos de `usuarios`
    (`unique_tipo_numero_documento`): dos compras simultáneas con el mismo
    documento no crean dos identidades.
    """

    @abstractmethod
    def obtener_o_registrar(
        self,
        *,
        tipo_documento: str,
        numero_documento: str,
        nombres: str,
        apellidos: str = "",
    ):
        """La `Persona` de ese documento, registrándola si no existía.

        Args:
            tipo_documento: tipo de documento (DNI, CE, PAS…).
            numero_documento: número de documento.
            nombres: nombres declarados en el checkout.
            apellidos: apellidos declarados en el checkout (opcionales).

        Returns:
            La `Persona` del padrón.

        Raises:
            Exception: si el documento ya existe con datos distintos o si la
                base de datos rechaza el registro. El flujo lo traduce a un
                error de dominio.
        """
        ...


__all__ = [
    "IAlcanceEdicionService",
    "IObtensionPersonaService",
    "IResolucionPersonaService",
    "ITitularidadService",
]
