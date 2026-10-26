"""
Domain selectors — read-only queries for Usuario and Persona.

`modules.usuarios` owns the identity data (`Persona`) and the accounts
(`Usuario`). The operational administration surface lists both, so it needs a
query surface owned HERE — the admin module consumes these selectors and never
imports another module's `presentation/` layer
(`contract/api-wrapper-presenter-contract.md` §1).

There is a single implementation of each query, so NO port/ABC is declared:
the concrete selectors live in the domain layer, exactly like the selectors of
`modules.salesianos_fest` (`contract/django-app-architecture-contract.md`
§4.12 — "no crear un repository/port solo para envolver el ORM").

Read-only by construction: no method in this module writes.
"""
from django.db.models import Q, QuerySet

from modules.usuarios.domain.models import Persona, Usuario


class UsuarioSelector:
    """Read-only queries for Usuario."""

    def obtener_por_id(self, usuario_id: str) -> Usuario | None:
        """Return the account with the given id, or None."""
        return (
            Usuario.objects
            .select_related("persona_fk")
            .filter(id=usuario_id)
            .first()
        )

    def obtener_por_username(self, username: str) -> Usuario | None:
        """Return the account with the given username, or None."""
        return (
            Usuario.objects
            .select_related("persona_fk")
            .filter(username=username)
            .first()
        )

    def listar(
        self,
        *,
        activo: bool | None = None,
        es_admin: bool | None = None,
        q: str | None = None,
    ) -> QuerySet[Usuario]:
        """Return the accounts matching the given filters.

        Args:
            activo: filter by `is_active` when not None.
            es_admin: filter by the project admin rule
                (`is_staff OR is_superuser`) when not None.
            q: free text over username, email, legacy dni and the civil
                identity of the linked persona.

        Returns:
            An unevaluated QuerySet: the caller decides how to paginate it.
        """
        qs = Usuario.objects.select_related("persona_fk")

        if activo is not None:
            qs = qs.filter(is_active=activo)

        if es_admin is not None:
            # The SAME rule that `core.permissions.RequireAdmin` applies.
            admin_filter = Q(is_staff=True) | Q(is_superuser=True)
            qs = qs.filter(admin_filter if es_admin else ~admin_filter)

        if q:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(email__icontains=q)
                | Q(dni__icontains=q)
                | Q(persona_fk__nombres__icontains=q)
                | Q(persona_fk__apellidos__icontains=q)
                | Q(persona_fk__numero_documento__icontains=q)
            )

        return qs.order_by("-created_at")


class PersonaSelector:
    """Read-only queries for Persona."""

    def obtener_por_id(self, persona_id: str) -> Persona | None:
        """Return the person with the given id, or None."""
        return Persona.objects.filter(id=persona_id).first()

    def obtener_por_documento(
        self,
        tipo_documento: str,
        numero_documento: str,
    ) -> Persona | None:
        """Return the person with the given civil identity, or None."""
        return (
            Persona.objects
            .filter(
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
            )
            .first()
        )

    def listar(self, *, q: str | None = None) -> QuerySet[Persona]:
        """Return the people matching the given filters.

        Args:
            q: free text over first name, last name and document number.

        Returns:
            An unevaluated QuerySet: the caller decides how to paginate it.
        """
        qs = Persona.objects.all()

        if q:
            qs = qs.filter(
                Q(nombres__icontains=q)
                | Q(apellidos__icontains=q)
                | Q(numero_documento__icontains=q)
            )

        return qs.order_by("nombres", "apellidos")


__all__ = ["UsuarioSelector", "PersonaSelector"]
