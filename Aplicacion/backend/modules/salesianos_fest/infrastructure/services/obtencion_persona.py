"""Adaptador de la OBTENCIÓN de la identidad de un comprador invitado.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Traduce la intención del dominio de pases a las primitivas del módulo DUEÑO
del padrón (`modules.usuarios`). El adaptador NO decide: sólo traduce.

- **Registra** una identidad civil cuando el documento no existe en el
  padrón.
- **NO crea una cuenta**: la `Persona` existe sin `Usuario`
  (`FR-03` §1.1 y §1.2). La compra invitada (`FL-06` paso 2) no obliga a
  crear un `Usuario`, y este adaptador no toca `usuarios.Usuario`.
- **No duplica**: la unicidad `(tipo_documento, numero_documento)` es
  autoritativa en la base de datos de `usuarios`. Dos compras simultáneas
  con el mismo documento no crean dos identidades: la segunda recibe la
  fila que ganó la carrera.
"""

from django.db import IntegrityError, transaction

from modules.salesianos_fest.domain.ports import IObtensionPersonaService


class ObtencionPersonaAdapter(IObtensionPersonaService):
    """Puente con el padrón de identidades de `modules.usuarios`.

    `usuarios` es el dueño del padrón (`FREEZE-ID-1.0.0`, `FR-03` §3). Este
    adaptador consulta y, si hace falta, REGISTRA la identidad civil del
    comprador invitado.
    """

    def __init__(self, persona_selector=None, persona_core=None):
        from modules.usuarios.domain.selectors import PersonaSelector
        from modules.usuarios.domain.services.core.persona_core_service import (
            PersonaCoreService,
        )

        self.persona_selector = persona_selector or PersonaSelector()
        self.persona_core = persona_core or PersonaCoreService()

    def obtener_o_registrar(
        self,
        *,
        tipo_documento: str,
        numero_documento: str,
        nombres: str,
        apellidos: str = "",
        genero: str = "",
    ):
        """La `Persona` del documento, registrándola si no existía.

        Si el documento YA existe, devuelve ESA `Persona` y NO reescribe sus
        datos: los nombres, los apellidos y el género declarados sólo se usan
        cuando la identidad se REGISTRA (`FR-03` §1.1 — la identidad que ya
        existe no se reescribe).

        Args:
            tipo_documento: tipo de documento (DNI, CE, PAS…).
            numero_documento: número de documento.
            nombres: nombres declarados en el checkout.
            apellidos: apellidos declarados en el checkout.
            genero: género declarado (opcional). Lo exige la ELEGIBILIDAD de
                una disciplina que no es mixta.

        Returns:
            La `Persona` del padrón.

        Raises:
            IntegrityError: la base de datos rechazó el registro por una
                razón que no es una carrera (documento duplicado con datos
                distintos). El flujo lo traduce a un error de dominio.
        """
        from modules.usuarios.domain.schemas import PersonaCreateData

        existente = self.persona_selector.obtener_por_documento(
            tipo_documento,
            numero_documento,
        )
        if existente is not None:
            return existente

        try:
            # La escritura va en su PROPIA transacción: si la `UniqueConstraint`
            # la rechaza, el intento queda DESHECHO y la relectura de la fila
            # ganadora puede ejecutarse sobre una conexión sana.
            with transaction.atomic():
                return self.persona_core.crear(
                    PersonaCreateData(
                        tipo_documento=tipo_documento,
                        numero_documento=numero_documento,
                        nombres=nombres,
                        apellidos=apellidos or "",
                        genero=genero or "",
                    )
                )
        except IntegrityError:
            # Carrera perdida: otra compra con el mismo documento registró la
            # identidad primero. La fila que ganó es la buena.
            ganador = self.persona_selector.obtener_por_documento(
                tipo_documento,
                numero_documento,
            )
            if ganador is None:
                raise
            return ganador


__all__ = ["ObtencionPersonaAdapter"]
