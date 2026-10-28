"""
Payload factories of the administracion module.

Pure Python functions that return `dict` payloads — NOT fixtures, no DB and no
pytest dependency (`contract/TEST_ARCHITECTURE_CONTRACT.md` §4).

The administrative area is READ-ONLY: it declares NO request body, so the
factories here build the QUERY payloads and the test helpers, not bodies.

- `make_auth_header(user)` — the Authorization header of an actor.
- `make_list_query(...)` — the canonical query string of a list endpoint.
- `make_forbidden_keys()` — the keys that must NEVER travel in a response.
- `make_forbidden_keys_de_cuentas()` — the same, for the accounts surface.
"""
from ninja_jwt.tokens import AccessToken


def make_auth_header(user) -> dict:
    """Return the Authorization header of an authenticated user."""
    token = AccessToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def make_list_query(
    *,
    page: int | None = None,
    page_size: int | None = None,
    q: str | None = None,
    ordering: str | None = None,
    **filtros,
) -> dict:
    """Return the query payload of a list endpoint.

    Only the values that are not None travel: an absent filter is not sent,
    so the default rules of the server apply.
    """
    payload: dict = {}
    for clave, valor in {
        "page": page,
        "page_size": page_size,
        "q": q,
        "ordering": ordering,
        **filtros,
    }.items():
        if valor is not None:
            payload[clave] = valor
    return payload


def make_forbidden_keys() -> tuple:
    """Return the keys that must NEVER travel in an administrative response.

    They are the credentials, the payment internals and the live QR:
    `password`, `password_hash`, `token`, `codigo_qr`, `metadata`,
    `token_sesion`, `transaction_id`, `response_message`, `is_superuser`.
    """
    return (
        "password",
        "password_hash",
        "token",
        "codigo_qr",
        "metadata",
        "token_sesion",
        "transaction_id",
        "response_message",
        "is_superuser",
    )


def make_forbidden_keys_de_cuentas() -> tuple:
    """Return the keys that must NEVER travel in the ACCOUNTS response.

    Same as `make_forbidden_keys` minus `is_superuser`: the tier of an
    account IS published (A13/A14) so an account administrator can see who
    holds the break-glass tier. The credential NEVER travels.
    """
    return tuple(
        clave for clave in make_forbidden_keys() if clave != "is_superuser"
    )
