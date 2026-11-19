"""
Vocabulario cerrado del módulo de identidad.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1, §2 y §3.

Cada `TextChoices` es una lista cerrada: un valor fuera del vocabulario es un
error de validación, nunca un dato que se pueda inventar.
"""

from django.db import models


class TipoDocumentoChoices(models.TextChoices):
    """Tipos de documento de identidad reconocidos (`FR-03` §1.1)."""

    DNI = "DNI", "DNI"
    CE = "CE", "Carnet de Extranjería"
    PAS = "PAS", "Pasaporte"


class GeneroChoices(models.TextChoices):
    """Géneros reconocidos."""

    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"


class GrupoFuncionalChoices(models.TextChoices):
    """Los DOS grupos funcionales de negocio (`FR-03` §1.2, `DEC-02`).

    `Normal` accede a sus propias operaciones. `Administrador` administra las
    operaciones previstas. `is_superuser` NO es un rol de negocio: es el nivel
    técnico de soporte (`DEC-02`).

    Prohibido crear un tercer grupo por defecto (`FR-03` §1.2); la política de
    los operadores de validación sigue abierta (`GOV-01-OPEN-04`).
    """

    NORMAL = "Normal", "Normal"
    ADMINISTRADOR = "Administrador", "Administrador"


class OrigenResolucionChoices(models.TextChoices):
    """Origen del resultado del resolver (`FR-03` §3.1).

    El origen es OBLIGATORIO y explícito: el resolver nunca devuelve una
    `Persona` ambigua.
    """

    LOCAL = "LOCAL", "Registro local"
    EXTERNO = "EXTERNO", "Fuente externa (sin persistir)"
    NO_ENCONTRADO = "NO_ENCONTRADO", "El documento no existe en la fuente"
    FUENTE_NO_DISPONIBLE = "FUENTE_NO_DISPONIBLE", "La fuente externa falló"


class EstadoConsultaDocumentoChoices(models.TextChoices):
    """Estados distinguibles de la consulta a la fuente externa (`FR-03` §3.3).

    Son CUATRO estados de fallo distintos, no uno:

    - `NO_ENCONTRADO` — el documento no existe (no reintentable).
    - `DATOS_INCOMPLETOS` — la fuente respondió sin datos utilizables.
    - `TIMEOUT` — se agotó el tiempo de espera (reintentable).
    - `FUENTE_NO_DISPONIBLE` — la fuente falló (reintentable).

    `ENCONTRADO` es el único estado exitoso.
    """

    ENCONTRADO = "ENCONTRADO", "Documento encontrado"
    NO_ENCONTRADO = "NO_ENCONTRADO", "Documento no encontrado"
    DATOS_INCOMPLETOS = "DATOS_INCOMPLETOS", "Datos incompletos"
    TIMEOUT = "TIMEOUT", "Tiempo de espera agotado"
    FUENTE_NO_DISPONIBLE = "FUENTE_NO_DISPONIBLE", "Fuente no disponible"


class OrigenDatosChoices(models.TextChoices):
    """Procedencia de los datos de una `Persona` (`FR-03` §3.2 regla 5).

    Se conserva el origen y la fecha de los datos recuperados para el control
    de calidad de la fuente externa.
    """

    LOCAL = "LOCAL", "Registro local"
    EXTERNO = "EXTERNO", "Fuente externa"


class TitularidadChoices(models.TextChoices):
    """Las cuatro titularidades congeladas (`FR-03` §2).

    Los VALORES son los nombres congelados; cada módulo dueño implementa la
    comprobación sobre SU recurso usando la interfaz de este módulo.
    """

    RESPONSABLE = "TITULARIDAD_RESPONSABLE", "Responsable de la inscripción"
    COMPRADOR = "TITULARIDAD_COMPRADOR", "Comprador de la compra"
    BENEFICIARIO = "TITULARIDAD_BENEFICIARIO", "Beneficiario del pase"
    ADMIN = "TITULARIDAD_ADMIN", "Administración del evento"


__all__ = [
    "EstadoConsultaDocumentoChoices",
    "GeneroChoices",
    "GrupoFuncionalChoices",
    "OrigenDatosChoices",
    "OrigenResolucionChoices",
    "TitularidadChoices",
    "TipoDocumentoChoices",
]
