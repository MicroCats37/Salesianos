"""
RegistroOrchestrator — fachada asíncrona ligera para controladores de registro.

Solo delega a RegistroFlujo. Sin lógica de negocio aquí.
"""
from injector import inject

from modules.usuarios.domain.services.flujos.registro_flujo import RegistroFlujo
from modules.usuarios.domain.schemas.registro_result_schemas import RegistroTokenResult


class RegistroOrchestrator:
    """
    Fachada asíncrona ligera — delega toda la lógica a RegistroFlujo.

    Inyecta RegistroFlujo vía __init__.
    """

    @inject
    def __init__(self, flujo: RegistroFlujo):
        self.flujo = flujo

    async def registrar(
        self,
        email: str,
        password: str,
        tipo_documento: str,
        numero_documento: str,
        nombres: str,
        apellidos: str,
        genero: str,
        aceptacion_ip: str | None,
        aceptacion_user_agent: str | None,
        telefono: str | None = None,
        whatsapp: str | None = None,
        contacto_emergencia_nombre: str | None = None,
        contacto_emergencia_telefono: str | None = None,
    ) -> RegistroTokenResult:
        """
        Registro de usuario — delega a RegistroFlujo._proceso_registro.
        """
        return await self.flujo._proceso_registro(
            email=email,
            password=password,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            nombres=nombres,
            apellidos=apellidos,
            genero=genero,
            aceptacion_ip=aceptacion_ip,
            aceptacion_user_agent=aceptacion_user_agent,
            telefono=telefono,
            whatsapp=whatsapp,
            contacto_emergencia_nombre=contacto_emergencia_nombre,
            contacto_emergencia_telefono=contacto_emergencia_telefono,
        )