"""Módulo `competencias` — competencias, rondas, encuentros y agenda.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

El módulo es el DUEÑO de la operación deportiva de una edición:

- la **elegibilidad** de un equipo para competir (`RN-K01`) se resuelve
  POR PUERTO contra `modules.salesianos_fest` (que es su dueño) — este módulo
  no reimplementa ninguna regla de inscripción;
- la **categoría** (franja etaria) es parte de la IDENTIDAD de una
  competencia: (edición, disciplina, categoría, nombre) son CUATRO partes, y
  la elegibilidad la compara con la del equipo;
- las **rondas**, los **encuentros** y la **agenda** son los hechos propios;
- el **resultado**, el **avance** y la **corrección** son operaciones
  versionadas, auditadas y con vista previa que NUNCA escribe.

El módulo NO toca el pool de inscripción, ni el comercio, ni los pases: los
consume por su interfaz congelada.
"""
