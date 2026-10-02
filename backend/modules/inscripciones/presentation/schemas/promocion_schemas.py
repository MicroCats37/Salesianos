"""HTTP schemas for Promocion catalog."""

from ninja import Schema


class PromocionOut(Schema):
    """Promocion response schema."""

    id: str
    anio: int
    colegio: str
    nombre: str
    activa: bool
