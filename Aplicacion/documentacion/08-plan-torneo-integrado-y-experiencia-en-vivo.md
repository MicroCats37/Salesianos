# Plan del torneo integrado y la experiencia en vivo

Este documento define el trabajo que convertirá el prototipo actual del torneo en una superficie integrada con los datos reales de Salesianos FEST. El resultado debe permitir administrar partidos con claridad y publicar resultados en una experiencia visual coherente con la landing.

## Decisión principal

El torneo no tendrá una segunda fuente de equipos. `salesianos_fest.Equipo` será la fuente de verdad y `EquipoTorneo` representará únicamente la participación de ese equipo dentro de una competencia y un grupo.

La pantalla administrativa actual de fondo azul completo queda descartada. Administración y público compartirán la identidad visual de la landing, pero conservarán jerarquías diferentes porque resuelven tareas distintas.

## Estado verificado

| Tema | Estado actual | Problema |
|---|---|---|
| Disciplinas oficiales | Fútbol 7 Masculino, Fútbol 7 Femenino, Vóley Mixto y Básquet Masculino | La cantidad oficial es cuatro; algunos paquetes permiten únicamente tres |
| Disciplina temporal | El seed del torneo creó `Fulbito` | Introdujo una quinta disciplina artificial |
| Competencia pública | El endpoint busca `Fulbito Interpromociones` por nombre | La UI queda amarrada a una competencia y no muestra el contexto deportivo |
| Equipos del fixture | 33 filas independientes con nombres como `2012` o `2023` | No están vinculadas a `fest_equipo` |
| Panel administrativo | Bloque oscuro de gran tamaño dentro del shell | No sigue la jerarquía ni la densidad del área administrativa |
| Escrituras | Funciones API directas y refetch manual | No usan los hooks genéricos ni declaran la invalidación |
| Realtime | WebSocket invalida el snapshot público | El panel administrativo no comunica bien la actualización ni su progreso |

## Alcance funcional

### Catálogo y disciplinas

El catálogo oficial conservará sus cuatro modalidades. No se eliminará una disciplina oficial para forzar un total de tres.

Los paquetes seguirán mostrando solo las disciplinas que permiten. Por ejemplo, `Trío + Fiesta Box` permite tres: Fútbol 7 Masculino, Vóley Mixto y Básquet Masculino.

La superficie del torneo no tendrá una cantidad hardcodeada. Mostrará las competencias existentes para la edición publicada y siempre identificará disciplina, modalidad, categoría y fecha.

La disciplina temporal `Fulbito` se retirará. El fixture de referencia se asociará con `Fútbol 7 Masculino`, que es la modalidad oficial equivalente disponible en el catálogo.

### Equipos reales

`EquipoTorneo` conservará el código externo del fixture, el grupo y la competencia. Añadirá una FK hacia `salesianos_fest.Equipo`.

La base de datos impedirá que el mismo equipo se incorpore dos veces a la misma competencia mediante una restricción única `(competencia, equipo)`.

El nombre, la promoción, la disciplina, la categoría, el estado y los participantes se leerán desde el equipo real y su inscripción. No se copiarán esos datos en `EquipoTorneo`.

El código del fixture continuará existiendo para distinguir entradas como `2011A` y `2011B` sin convertir ese código en el nombre canónico del equipo.

### Seed de referencia

El comando `seed_torneo_referencia` será idempotente y solo se permitirá en desarrollo.

El comando realizará estas acciones:

1. Resolver la edición publicada y el catálogo oficial existente.
2. Resolver Fútbol 7 Masculino, la categoría Interpromociones y el paquete individual correspondiente.
3. Crear o reutilizar una persona responsable de desarrollo por entrada del fixture.
4. Crear o reutilizar una inscripción real por promoción y variante.
5. Crear o reutilizar un `Equipo` real para cada una de las 33 entradas.
6. Vincular cada participación del torneo con ese equipo.
7. Conservar resultados existentes al ejecutarse nuevamente.
8. Retirar `Fulbito` cuando ya no tenga referencias.

Los datos creados por este comando son demostrativos. No sustituyen inscripciones reales de producción ni inventan participantes de plantilla.

## Backend

### Modelo

| Modelo | Cambio |
|---|---|
| `EquipoTorneo` | Reemplazar `promocion` y `nombre` duplicados por FK a `Equipo` |
| `PromocionTorneo` | Eliminar; la promoción se obtiene desde `equipo.inscripcion.promocion` |
| `GrupoTorneo` | Mantener competencia, código y revisión optimista |
| `PartidoTorneo` | Mantener horario, cancha, marcador, estado, reloj y ganador |

La FK podrá ser temporalmente nula para que la migración sea desplegable sobre datos existentes. El seed dejará todas las participaciones de referencia asignadas. Una participación sin asignar se mostrará como pendiente y no fingirá un equipo.

### Lecturas

El snapshot público dejará de buscar una competencia por un nombre fijo. Resolverá la edición publicada y expondrá contexto suficiente para que la UI pueda reconocer la competencia seleccionada.

Cada competencia expuesta incluirá como mínimo:

| Campo | Uso |
|---|---|
| `id` | Identidad estable de la competencia |
| `name` | Nombre público |
| `discipline` | Disciplina y modalidad visibles |
| `category` | Categoría visible |
| `date` | Jornada de la competencia |
| `ready` | Indica si el fixture está publicado |

El snapshot seleccionado incluirá grupos, equipos, tabla, partidos y llaves. Los nombres de equipo se resolverán desde `fest_equipo`.

### Escrituras

Los controllers conservarán las rutas HTTP actuales durante este cambio, pero delegarán la lógica de aplicación en servicios del módulo.

