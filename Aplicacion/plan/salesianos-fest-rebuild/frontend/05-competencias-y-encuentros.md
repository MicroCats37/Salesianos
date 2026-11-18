# Frontend 05 — Administración de competencias, programación y encuentros

**Base actual:** existe backend de `Competencia`, `CompetenciaEquipo`, `Ronda`, `Encuentro` con 29 rutas administrativas documentadas (17 + 12), incluida propagación y corrección del cuadro. Fuente: `03b-paginas-administrativas-y-operativas.md`, §4.9–4.12. **Diseñar UX objetivo sin perder reglas verificadas**.

## 1. Escenario del administrador

1. Crear/seleccionar competencia para la edición y disciplina/categoría (si está habilitado).
2. Incorporar equipos elegibles y definir su orden cuando se requiera.
3. Crear rondas y encuentros, incluso encuentros con participantes por definir.
4. Programar fecha/hora evitando solapamientos.
5. Registrar resultado y ganador confirmado.
6. Previsualizar y confirmar avance; corregir errores con impacto visible.
7. Mostrar cuadro al público solo como lectura de la competición publicada.

## 2. Rutas y responsabilidades (propuestas)

| Página | Objetivo | Acciones |
|---|---|---|
| `/administracion/competencias` | Lista de torneos de la edición | Buscar/filtrar, crear si está autorizado, abrir detalle/agenda/cuadro |
| `/administracion/competencias/[id]` | Central operativa de competencia | Editar datos, equipos elegibles, rondas, encuentros, indicadores |
| `/administracion/competencias/[id]/cuadro` | Visualizar progresión en bracket | Abrir encuentro, registrar resultado, preview/confirmar avance y correcciones |
| `/administracion/competencias/agenda` | Gestión temporal transversal | Ver encuentros del día, filtros, abrir encuentro |
| `/competencias/[id]` | Cuadro público (propuesta) | Visualización de rondas/resultado sin mutaciones |

## 3. Componente central: detalle de encuentro

Propuesta: **panel lateral o diálogo accesible reutilizable** desde lista, agenda y cuadro; misma información y acciones, sin múltiples editores divergentes.

**Cabecera:** competencia + ronda + encuentro + estado legible. **Secciones:** participantes, fecha/hora, marcador, ganador, secuencia de avance, historial de correcciones. **Acciones según estado:** programar, marcar bye, registrar resultado, previsualizar avance, confirmar avance, corregir, enlazar/desenlazar.

Cada acción informa **consecuencia concreta**, no solo `ok=true`. Ejemplos: “Ganador registrado: Equipo Norte”; “La corrección afecta a 2 encuentros posteriores”; “Este equipo ya juega en ese horario”.

## 4. Tabla de acciones y condiciones

| Acción | Precondición | Confirmación de UX | Salida observable |
|---|---|---|---|
| Agregar equipo a competencia | Edición/disciplina/categoría elegibles | Mostrar razón si no elegible | Equipo aparece en lista |
| Crear ronda | Etiqueta y orden válidos | Guardado | Ronda visible en cuadro |
| Crear encuentro | Ronda y orden válidos | Guardado | Encuentro (vacío/parcial permitido) |
| Programar | Hora válida, no solapamiento | Confirmar cambios | Agenda y cuadro actualizados |
| Registrar resultado | Ganador válido | Guardar resultado | Encuentro finalizado |
| Bye manual | Exactamente un equipo | Mostrar efecto antes de guardar | Encuentro resuelto como bye |
| Avance a siguiente fase | Destino disponible | **Preview + confirmar** | Ganador aparece en slot destino |
| Corregir resultado | Permisos y versión actual | **Preview de impacto + motivo** | Historial y cuadro coherentes |

## 5. Estados y feedback

- **Por definir:** no existen aún participantes o enfrentamiento.
- **Programado:** fecha/hora definida; mostrar hora local de la edición.
- **En curso / finalizado:** usar los estados de negocio reales que defina el backend, no introducir enumeraciones por presentación.
- **Conflicto de versión:** otro administrador actualizó el encuentro; recargar datos y reintentar **sin aplicar silenciosamente** cambios obsoletos.
- **Sin rondas/equipos:** CTA específico para añadirlos, no pantalla vacía genérica.
- **Error de avance:** destacar encuentro/slot bloqueante.

## 6. Backend como autoridad

Mantener los invariantes documentados: un equipo no debe jugar dos veces simultáneamente; los enlaces avanzan a rondas posteriores sin ciclos; ganador autoritativo; corrección descendente no puede ser silenciosa; versionado/`expected_version` u otra protección equivalente definida por arquitectura.

**No:** calcular automáticamente ganadores desde el marcador en React, forzar avances desde la UI o inventar byes sin confirmar.

## 7. Puntos para el agente UX

- La programación y edición no deben estar ocultas solo en el bracket: abrir mismo detalle del encuentro desde agenda, cuadro o competencia.
- En móvil, bracket horizontal desplazable con indicadores de ronda y acceso a tarjeta; no depender de rejilla desktop.
- Distinguir acciones destructivas, sensibles y de simple lectura; todas con nombres claros.
- Filtros coherentes entre lista de competencias y selector de cuadro.
- Mostrar vista previa de resultado y efecto de corrección antes de confirmar.

## 8. Casos de aceptación

`QA-K01` Equipo no elegible no puede agregarse; mensaje explica motivo. `QA-K02` Programación solapada se rechaza y no cambia agenda. `QA-K03` Resultado fija ganador una sola vez y se ve en cuadro. `QA-K04` Advance preview no escribe; confirm sí. `QA-K05` Corrección que afecta descendientes exige motivo/confirmación; si hay conflicto de versión, informa y recupera.
