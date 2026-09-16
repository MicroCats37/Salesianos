# Contrato Arquitectónico: Intención del Patrón DRY en Schemas (Wrappers/Composición)

## Propósito
Este documento define las reglas y la intención arquitectónica para la creación y gestión de schemas en la capa de presentación (API) del backend. El objetivo es mantener el código limpio, reutilizable y escalable.

## El Anti-Patrón: "Schema Inflation"
Históricamente, al desarrollar nuevos endpoints (crear, actualizar, listar, detallar), se tiende a crear un schema masivo e independiente para cada caso de uso. Este anti-patrón, conocido como **Schema Inflation**, genera:
- Duplicación masiva de código.
- Dificultad para mantener la consistencia (un cambio en una entidad obliga a actualizar decenas de schemas).
- Lógica de validación dispersa y repetida.

## La Solución: Composición sobre Herencia
Para erradicar la inflación de schemas, adoptamos el principio de **"Composition over Inheritance"** (Composición sobre Herencia). Construiremos nuestros schemas como si fueran piezas de Lego, ensamblando bloques reutilizables según las necesidades de cada endpoint.

## Estructura de los Bloques Conceptuales
Todo schema final que se exponga o reciba en la API debe componerse utilizando los siguientes 3 bloques conceptuales (Wrappers):

### a) Bloque General
Contiene la información compartida a través de todos o casi todos los endpoints de una entidad (ej. datos básicos que siempre se envían o devuelven). Se define **una sola vez** y actúa como la base de la composición.

### b) Bloque Específico/Lógica
Es la única parte que varía según el caso de uso de negocio (ej. campos requeridos solo al crear, o propiedades específicas de una transición de estado). Define la variabilidad y el comportamiento específico del endpoint.

### c) Bloque Identidad
Contiene exclusivamente los identificadores únicos, números autogenerados (como números de expediente o tickets), timestamps de creación/actualización y UUIDs de auditoría. Este bloque se acopla generalmente en las respuestas (responses) o en actualizaciones (updates).

## Regla Estricta para Futuros Módulos
Todos los desarrollos de nuevos módulos, incluyendo pero no limitándose a **expedientes**, **solicitudes** y **asignaciones**, **DEBEN** adherirse estrictamente a este patrón de composición.

Queda prohibida la creación de schemas monolíticos independientes por endpoint. La capa de presentación debe mantenerse limpia y mantenible componiendo estos tres bloques fundamentales.