Las escrituras mantendrán estas garantías:

- Transacción atómica por operación.
- Revisión optimista del grupo.
- Validación de que ambos equipos pertenecen al grupo o competencia.
- Ganador declarado explícitamente cuando el marcador no lo determina.
- Publicación WebSocket mediante `transaction.on_commit`.
- Mensaje público fijo de éxito en el envelope.

## Frontend administrativo

### Dirección visual

La ruta se integrará al shell claro de administración. La marca aparecerá en una franja institucional compacta, no en una página oscura insertada dentro del dashboard.

La jerarquía será:

1. Contexto de competencia: disciplina, categoría, fecha y estado de conexión.
2. Selector de competencia cuando exista más de una.
3. Resumen operativo compacto: en juego, pendientes y finalizados.
4. Selector horizontal de grupos o rondas.
5. Un editor de partido enfocado, con navegación al partido anterior y siguiente.
6. Acciones del reloj y cierre claramente separadas de la edición del fixture.

La pantalla no renderizará seis formularios completos uno debajo del otro. El operador seleccionará el partido que necesita atender y conservará el contexto del grupo.

### Formularios y transporte

Los formularios de grupo y llave usarán `GenericForm` en modo manual con Zod como fuente de validación.

Los hooks del feature envolverán `useApiUpdate` y `useApiCreate`. Cada mutación declarará la clave pública que invalida y validará el envelope de respuesta con Zod.

Los componentes no llamarán a `apiSend`, no construirán URLs y no interpretarán errores crudos.

### Feedback

Cada operación tendrá cuatro señales visibles:

- Botón bloqueado con texto de progreso.
- Toast con el mensaje del backend.
- Región `aria-live` dentro del editor.
- Refresco inmediato del marcador, tabla y estado del partido.

Los conflictos de revisión mostrarán una acción para recargar los datos antes de volver a guardar.

## Frontend público

### Dirección visual

La vista pública seguirá la identidad de la landing: gradiente institucional, tipografía Plus Jakarta Sans, superficies claras y oscuras alternadas, radios amplios, acento dorado y cian de marca, y fotografía del evento solo donde aporte contexto.

La página no será una copia del panel administrativo. Tendrá una narrativa de espectador:

1. Hero compacto con competencia, disciplina y jornada.
2. Partido en vivo o próximo partido como momento principal.
3. Navegación entre resumen, grupos, programación y llaves.
4. Tabla del grupo con lectura priorizada en móvil.
5. Programación filtrable por estado y grupo.
6. Llaves finales con desplazamiento contenido, sin desbordar la página.

Todos los colores se consumirán desde tokens semánticos de `globals.css`. No se aceptarán literales hexadecimales, RGB/HSL ni utilidades de paleta dentro de los componentes modificados.

### Realtime

HTTP seguirá siendo la fuente de verdad. El WebSocket solo notificará que el snapshot cambió.

Al recibir `encuentro.actualizado`, React Query invalidará la misma clave que usan la portada, la ruta pública y el panel. La UI anunciará la actualización sin mover el foco ni reemplazar de forma brusca el contenido que el usuario está usando.

## Responsive y accesibilidad

La aceptación se realizará en 360, 390, 768, 1024 y 1440 píxeles.

Se verificará:

- Ausencia de scroll horizontal de página.
- Controles táctiles de al menos 44 píxeles.
- Foco visible y orden de teclado coherente.
- Labels programáticos para equipos, marcadores, cancha, hora y duración.
- Errores y éxitos anunciados mediante regiones vivas.
- Tablas y llaves con scroll interno cuando sea necesario.
- Respeto de `prefers-reduced-motion`.

## Orden de implementación

1. Normalizar el modelo y generar la migración mediante `makemigrations`.
2. Actualizar y ejecutar el seed idempotente.
3. Adaptar snapshot, servicios y mensajes de los endpoints.
4. Crear schemas y hooks de mutación del frontend.
5. Reconstruir el panel administrativo con `GenericForm` y tokens.
6. Reconstruir la vista pública con la dirección visual de la landing.
7. Verificar WebSocket e invalidación compartida.
8. Ejecutar pruebas backend, pruebas frontend, TypeScript, Biome y build.

## Criterios de aceptación

- [ ] No existe una tabla paralela de promociones del torneo.
- [ ] Cada participación del fixture apunta a un equipo real o declara explícitamente que está pendiente.
- [ ] El seed puede ejecutarse dos veces sin duplicar personas, inscripciones, equipos ni partidos.
- [ ] `Fulbito` deja de aparecer como quinta disciplina artificial.
- [ ] La disciplina y categoría son visibles antes de elegir un grupo o partido.
- [ ] Administración no usa el bloque oscuro completo de la captura rechazada.
- [ ] Público y administración comparten tokens e identidad, pero tienen jerarquías adecuadas a sus usuarios.
- [ ] Los formularios usan `GenericForm` y las escrituras usan hooks genéricos.
- [ ] Guardar o controlar un partido produce progreso, éxito/error y actualización visible.
- [ ] El WebSocket actualiza marcador, tabla y llaves sin polling.
- [ ] No quedan colores literales en las vistas modificadas.
- [ ] Las pruebas, typecheck, lint focal y build terminan correctamente.

## Fuera de alcance

- Inventar fixtures deportivos que no estén respaldados por la referencia entregada.
- Crear plantillas o participantes ficticios para los equipos sembrados.
- Cambiar reglas de elegibilidad, cupos, paquetes o pagos.
- Reemplazar los modelos canónicos de competencias ya existentes fuera del alcance necesario para integrar la fase de grupos de referencia.
