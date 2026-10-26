"""
Participation business rules — the discipline/gender compatibility matrix.

This module is the ONLY owner of the matrix. The read-only audit command, the
core write service, the model ``clean()`` safety net and the Django Admin
guards all call :func:`es_genero_compatible_con_modalidad`; nobody keeps a
private copy, because a duplicated matrix lets the audit and the enforcement
drift apart silently.

The rule
--------
A persona may hold an ACTIVE participation only in a discipline whose
``modalidad`` accepts the persisted ``Persona.genero``:

    M/M, M/X, F/F, F/X  -> compatible
    M/F, F/M            -> incompatible
    anything else       -> incompatible (fail closed)

The values mirror ``ModalidadChoices`` (``domain/constants.py``) and
``GeneroChoices`` (``modules/usuarios/domain/constants.py``). They are spelled
out literally instead of imported so this module stays free of Django
imports and therefore trivially testable.
"""

# Modalidades accepted for each gender.
#
# `X` (mixto) accepts any gender; `M` (masculino) accepts only `M` and `F`
# (femenino) accepts only `F`.
COMPATIBILIDADES_POR_GENERO = {
    "M": frozenset({"M", "X"}),
    "F": frozenset({"F", "X"}),
}


def es_genero_compatible_con_modalidad(genero, modalidad) -> bool:
    """Return True when a persona of ``genero`` may play in ``modalidad``.

    Fails closed: any pair outside the allow-list — including an unknown or
    missing gender, an unknown or missing modality, or a value of the wrong
    type — is incompatible. A rule that cannot prove compatibility denies it.
    """
    try:
        modalidades_aceptadas = COMPATIBILIDADES_POR_GENERO.get(genero)
    except TypeError:  # unhashable gender (e.g. a list) — fail closed
        return False

    if modalidades_aceptadas is None:
        return False

    try:
        return modalidad in modalidades_aceptadas
    except TypeError:  # unhashable modalidad — fail closed
        return False
