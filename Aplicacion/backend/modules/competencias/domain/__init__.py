"""Dominio del módulo `competencias`.

Contiene la lógica de negocio: modelos, DTOs, results, selectores, puertos y
servicios. No depende de la capa HTTP
(`contract/django-app-architecture-contract.md` §3).

El módulo es el DUEÑO de la operación deportiva de una edición:

- la **elegibilidad** de un equipo (`RN-K01`) se resuelve POR PUERTO contra
  `modules.salesianos_fest`, que es su dueño: aquí no se reimplementa ninguna
  regla de inscripción;
- las **rondas**, los **encuentros** y la **agenda** son hechos propios;
- el **resultado**, el **avance** y la **corrección** son operaciones
  versionadas, auditadas y con vista previa que NUNCA escribe.
"""

__all__: list[str] = []
