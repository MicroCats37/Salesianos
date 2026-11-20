"""
`RegistroCoreService` — operaciones de escritura del ALTA DE UNA CUENTA.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.2 · `DEC-02`.

Es SYNC y NO abre `transaction.atomic()`: la transacción y el reintento
controlado viven en el flujo
(`contract/django-app-architecture-contract.md` §4.3 y §4.4).

**El nombre de usuario es DERIVADO del documento**, no lo elige el cliente:
la cuenta nace del documento y su `username` lo refleja
(`{tipo}_{documento}` en minúsculas). El `RegexValidator` del modelo
(`^[a-z0-9._-]+$`) obliga a la forma minúscula: un pasaporte en mayúsculas
produciría un nombre de usuario inválido si no se normaliza aquí.

Este servicio NO decide el conflicto de negocio: sólo consulta y escribe. El
flujo traduce los hechos a excepciones de dominio con código estable.
"""

import logging

from modules.usuarios.domain.models import Usuario

logger = logging.getLogger(__name__)


class RegistroCoreService:
    """Consultas y escrituras del alta de una cuenta."""

    # ── Consultas ───────────────────────────────────────────────────────────

    def email_en_uso(self, email: str) -> bool:
        """Si el correo ya está vinculado a una cuenta.

        La comparación NO distingue mayúsculas porque el usuario lo escribe
        como lo escribe: es la misma clave que usa el inicio de sesión
        (`FR-03` §1.2).
        """
        correo = str(email or "").strip()
        if not correo:
            return False
        return (
            Usuario.objects.filter(email__iexact=correo)
            .exclude(email__isnull=True)
            .exclude(email="")
            .exists()
        )

    # ── Escrituras ──────────────────────────────────────────────────────────

    @staticmethod
    def username_para(tipo_documento: str, numero_documento: str) -> str:
        """El nombre de usuario derivado del documento.

        Es `{tipo}_{documento}` en MINÚSCULAS: el `RegexValidator` del modelo
        sólo admite minúsculas, números, punto, guion y guion bajo, y el
        documento se persiste normalizado en mayúsculas.
        """
        return f"{str(tipo_documento or '').lower()}_{str(numero_documento or '').lower()}"

    def crear_cuenta(
        self,
        *,
        username: str,
        email: str,
        password: str,
        persona_fk,
    ) -> Usuario:
        """Crea la cuenta y la vincula a su persona.

        La contraseña se guarda con el hash de Django: este servicio no
        reimplementa el hashing (`FR-03` §1.2).
        """
        return Usuario.objects.create_user(
            username=username,
            email=email,
            password=password,
            persona_fk=persona_fk,
        )


__all__ = ["RegistroCoreService"]
