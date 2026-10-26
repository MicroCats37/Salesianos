# DOCUMENTACIÓN DE LÓGICA Y TABLAS — SALESIANOS FEST

> **Versión:** 1.0
> **Fecha:** 2026-10-18
> **Proyecto:** Salesianos
> **Alcance:** Documentación completa de la lógica de aplicación, tablas de base de datos, flujos end-to-end, APIs, y gaps conocidos.

---

## 1. MAPA EJECUTIVO

### 1.1 Módulos del Proyecto

| Módulo | Responsabilidad |
|--------|---------------|
| `modules/usuarios` | Personas, usuarios, autenticación, búsqueda por documento |
| `modules/eventos` | Entidad Evento (ediciones del FEST) |
| `modules/pagos` | Órdenes de pago genéricas, Izipay, transacciones |
| `modules/salesianos_fest` | Catálogo, inscripciones deportivas, equipos, participaciones, compras, cupos, acreditaciones, control de acceso |

### 1.2 Arquitectura General

```
Frontend (Next.js)
    ↓ API (JWT auth)
Backend Django NinjaExtra
    ├── controllers (async,薄 — delegan a orchestrators)
    ├── orchestrators (薄 — delegan a flujos)
    ├── flujos (async con transaction.atomic)
    ├── services/core (sync, lógica de negocio pura)
    ├── selectors (consultas complejas)
    └── models (Django ORM, anémicos)
```

### 1.3 Fase Actual

| Fase | Alcance | Estado |
|------|---------|--------|
| Fase 2 | Catálogo (disciplinas, promociones, categorías, paquetes) | ✅ Completa |
| Fase 3 | Inscripciones deportivas, equipos, roster, participaciones | ✅ Completa |
| Fase 4 | Compras comerciales, Izipay | ✅ Completa |
| Fase 5 | Asignación de cupos, acreditaciones, QR | ✅ Completa |
| Fase 6 | Consentimientos (bases, aptitud física, imagen) | ✅ Completa |
| Fase 7 | — | — |
| Fase 8 | Release, limpieza de código | ✅ Completa |

---

## 2. CATÁLOGO COMPLETO DE TABLAS

### 2.1 Módulo: `eventos`

#### `eventos` — Evento

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `nombre` | VARCHAR(200) | Nombre de la edición (ej: "Salesianos FEST 2026") |
| `fecha_inicio` | DATE | Inicio del evento |
| `fecha_fin` | DATE | Fin del evento |
| `esta_activo` | BOOLEAN | Si está abierto para inscripciones |
| `fecha_limite_modificacion` | DATE | Fecha límite para modificar roster/equipos |

**Relaciones:**
- 1 Evento → N `paquetes` (PROTECT)
- 1 Evento → N `categorias` (PROTECT)
- 1 Evento → N `inscripciones` (PROTECT)
- 1 Evento → N `acreditaciones_evento` (PROTECT)

**Quién escribe:** Admin / seed `seed_catalogo_fest`
**Quién lee:** Todos los endpoints de catálogo e inscripción

**Verificado:** ✅ Completo

---

### 2.2 Módulo: `usuarios`

#### `usuarios_personas` — Persona

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `numero_documento` | VARCHAR(20) | DNI/CE/PAS — único |
| `tipo_documento` | VARCHAR(10) | Tipo de documento |
| `nombres` | VARCHAR(200) | Nombres completos |
| `apellidos` | VARCHAR(200) | Apellidos completos |
| `email` | VARCHAR(254) | Email (único, nullable) |
| `telefono` | VARCHAR(20) | Teléfono (nullable) |
| `whatsapp` | VARCHAR(20) | WhatsApp (nullable) |
| `genero` | CHAR(1) | M/F |
| `fecha_nacimiento` | DATE | Fecha de nacimiento (nullable) |
| `aseguradora_nombre` | VARCHAR(200) | Nombre aseguradora (nullable) |
| `aseguradora_numero_poliza` | VARCHAR(100) | Número de póliza (nullable) |
| `contacto_emergencia_nombre` | VARCHAR(200) | Contacto de emergencia (nullable) |
| `contacto_emergencia_telefono` | VARCHAR(20) | Teléfono de emergencia (nullable) |

**Relaciones:**
- 1 Persona → N `inscripciones_responsable` (PROTECT)
- 1 Persona → N `inscripciones_delegado` (PROTECT)
- 1 Persona → N `inscripciones_persona` (PROTECT)
- 1 Persona → N `participaciones` (PROTECT)
- 1 Persona → N `acreditaciones_evento` (PROTECT)

**Unicidad:** `(numero_documento)` — unique constraint
**Estado:** No tiene campo de estado explícito
**Quién escribe:** Registro (`registro_flujo`), admin
**Quién lee:** Todos los endpoints de inscripción, búsqueda

**Verificado:** ✅ Completo

#### `usuarios_usuarios` — Usuario (Django User extendido)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `persona_fk` | FK → Persona | Persona vinculada |
| `username` | VARCHAR(150) | Username único |
| `password` | VARCHAR(128) | Hash de contraseña |
| `is_staff` | BOOLEAN | Staff Django |
| `is_superuser` | BOOLEAN | Superusuario |

**Relaciones:**
- 1 Usuario → 1 Persona (PROTECT, 1:1)
- 1 Usuario → N ControlAcceso (`operador`)

**Quién escribe:** Registro, admin
**Quién lee:** `AuthMeController`, `AuthOrchestrator`

**Verificado:** ✅ Completo

---

### 2.3 Módulo: `salesianos_fest`

#### `disciplinas` — Disciplina

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `nombre` | VARCHAR(200) | Nombre completo (ej: "Fútbol 7 Masculino") |
| `sigla` | VARCHAR(10) | Código único (ej: F7M, VOL, BAS) |
| `modalidad` | CHAR(1) | M=Femenino, F=Femenino, X=Mixto |
| `min_jugadores` | INTEGER | Mínimo de jugadores por equipo |
| `max_jugadores` | INTEGER | Máximo de jugadores por equipo |
| `esta_activa` | BOOLEAN | Si está disponible |

**Unicidad:** `(sigla)` — unique constraint
**Relaciones:**
- 1 Disciplina → N `equipos` (PROTECT)
- 1 Disciplina → N `paquete_disciplinas` (PROTECT)
- 1 Disciplina → N `participaciones` (PROTECT)

**Quién escribe:** seed `seed_catalogo_fest`
**Quién lee:** Catálogo, creación de equipos

**Verificado:** ✅ Completo

---

#### `promociones` — Promoción (rango etario)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `anio` | INTEGER | Año base (ej: 2012) — único |
| `nombre` | VARCHAR(100) | Nombre (Junior, Senior, Master, Super Master) |
| `activa` | BOOLEAN | Si está vigente |

**Unicidad:** `(anio)` — unique constraint
**Semántica:** Los rangos etarios van de 1970 a 2025:
- Junior: 2012–2025
- Senior: 1998–2011
- Master: 1985–1997
- Super Master: 1970–1984

**Quién escribe:** seed `seed_catalogo_fest`
**Quién lee:** Catálogo, creación de inscripción

**Verificado:** ✅ Completo

---

#### `categorias` — Categoría competitiva

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `evento_id` | FK → Evento | Evento al que pertenece |
| `nombre` | VARCHAR(100) | Nombre (Junior, Senior, etc.) |
| `promocion_desde` | INTEGER | Año mínimo del rango etario |
| `promocion_hasta` | INTEGER | Año máximo del rango etario |
| `esta_activa` | BOOLEAN | Si está activa |

**Unicidad:** `(evento, nombre)` WHERE `esta_activa=True` — partial unique constraint
**Validación:** `promocion_desde <= promocion_hasta`
**Relaciones:**
- 1 Categoría → 1 Evento (PROTECT)
- 1 Categoría → N `equipos` (PROTECT)

**Quién escribe:** seed `seed_catalogo_fest` (reconcilia categorías obsoletas Sub-* a las 4 oficiales)
**Quién lee:** Catálogo, creación de equipos

**Verificado:** ✅ Completo

---

#### `paquetes` — Paquete comercial

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `evento_id` | FK → Evento | Evento al que pertenece |
| `nombre` | VARCHAR(200) | Nombre del paquete |
| `descripcion` | TEXT | Descripción detallada |
| `tipo` | CHAR(10) | PACK (con beneficios) o DISCIPLINA (individual) |
| `modo_disciplinas` | CHAR(10) | FIJO (predefinidas) o ELEGIBLE (elige el participante) |
| `cantidad_disciplinas` | INTEGER | Cantidad de disciplinas (1, 2 o 3) |
| `minimo_compra_inicial` | INTEGER | Monto mínimo de compra inicial |
| `activo` | BOOLEAN | Si está disponible |

**Unicidad:** `(evento, nombre)` — unique constraint
**Relaciones:**
- 1 Paquete → 1 Evento (PROTECT)
- 1 Paquete → N `inscripciones` (PROTECT)
- 1 Paquete → N `paquete_precios` (PROTECT)
- 1 Paquete → N `paquete_beneficios` (PROTECT)
- 1 Paquete → N `paquete_disciplinas` (PROTECT)

**Paquetes definidos (seed):**
| Nombre | Tipo | Precio Preventa | Precio Regular | Min | Disciplinas |
|--------|------|---------------|---------------|-----|------------|
| Reencuentro + Fiesta | PACK | S/40 | S/50 | 10 | F7F, VOL, BAS |
| Pichanga + Fiesta | PACK | S/45 | S/55 | 10 | F7M |
| Dúo + Fiesta Box | PACK | S/60 | S/70 | 15 | VOL, BAS |
| Trío + Fiesta Box | PACK | S/60 | S/70 | 20 | F7M, VOL, BAS |
| Fútbol 7 Masculino | DISCIPLINA | S/40 | S/50 | 7 | F7M |
| Fútbol 7 Femenino | DISCIPLINA | S/40 | S/50 | 7 | F7F |
| Vóley Mixto | DISCIPLINA | S/40 | S/50 | 6 | VOL |
| Básquet Masculino | DISCIPLINA | S/40 | S/50 | 5 | BAS |

**Quién escribe:** seed `seed_catalogo_fest`
**Quién lee:** Catálogo, creación de inscripción

**Verificado:** ✅ Completo

---

#### `paquete_precios` — Precios por etapa

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `paquete_id` | FK → Paquete | Paquete |
| `etapa` | CHAR(10) | PREVENTA o REGULAR |
| `precio_unitario` | DECIMAL(10,2) | Precio en soles |
| `vigente_desde` | DATE | Fecha inicio de vigencia |
| `vigente_hasta` | DATE | Fecha fin de vigencia (null = sin límite) |
| `activo` | BOOLEAN | Si está vigente |

**Unicidad:** `(paquete, etapa)` WHERE `activo=True` — partial unique constraint
**Relaciones:** 1 Paquete → N PaquetePrecios

**Verificado:** ✅ Completo

---

#### `paquete_beneficios` — Beneficios del paquete

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `paquete_id` | FK → Paquete | Paquete |
| `tipo` | CHAR(20) | FIESTA, BOX o CERVEZA |
| `cantidad` | INTEGER | Cantidad del beneficio |
| `alcance` | CHAR(20) | INDIVIDUAL o GRUPAL |
| `modo_calculo` | CHAR(20) | POR_CUPO o FIJO_INICIAL |

**Unicidad:** `(paquete, tipo)` — unique constraint
**Semántica de modo_calculo:**
- `POR_CUPO`: cada cupo pagado otorga el beneficio individualmente (ej: Dúo + Fiesta — cada persona tiene fiesta)
- `FIJO_INICIAL`: un solo beneficio fijo por inscripción (ej: box de bebidas grupal)

**Verificado:** ✅ Completo

---

#### `paquete_disciplinas` — Disciplinas vinculadas

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `paquete_id` | FK → Paquete | Paquete |
| `disciplina_id` | FK → Disciplina | Disciplina |

**Unicidad:** `(paquete, disciplina)` — unique constraint

**Verificado:** ✅ Completo

---

#### `inscripciones` — Inscripción deportiva

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `evento_id` | FK → Evento | Evento |
| `responsable_id` | FK → Persona | Persona que crea y gestiona |
| `paquete_id` | FK → Paquete | Paquete comercial seleccionado |
| `promocion_id` | FK → Promocion | Promoción principal (calcula categoría) |
| `fusion_promocion_id` | FK → Promocion (nullable) | Promoción secundaria para fusión |
| `delegado_id` | FK → Persona (nullable) | Delegado/responsable del equipo |
| `estado` | CHAR(20) | BORRADOR, RECIBIDA, EN_REVISION, OBSERVADA, VALIDADA, CONFIRMADA, RECHAZADA, CANCELADA |
| `observacion` | TEXT | Notas administrativas |

**Unicidad:** `(evento, responsable, paquete)` — unique constraint
**Estado:** Solo deportivo/administrativo. NO incluye estado comercial (PAGADA es de Compra)
**Relaciones:**
- 1 Inscripción → 1 Evento, 1 Persona (responsable), 1 Paquete, 1-2 Promociones
- 1 Inscripción → N `equipos` (PROTECT)
- 1 Inscripción → N `inscripcion_personas` (PROTECT)
- 1 Inscripción → N `compras` (PROTECT)
- 1 Inscripción → N `asignaciones_cupo` (PROTECT)

**Quién escribe:** `CrearInscripcionFlujo`, `InscripcionOrchestrator.actualizar_inscripcion_proceso`
**Quién lee:** Todos los endpoints de inscripción

**Verificado:** ✅ Completo

---

#### `equipos` — Equipo deportivo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `inscripcion_id` | FK → Inscripcion | Inscripción padre |
| `disciplina_id` | FK → Disciplina | Disciplina en que compite |
| `categoria_id` | FK → Categoria (nullable) | Categoría (calculada, reservada) |
| `promocion_id` | FK → Promocion (nullable) | Reserva — heredar de inscripción |
| `nombre` | VARCHAR(200) | Nombre libre del equipo |
| `estado` | CHAR(20) | EQUIPO_ACTIVO o EQUIPO_CANCELADO |

**Unicidad:** `(inscripcion, disciplina)` WHERE `estado=EQUIPO_ACTIVO` — partial unique constraint
**Relaciones:**
- 1 Equipo → 1 Inscripción, 1 Disciplina
- 1 Equipo → N `participaciones` (PROTECT)

**Regla:** La categoría se calcula desde `Inscripcion.promocion` usando el rango de `Categoria.promocion_desde/hasta` — no desde la disciplina.

**Verificado:** ✅ Completo

---

#### `inscripciones_personas` — Vínculo inscripción-persona

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `inscripcion_id` | FK → Inscripcion | Inscripción |
| `persona_id` | FK → Persona | Persona registrada |
| `estado` | CHAR(1) | A=Activo, R=Retirado |

**Unicidad:** `(inscripcion, persona)` — unique constraint
**Semántica:** Una misma persona puede estar en múltiples inscripciones (distintos eventos/paquetes). El estado permite retirar sin borrar el registro histórico.
**Relaciones:**
- 1 InscripcionPersona → 1 Inscripcion, 1 Persona
- 1 InscripcionPersona → N `aceptaciones` (CASCADE)
- 1 InscripcionPersona → N `participaciones` (PROTECT)
- 1 InscripcionPersona → N `asignaciones_cupo` (PROTECT)

**Verificado:** ✅ Completo

---

#### `participaciones` — Participación en equipo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `inscripcion_persona_id` | FK → InscripcionPersona | Vínculo inscripción-persona |
| `equipo_id` | FK → Equipo | Equipo |
| `evento_id` | FK → Evento | Redundante para R11 sin JOIN |
| `disciplina_id` | FK → Disciplina | Redundante para R11 sin JOIN |
| `persona_id` | FK → Persona | Redundante para R11 sin JOIN |
| `rol` | CHAR(1) | J=Jugador, C=Capitán, D=Delegado |
| `talla_camiseta` | CHAR(3) | Talla (S, M, L, XL, etc.) |
| `notas` | TEXT | Notas adicionales |
| `estado` | CHAR(1) | A=Activa, R=Retirada |

**Unicidad:** `(evento, disciplina, persona)` WHERE `estado=A` — partial unique constraint (R11)
**R11:** Una persona no puede participar activamente en la misma disciplina del mismo evento a través de dos inscripciones distintas.
**Redundancia controlada:** Los campos `evento`, `disciplina`, `persona` se sincronizan con sus orígenes lógicos via el servicio.

**Verificado:** ✅ Completo

---

#### `compras` — Compra comercial de cupos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `inscripcion_id` | FK → Inscripcion | Inscripción asociada |
| `orden_pago_id` | FK → OrdenPago (1:1) | Orden de pago asociada |
| `tipo` | CHAR(15) | INICIAL o AMPLIACION |
| `cantidad` | INTEGER | Número de cupos comprados |
| `precio_unitario` | DECIMAL(10,2) | Precio snapshot en el momento de compra |
| `total` | DECIMAL(10,2) | Total snapshot = cantidad * precio_unitario |
| `estado` | CHAR(15) | PENDIENTE, PAGADA, CANCELADA |

**Relaciones:**
- 1 Compra → 1 Inscripcion, 1 OrdenPago
- 1 Compra → N `asignaciones_cupo` (PROTECT)

**Semántica:** El estado es exclusivamente comercial. Compra=PAGADA NO implica confirmación deportiva de la Inscripcion.

**Precio:** Se congela al momento de creación de la Compra (decision D2).

**Quién escribe:** `CrearCompraFlujo`, `ConfirmarPagoFlujo`
**Quién lee:** `CompraOrchestrator`, `CompraSelector`

**Verificado:** ✅ Completo

---

#### `asignaciones_cupo` — Cupo asignado a persona

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `inscripcion_id` | FK → Inscripcion | Inscripción duena del cupo |
| `compra_id` | FK → Compra | Compra origen del cupo pagado |
| `inscripcion_persona_id` | FK → InscripcionPersona | Persona asignada |
| `estado` | CHAR(15) | ACTIVA, LIBERADA, REVOCADA |
| `motivo` | TEXT | Razón de liberación/revocación (nullable) |
| `liberada_en` | DATETIME | Timestamp de liberación (nullable) |

**Unicidad:** `(inscripcion, inscripcion_persona)` WHERE `estado=ACTIVA` — partial unique constraint
**Invariantes:**
- `COUNT(AsignacionCupo WHERE compra=X AND estado=ACTIVA) <= Compra.cantidad`
- No hay filas vacías — AsignacionCupo solo se crea cuando una persona se asigna a un cupo pagado

**Semántica de estado:**
- ACTIVA: cupo ocupado por persona activa
- LIBERADA: persona retirada pero compra sigue pagada (cupo disponible para reasignación)
- REVOCADA: revocado por admin

**Quién escribe:** `CrearAsignacionesFlujo` (al confirmar pago), `AsignarPersonaFlujo`, `LiberarCupoFlujo`
**Quién lee:** `AsignacionOrchestrator`, `AsignacionSelector`

**Verificado:** ✅ Completo

---

#### `acreditaciones_evento` — Acreditación efectiva

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `evento_id` | FK → Evento | Evento |
| `persona_id` | FK → Persona | Persona acreditada |
| `estado` | CHAR(15) | PENDIENTE, ACTIVA, SUSPENDIDA, REVOCADA |
| `acceso_fiesta` | BOOLEAN | Derecho efectivo de acceso a fiesta |
| `acceso_box` | BOOLEAN (nullable) | Control individual de zona box (DEFERRED) |
| `autorizacion_fiesta` | CHAR(15) | AUTOMATICA, AUTORIZADA, BLOQUEADA |
| `habilitado` | BOOLEAN (nullable) | Override general de admin |
| `codigo_qr` | UUID | Token no adivinable para escaneo |
| `observacion` | TEXT | Nota administrativa |

**Unicidad:** `(evento, persona)` — unique constraint
**Precedencia de override:**
- `estado=REVOCADA` o `habilitado=False` bloquea independientemente de `acceso_fiesta`
- `autorizacion_fiesta=BLOQUEADA` > `AUTORIZADA` > `AUTOMATICA`
- Admin puede permitir fiesta a alguien que solo compró deporte, o bloquear a alguien que pagó

**QR:** Un solo uso por día de evento (single-use per event day)

**Quién escribe:** `CrearAsignacionesFlujo`, `AcreditacionCoreService.sync_acreditacion_desde_compras`, `OverrideFiestaFlujo`
**Quién lee:** `AcreditacionController`, `AccesoController`

**Verificado:** ✅ Completo

---

#### `controles_acceso` — Registro de intentos de acceso QR

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `acreditacion_id` | FK → AcreditacionEvento | Acreditación usada |
| `fecha_hora` | DATETIME | Timestamp del intento |
| `resultado` | CHAR(10) | PERMITIDO o DENEGADO |
| `punto_acceso` | VARCHAR(100) | Ubicación del scanner (nullable) |
| `operador_id` | FK → User (nullable) | Usuario que autorizó manualmente |

**Unicidad:** `(acreditacion)` WHERE `resultado=PERMITIDO` — partial unique constraint + `select_for_update` en flujo

**Semántica:** QR single-use per event day. `select_for_update` previene race condition TOCTOU.

**Verificado:** ✅ Completo

---

#### `aceptaciones_inscripcion` — Aceptación de documentos legales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `inscripcion_persona_id` | FK → InscripcionPersona (CASCADE) | Vínculo |
| `tipo_aceptacion` | CHAR(20) | BASES, APTITUD_FISICA, IMAGEN |
| `documento_version` | VARCHAR(50) | Versión del documento (ej: "BASES-SF26-2026-09-06") |
| `aceptado_en` | DATETIME | Timestamp (auto_now_add) |
| `actor_id` | VARCHAR(36) | ID de la persona que declaró la aceptación |
| `medio` | CHAR(10) | WEB, MOBILE, PAPER |
| `ip_address` | IPADDRESS | Dirección IP (nullable) |

**Unicidad:** `(inscripcion_persona, tipo_aceptacion)` — unique constraint
**Versión actual de bases:** `BASES-SF26-2026-09-06` (hardcoded en `AgregarPersonaFlujo`)

**Verificado:** ✅ Completo

---

### 2.4 Módulo: `pagos`

#### `pagos_ordenes_pago` — Orden de pago genérica

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `numero` | VARCHAR(20) | Número de orden — único |
| `monto_total` | DECIMAL(10,2) | Monto total |
| `moneda` | VARCHAR(3) | Moneda (default: PEN) |
| `estado` | CHAR(15) | PENDIENTE, PAGADA, CANCELADA, EXPIRADA |
| `pagada_en` | DATETIME | Timestamp de pago (nullable) |
| `expires_at` | DATETIME | Fecha de expiración (nullable) |

**Relaciones:**
- 1 OrdenPago → 1 `compra` (1:1, PROTECT)
- 1 OrdenPago → N `transacciones` (PROTECT)

**Verificado:** ✅ Completo

---

#### `pagos_transacciones_pago` — Transacción Izipay

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | PK |
| `orden_pago_id` | FK → OrdenPago | Orden asociada |
| `transaction_id` | VARCHAR(100) | ID de transacción Izipay — único |
| `order_number` | VARCHAR(100) | Número de orden |
| `amount` | DECIMAL(10,2) | Monto |
| `currency` | VARCHAR(3) | Moneda |
| `status` | CHAR(20) | Estado Izipay |
| `response_code` | VARCHAR(10) | Código de respuesta |
| `response_message` | TEXT | Mensaje de respuesta |
| `metodo_pago` | VARCHAR(20) | Método de pago |
| `metadata` | JSON | Metadatos |

**Índices:** `(orden_pago, status)`, `(orden_pago, created_at)`
**Semántica:** Múltiples intentos por orden (reintento en caso de falla)

**Verificado:** ✅ Completo

---

## 3. DIAGRAMA DE RELACIONES ENTIDAD (Mermaid)

```mermaid
erDiagram
    EVENTO {
        uuid id PK
        string nombre
        date fecha_inicio
        date fecha_fin
        boolean esta_activo
        date fecha_limite_modificacion
    }

    PERSONA {
        uuid id PK
        string numero_documento UK
        string nombres
        string apellidos
        string email
        string telefono
        string whatsapp
        char genero
        date fecha_nacimiento
    }

    USUARIO {
        uuid id PK
        uuid persona_fk FK
        string username UK
    }

    DISCIPLINA {
        uuid id PK
        string nombre
        string sigla UK
        char modalidad
        int min_jugadores
        int max_jugadores
        boolean esta_activa
    }

    PROMOCION {
        uuid id PK
        int anio UK
        string nombre
        boolean activa
    }

    CATEGORIA {
        uuid id PK
        uuid evento_fk FK
        string nombre
        int promocion_desde
        int promocion_hasta
        boolean esta_activa
    }

    PAQUETE {
        uuid id PK
        uuid evento_fk FK
        string nombre
        text descripcion
        char tipo
        char modo_disciplinas
        int cantidad_disciplinas
        int minimo_compra_inicial
        boolean activo
    }

    PAQUETE_PRECIO {
        uuid id PK
        uuid paquete_fk FK
        char etapa
        decimal precio_unitario
        date vigente_desde
        date vigente_hasta
        boolean activo
    }

    PAQUETE_BENEFICIO {
        uuid id PK
        uuid paquete_fk FK
        char tipo
        int cantidad
        char alcance
        char modo_calculo
    }

    PAQUETE_DISCIPLINA {
        uuid id PK
        uuid paquete_fk FK
        uuid disciplina_fk FK
    }

    INSCRIPCION {
        uuid id PK
        uuid evento_fk FK
        uuid responsable_fk FK
        uuid paquete_fk FK
        uuid promocion_fk FK
        uuid fusion_promocion_fk FK nullable
        uuid delegado_fk FK nullable
        char estado
        text observacion
    }

    EQUIPO {
        uuid id PK
        uuid inscripcion_fk FK
        uuid disciplina_fk FK
        uuid categoria_fk FK nullable
        uuid promocion_fk FK nullable
        string nombre
        char estado
    }

    INSCRIPCION_PERSONA {
        uuid id PK
        uuid inscripcion_fk FK
        uuid persona_fk FK
        char estado
    }

    PARTICIPACION {
        uuid id PK
        uuid inscripcion_persona_fk FK
        uuid equipo_fk FK
        uuid evento_fk FK
        uuid disciplina_fk FK
        uuid persona_fk FK
        char rol
        string talla_camiseta
        text notas
        char estado
    }

    ORDEN_PAGO {
        uuid id PK
        string numero UK
        decimal monto_total
        char moneda
        char estado
        datetime pagada_en
        datetime expires_at
    }

    COMPRA {
        uuid id PK
        uuid inscripcion_fk FK
        uuid orden_pago_fk FK 1:1
        char tipo
        int cantidad
        decimal precio_unitario
        decimal total
        char estado
    }

    TRANSACCION_PAGO {
        uuid id PK
        uuid orden_pago_fk FK
        string transaction_id UK
        string order_number
        decimal amount
        char currency
        char status
        string response_code
        text response_message
        string metodo_pago
        json metadata
    }

    ASIGNACION_CUPO {
        uuid id PK
        uuid inscripcion_fk FK
        uuid compra_fk FK
        uuid inscripcion_persona_fk FK
        char estado
        text motivo
        datetime liberada_en
    }

    ACREDITACION_EVENTO {
        uuid id PK
        uuid evento_fk FK
        uuid persona_fk FK
        char estado
        boolean acceso_fiesta
        boolean acceso_box
        char autorizacion_fiesta
        boolean habilitado
        uuid codigo_qr UK
        text observacion
    }

    CONTROL_ACCESO {
        uuid id PK
        uuid acreditacion_fk FK
        datetime fecha_hora
        char resultado
        string punto_acceso
        uuid operador_fk FK nullable
    }

    ACEPTACION_INSCRIPCION {
        uuid id PK
        uuid inscripcion_persona_fk FK CASCADE
        char tipo_aceptacion
        string documento_version
        datetime aceptado_en
        string actor_id
        char medio
        string ip_address
    }

    EVENTO ||--o{ PAQUETE : "1:N"
    EVENTO ||--o{ CATEGORIA : "1:N"
    EVENTO ||--o{ INSCRIPCION : "1:N"
    EVENTO ||--o{ ACREDITACION_EVENTO : "1:N"
    EVENTO ||--o{ PARTICIPACION : "1:N"

    PERSONA ||--o{ USUARIO : "1:1"
    PERSONA ||--o{ INSCRIPCION : "responsable 1:N"
    PERSONA ||--o{ INSCRIPCION : "delegado 1:N"
    PERSONA ||--o{ INSCRIPCION_PERSONA : "1:N"
    PERSONA ||--o{ PARTICIPACION : "1:N"
    PERSONA ||--o{ ACREDITACION_EVENTO : "1:N"

    PAQUETE ||--o{ PAQUETE_PRECIO : "1:N"
    PAQUETE ||--o{ PAQUETE_BENEFICIO : "1:N"
    PAQUETE ||--o{ PAQUETE_DISCIPLINA : "1:N"
    PAQUETE ||--o{ INSCRIPCION : "1:N"

    DISCIPLINA ||--o{ PAQUETE_DISCIPLINA : "1:N"
    DISCIPLINA ||--o{ EQUIPO : "1:N"
    DISCIPLINA ||--o{ PARTICIPACION : "1:N"

    PROMOCION ||--o{ CATEGORIA : "1:N"
    PROMOCION ||--o{ INSCRIPCION : "1:N"
    PROMOCION ||--o{ INSCRIPCION : "fusion_promocion 1:N"
    PROMOCION ||--o{ EQUIPO : "1:N"

    CATEGORIA ||--o{ EQUIPO : "1:N"

    INSCRIPCION ||--o{ EQUIPO : "1:N"
    INSCRIPCION ||--o{ INSCRIPCION_PERSONA : "1:N"
    INSCRIPCION ||--o{ COMPRA : "1:N"
    INSCRIPCION ||--o{ ASIGNACION_CUPO : "1:N"

    EQUIPO ||--o{ PARTICIPACION : "1:N"

    INSCRIPCION_PERSONA ||--o{ PARTICIPACION : "1:N"
    INSCRIPCION_PERSONA ||--o{ ASIGNACION_CUPO : "1:N"
    INSCRIPCION_PERSONA ||--o{ ACEPTACION_INSCRIPCION : "1:N CASCADE"

    ORDEN_PAGO ||--|| COMPRA : "1:1"
    ORDEN_PAGO ||--o{ TRANSACCION_PAGO : "1:N"

    COMPRA ||--o{ ASIGNACION_CUPO : "1:N"

    ACREDITACION_EVENTO ||--o{ CONTROL_ACCESO : "1:N"

    USUARIO ||--o{ CONTROL_ACCESO : "operador 1:N"
```

---

## 4. FLUJOS END-TO-END

### 4.1 Flujo de Catálogo

```
Usuario abre app
    ↓
GET /api/catalogo/disciplinas/
GET /api/catalogo/promociones/
GET /api/catalogo/categorias/
GET /api/catalogo/paquetes/
GET /api/catalogo/paquetes/{id}/
    ↓
CatalogoController.listar_*()
    ↓
sync_to_async(Selector.get_activas/get_activos/get_by_id)
    ↓
CatalogoPresenter.present_*()
    ↓
ApiResponse[{...}]
```

**Fuentes de datos:**
- Disciplinas → `Disciplina.objects.filter(esta_activa=True)`
- Promociones → `Promocion.objects.filter(activa=True)`
- Categorías → `Categoria.objects.filter(esta_activa=True)`
- Paquetes → `Paquete.objects.filter(activo=True).prefetch_related('precios', 'beneficios', 'paquete_disciplinas')`

**Verificado:** ✅ Completo

---

### 4.2 Flujo de Autenticación / Búsqueda de Persona

```
Usuario ingresa DNI
    ↓
GET /api/personas/busqueda/{documento}
    ↓
PersonaBusquedaController.buscar_por_documento()
    ↓
sync_to_async(PersonaBusquedaFlujo.ejecutar)
    ↓
SIP Client (CIP simulator o real) → busca persona
    ↓
Si existe: PersonaResult
Si no existe: {"existe": false, "sugerencia_registro": true}
    ↓
Registro (si no existe):
POST /api/registro/ {tipo_documento, numero_documento, nombres, apellidos, email, ...}
    ↓
RegistroFlujo.ejecutar() → Crea Persona + Usuario → JWT
```

**Fuente:** `modules/usuarios/domain/services/flujos/persona_busqueda_flujo.py`
**CIP Simulator:** `modules/usuarios/infrastructure/services.py` — `CipClientSimulator`

**Verificado:** ✅ Completo

---

### 4.3 Flujo de Inscripción (Creación)

```
Usuario autenticado (JWT)
    ↓
POST /api/inscripciones/
{
  evento_id,
  paquete_id,
  promocion_id,
  fusion_promocion_id (opcional),
  delegado_id (opcional),
  estado: "BORRADOR",
  observacion: ""
}
    ↓
InscripcionController.crear_inscripcion()
    ↓
InscripcionOrchestrator.crear_inscripcion_proceso()
    ↓
sync_to_async(CrearInscripcionFlujo._crear_atomico)
    ↓
transaction.atomic():
  - Crear Inscripcion (estado=BORRADOR)
  - Relacionar evento, paquete, promocion, responsable
    ↓
InscripcionResult
    ↓
InscripcionPresenter.present_inscripcion()
    ↓
ApiResponse<InscripcionOut>
```

**Restricciones:**
- `(evento, responsable, paquete)` debe ser único
- `responsable_id` se deriva del JWT, no del payload

**Verificado:** ✅ Completo

---

### 4.4 Flujo de Equipos y Roster

```
Inscripción existente
    ↓
POST /api/equipos/
{
  inscripcion_id,
  disciplina_id,
  categoria_id (opcional),
  nombre,
  estado: "EQUIPO_ACTIVO"
}
    ↓
EquipoController.crear_equipo()
    ↓
EquipoOrchestrator.crear_equipo_proceso()
    ↓
sync_to_async(CrearEquipoFlujo._crear_atomico)
    ↓
transaction.atomic():
  - Validar fecha_limite no excedida
  - Crear Equipo
    ↓
EquipoResult
```

**Verificado:** ✅ Completo

---

### 4.5 Flujo de Agregar Participante a Equipo

```
Inscripción con equipo existente
    ↓
POST /api/inscripciones/{id}/personas
{
  persona_id,
  equipo_id,
  aceptaciones: ["BASES", "APTITUD_FISICA", "IMAGEN"]
}
    ↓
InscripcionController.agregar_persona()
    ↓
InscripcionOrchestrator.agregar_persona_proceso()
    ↓
sync_to_async(AgregarPersonaFlujo._agregar_atomico)
    ↓
transaction.atomic():
  1. Validar fecha_limite no excedida
  2. Crear/get InscripcionPersona (estado=A)
  3. Si equipo_id: crear Participacion (R11 check)
  4. Registrar AceptacionInscripcion para cada tipo
    ↓
(InscripcionPersona, Participacion | None)
    ↓
InscripcionPresenter.present_*() → ApiResponse
```

**R11:** Validada por `ParticipacionCoreService.crear()`
**Aceptaciones:** Se registran con `update_or_create` para idempotencia

**Verificado:** ✅ Completo

---

### 4.6 Flujo de Compra y Pago

```
Inscripción existente (con estado deportivo)
    ↓
POST /api/compras/
{
  inscripcion_id,
  tipo: "INICIAL" | "AMPLIACION",
  cantidad: N
}
    ↓
CompraController.crear_compra()
    ↓
CompraOrchestrator.crear_compra()
    ↓
sync_to_async(CrearCompraFlujo._crear_compra_sync)
    ↓
transaction.atomic():
  1. Obtener precio vigente de PaquetePrecio (PREVENTA o REGULAR según fecha)
  2. Validar cantidad >= minimo_compra_inicial (solo para INICIAL)
  3. Congelar precio_unitario
  4. Calcular total = cantidad * precio_unitario
  5. Crear OrdenPago (PENDIENTE) via IzipayCoreService
  6. Crear Compra (PENDIENTE) vinculada a OrdenPago
    ↓
CompraCreatedResult {compra_id, orden_pago_id, tipo, cantidad, precio_unitario, total, estado}
    ↓
CompraPresenter.present_created() → ApiResponse<CompraCreateOut>
```

**Precio vigente:**
- `PREVENTA`: si `fecha_hoy <= fecha_limite_preventa` (2026-10-31)
- `REGULAR`: si no hay PREVENTA vigente o fecha excedida

**Verificado:** ✅ Completo

---

### 4.7 Flujo de Inicio de Pago Izipay

```
Compra existente (PENDIENTE)
    ↓
POST /api/compras/{id}/iniciar-pago
    ↓
CompraController.iniciar_pago()
    ↓
CompraOrchestrator.iniciar_pago()
    ↓
sync_to_async(IniciarPagoFlujo._iniciar_pago)
    ↓
1. Cargar Compra + OrdenPago (validar PENDIENTE)
2. Obtener buyer data de Inscripcion.responsable (Persona)
3. Llamar PagosOrchestrator.preparar_pago_izipay()
    ↓
PagosOrchestrator.preparar_pago_izipay()
    ↓
IzipayCoreService.crear_token_y_config() → {token, merchant_code, amount, ...}
    ↓
CompraIzipayPreparedResult
    ↓
CompraPresenter.present_iniciar_pago() → {token, merchant_code, order_number, ...}
    ↓
Frontend abre iframe Izipay con token
```

**Fuente:** `modules/pagos/domain/services/flujos/registrar_pago_izipay_flujo.py`

**Verificado:** ✅ Completo

---

### 4.8 Flujo de Confirmación de Pago

```
Izipay callback (POST /api/pagos/webhook) — externo
    ↓
PagosOrchestrator.registrar_pago()
    ↓
1. Validar firma Izipay
2. Crear TransaccionPago (EXITO o FALLIDO)
3. Si EXITO: actualizar OrdenPago.estado = PAGADA, pagada_en
    ↓
POST /api/compras/confirmar-pago?orden_pago_id=X
    ↓
CompraController.confirmar_pago()
    ↓
CompraOrchestrator.confirmar_pago()
    ↓
sync_to_async(ConfirmarPagoFlujo._confirmar_sync)
    ↓
transaction.atomic():
  1. Obtener Compra por orden_pago_id (select_for_update)
  2. Si ya PAGADA: return already_confirmed=True (idempotente)
  3. Marcar Compra.estado = PAGADA
    ↓
4. Trigger implícito: CrearAsignacionesFlujo (para crear AsignacionCupo de personas ya registradas)
    ↓
CompraConfirmedResult
```

**Idempotencia:** Si Compra ya está PAGADA, retorna `already_confirmed=True` sin error.

**Verificado:** ✅ Completo

---

### 4.9 Flujo de Asignación de Cupos (Post-Pago)

```
Compra confirmada (PAGADA)
    ↓
CrearAsignacionesFlujo._crear_asignaciones_por_compra(compra_id)
    ↓
transaction.atomic():
  1. Bloquear Compra con select_for_update
  2. Calcular saldo disponible: (sum(cantidad de compras PAGADAS) - sum(asignaciones ACTIVAS))
  3. Obtener InscripcionPersona con estado=A sin asignacion activa
  4. Para cada persona pendiente hasta disponibles:
     - Crear AsignacionCupo (ACTIVA)
     - Sync AcreditacionEvento para esa persona
    ↓
[{asignacion_id, persona_id, inscripcion_id}, ...]
```

**Importante:** No se crean filas vacías. AsignacionCupo solo existe cuando una persona ocupa un cupo pagado.

**Verificado:** ✅ Completo

---

### 4.10 Flujo de Agregar Persona Post-Pago (Con Cupo Disponible)

```
Usuario quiere agregar persona a inscripción ya pagada
    ↓
POST /api/asignaciones/
{
  inscripcion_id,
  persona_id
}
    ↓
AsignacionController.asignar_persona()
    ↓
AsignacionOrchestrator.asignar_persona()
    ↓
sync_to_async(AsignarPersonaFlujo._asignar_persona_sync)
    ↓
transaction.atomic():
  1. Verificar fecha_limite no excedida
  2. Verificar persona no tiene asignacion ACTIVA para esta inscripcion
  3. Obtener compra con saldo disponible
  4. Si saldo == 0: raise CupoAgotadoError
  5. Crear/get InscripcionPersona (estado=A)
  6. Crear AsignacionCupo (ACTIVA)
  7. Sync AcreditacionEvento
    ↓
Si persona tenía asignacion LIBERADA: se reactiva
```

**Verificado:** ✅ Completo

---

### 4.11 Flujo de Liberación de Cupo (Retirar Participante)

```
POST /api/asignaciones/liberar
{
  inscripcion_id,
  persona_id,
  motivo (opcional)
}
    ↓
AsignacionController.liberar_cupo()
    ↓
AsignacionOrchestrator.liberar_cupo()
    ↓
sync_to_async(LiberarCupoFlujo._liberar_cupo_sync)
    ↓
transaction.atomic():
  1. Verificar fecha_limite no excedida
  2. Marcar Participacion.estado = RETIRADA para todas las participaciones de esta persona
  3. Si no hay más participaciones activas de esta persona en esta inscripcion:
     - Marcar AsignacionCupo.estado = LIBERADA
  4. Recalcular AcreditacionEvento para la persona (puede mantener acceso via otra inscripcion)
    ↓
La compra NO se devuelve. El cupo queda disponible para reasignación.
```

**R10:** Una persona puede mantener su acreditación via otra inscripción si fue retirada de una.

**Verificado:** ✅ Completo

---

### 4.12 Flujo de Acreditación y Acceso QR

```
Participante con AsignacionCupo ACTIVA
    ↓
AcreditacionCoreService.sync_acreditacion_desde_compras(evento_id, persona_id)
    ↓
Para cada Compra PAGADA de la inscripcion de esa persona:
  - Calcular acceso_fiesta según beneficios del paquete
  - Crear/get AcreditacionEvento (estado según reglas)
    ↓
GET /api/acreditaciones/{evento_id}/{persona_id}
    ↓
AcreditacionController.obtener_acreditacion()
    ↓
AcreditacionPresenter.present_acreditacion()
    ↓
{codigo_qr, acceso_fiesta, autorizacion_fiesta, ...}
```

**Override admin:**
```
PATCH /api/acreditaciones/{evento_id}/{persona_id}/override-fiesta
{
  autorizacion: "AUTORIZADA" | "BLOQUEADA",
  motivo: "..."
}
```

**Verificado:** ✅ Completo

---

### 4.13 Flujo de Registro de Acceso QR (Día del Evento)

```
Scanner QR → POST /api/acceso/registrar
{
  qr_token: "uuid-no-adivinable"
}
    ↓
AccesoController.registrar_acceso()
    ↓
AcreditacionOrchestrator.registrar_acceso()
    ↓
sync_to_async(RegistrarAccesoFlujo._registrar_acceso_sync)
    ↓
transaction.atomic():
  1. Buscar AcreditacionEvento por codigo_qr
  2. Verificar no haya ControlAcceso PERMITIDO hoy (single-use)
  3. Validar acceso_fiesta (precedence: BLOQUEADA > AUTORIZADA > AUTOMATICA)
  4. Crear ControlAcceso (PERMITIDO o DENEGADO)
    ↓
{resultado: "PERMITIDO" | "DENEGADO", persona_nombre, acceso_fiesta, timestamp}
```

**Single-use:** Un QR solo permite un acceso PERMITIDO por día de evento.

**Verificado:** ✅ Completo

---

## 5. MAPA DE APIs

### 5.1 Catálogo (público)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/catalogo/disciplinas/` | AllowAny | Lista de disciplinas activas |
| GET | `/api/catalogo/promociones/` | AllowAny | Lista de promociones activas |
| GET | `/api/catalogo/categorias/` | AllowAny | Lista de categorías activas |
| GET | `/api/catalogo/paquetes/` | AllowAny | Lista de paquetes con precios |
| GET | `/api/catalogo/paquetes/{id}/` | AllowAny | Detalle de paquete |

**Responsabilidad:** Solo lectura. Entregan datos para que el usuario seleccione su inscripción.

---

### 5.2 Autenticación y Usuarios

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/auth/login/` | AllowAny | Login (DNI/password → JWT) |
| POST | `/api/registro/` | AllowAny | Registro de nueva persona + usuario |
| GET | `/api/personas/busqueda/{documento}` | AllowAny | Búsqueda por número de documento |
| GET | `/api/auth/me/` | JWT | Datos del usuario autenticado |

**Responsabilidad:** Identificación del usuario, búsqueda de personas existentes.

---

### 5.3 Inscripciones (JWT para crear/listar, público para detalle)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/inscripciones/` | JWT | Crear inscripción deportiva |
| GET | `/api/inscripciones/` | JWT | Lista de inscripciones del usuario |
| GET | `/api/inscripciones/{id}` | AllowAny | Detalle de inscripción |
| GET | `/api/inscripciones/{id}/detalle` | AllowAny | Detalle con equipos y roster |
| PATCH | `/api/inscripciones/{id}` | AllowAny | Actualizar estado/delegado/observación |

**Responsabilidad:** Creación y gestión de inscripciones deportivas.

---

### 5.4 Equipos (público)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/equipos/` | AllowAny | Crear equipo |
| GET | `/api/equipos/{id}` | AllowAny | Obtener equipo |
| GET | `/api/equipos/inscripcion/{id}` | AllowAny | Lista de equipos de inscripción |

**Responsabilidad:** Gestión de equipos dentro de una inscripción.

---

### 5.5 Participaciones (público)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/participaciones/` | AllowAny | Crear participación |
| GET | `/api/participaciones/{id}` | AllowAny | Obtener participación |
| GET | `/api/participaciones/equipo/{id}` | AllowAny | Lista de participantes de equipo |
| PATCH | `/api/participaciones/{id}` | AllowAny | **ACTUALIZAR** participación (CRITICAL - ver GAPS) |
| PATCH | `/api/participaciones/{id}/retirar` | AllowAny | Retirar participación |
| PATCH | `/api/participaciones/{id}/mover` | AllowAny | Mover a otro equipo |

**Responsabilidad:** Gestión de roster (participaciones en equipos).

---

### 5.6 Compras (JWT)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/compras/` | JWT | Crear compra (inicial o ampliación) |
| GET | `/api/compras/{id}` | JWT | Detalle de compra |
| GET | `/api/compras/inscripciones/{id}/compras` | JWT | Lista de compras de inscripción |
| POST | `/api/compras/{id}/iniciar-pago` | JWT | Generar token Izipay |
| POST | `/api/compras/confirmar-pago` | JWT | Confirmar pago (callback) |

**Responsabilidad:** Gestión comercial de cupos.

---

### 5.7 Asignaciones (JWT)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/asignaciones/` | JWT | Asignar persona a cupo disponible |
| GET | `/api/asignaciones/{id}` | JWT | Detalle de asignación |
| GET | `/api/asignaciones/inscripciones/{id}/asignaciones` | JWT | Lista de asignaciones |
| POST | `/api/asignaciones/liberar` | JWT | Liberar cupo (retirar persona) |
| GET | `/api/inscripciones/{id}/saldo` | JWT | Saldo: contratados/pagados/asignados/disponibles |

**Responsabilidad:** Gestión de cupos pagados y su asignación a personas.

---

### 5.8 Acreditaciones (JWT)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/acreditaciones/{evento_id}/{persona_id}` | JWT | Obtener acreditación |
| PATCH | `/api/acreditaciones/{evento_id}/{persona_id}/override-fiesta` | JWT | Override admin de fiesta |
| POST | `/api/acreditaciones/{evento_id}/{persona_id}/generar-qr` | JWT | Regenerar QR |

---

### 5.9 Acceso (JWT)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/acceso/registrar` | JWT | Registrar intento de acceso QR |

---

## 6. SEMILLAS DE DATOS Y REGLAS COMERCIALES

### 6.1 Seed: `python manage.py seed_catalogo_fest`

**Comportamiento:**
- Idempotente: usa `get_or_create` / `update_or_create`
- Soporta `--clear` para borrar y recrear
- Envuelto en `transaction.atomic`

**Datos creados:**

1. **1 Evento:** "Salesianos FEST 2026" (2026-11-15 a 2026-11-20)

2. **56 Promociones:** Una por año (1970–2025) con nombre según rango etario

3. **4 Categorías oficiales:** Junior, Senior, Master, Super Master
   - Elimina obsoletas: Sub-14, Sub-16, Sub-18, Sub-20

4. **4 Disciplinas:**
   - Fútbol 7 Masculino (F7M) — min 7, max 10
   - Fútbol 7 Femenino (F7F) — min 7, max 10
   - Vóley Mixto (VOL) — min 6, max 8
   - Básquet Masculino (BAS) — min 5, max 10

5. **8 Paquetes** con precios de preventa y regular:
   - 4 PACK con beneficios (fiesta, box, cerveza)
   - 4 DISCIPLINA individual

### 6.2 Reglas Comerciales de Precios

| Regla | Descripción |
|-------|-------------|
| Etapa PREVENTA | Vigente hasta 2026-10-31 inclusive |
| Etapa REGULAR | Desde 2026-11-01 en adelante |
| Precio congelado | Se congela al momento de crear la Compra |
| Mínimo INICIAL | Validado contra `paquete.minimo_compra_inicial` |
| AMPLIACION | Sin validación de mínimo |

### 6.3 Reglas de Beneficios

| Paquete | Beneficio | Alcance | Modo Cálculo |
|---------|-----------|---------|-------------|
| Reencuentro + Fiesta | FIESTA x1 | INDIVIDUAL | FIJO_INICIAL |
| Pichanga + Fiesta | FIESTA x1 | INDIVIDUAL | FIJO_INICIAL |
| Dúo + Fiesta Box | FIESTA x1 | INDIVIDUAL | POR_CUPO |
| Dúo + Fiesta Box | BOX x1 | GRUPAL | FIJO_INICIAL |
| Dúo + Fiesta Box | CERVEZA x6 | GRUPAL | FIJO_INICIAL |
| Trío + Fiesta Box | FIESTA x1 | INDIVIDUAL | POR_CUPO |
| Trío + Fiesta Box | BOX x1 | GRUPAL | FIJO_INICIAL |
| Trío + Fiesta Box | CERVEZA x6 | GRUPAL | FIJO_INICIAL |

**POR_CUPO:** cada persona con cupo pagado recibe el beneficio.
**FIJO_INICIAL:** un solo beneficio grupal por inscripción.

---

## 7. FRONTEND: PANTALLAS, HOOKS, SERVICIOS Y DEPENDENCIAS

### 7.1 Mapeo Frontend → Backend

| Pantalla/Componente | Hook/Service | Endpoint Backend | Datos |
|---------------------|-------------|------------------|-------|
| `LoginClientShell` | `useLogin` | POST `/api/auth/login/` | JWT |
| `RegisterClientShell` | `useRegistro` | POST `/api/registro/` | Persona + Usuario |
| `InscripcionClientShell` (wizard) | `useCreateInscripcion` | POST `/api/inscripciones/` | Inscripcion |
| `InscripcionDetailView` | `useInscripcionDetalle` | GET `/api/inscripciones/{id}/detalle` | Detalle con equipos y roster |
| Catálogo | `useInscripcionCatalogs` | GET `/api/catalogo/*/` | Paquetes, disciplinas, categorías |
| `AgregarmeModal` | `useAgregarParticipantes` | POST `/api/inscripciones/{id}/personas` | Agrega persona a equipo |
| `EditParticipanteModal` | `useEditarParticipante` | PATCH `/api/participaciones/{id}` | **CRITICAL GAP** |
| `SortableEquipoCard` | `useMoverParticipante` | PATCH `/api/participaciones/{id}/mover` | Mover a otro equipo |
| `StepDeclarations` | `useEliminarParticipante` | PATCH `/api/participaciones/{id}/retirar` | Retirar participante |
| Dashboard | `getMisInscripciones` | GET `/api/inscripciones/` | Lista de inscripciones |

### 7.2 Frontend: Tipos Principales (verificados)

```typescript
// InscripcionOut — lista de inscripciones
interface InscripcionOut {
  id: string;
  evento_id: string;
  evento_nombre: string;
  responsable_id: string;
  paquete_id: string;
  paquete_nombre: string;
  estado: string;
  created_at: string;
}

// InscripcionDetalleOut — detalle completo
interface InscripcionDetalleOut {
  id: string;
  evento_id: string;
  evento_nombre: string;
  responsable_id: string;
  responsable_nombre: string;
  paquete_id: string;
  paquete_nombre: string;
  promocion_id: string;
  promocion_nombre: string;
  fusion_promocion_id: string | null;
  delegado_id: string | null;
  delegado_nombre: string | null;
  estado: string;
  observacion: string | null;
  created_at: string;
  equipos: EquipoDetalleOut[];
  personas: InscripcionPersonaSummaryOut[];
}

// EquipoDetalleOut — equipo con participantes
interface EquipoDetalleOut {
  id: string;
  inscripcion_id: string;
  disciplina_id: string;
  categoria_id: string | null;
  nombre: string;
  disciplina: DisciplinaResumen;
  categoria: CategoriaResumen | null;
  participantes: ParticipanteOut[];
}

// ParticipanteOut — participante en equipo
interface ParticipanteOut {
  id: string;
  inscripcion_persona_id: string;
  equipo_id: string;
  equipo_nombre: string;
  evento_id: string;
  disciplina: DisciplinaResumen;
  persona: PersonaResumen;
  rol: string; // J, C, D
  talla_camiseta: string | null;
  notas: string | null;
  estado: string; // A, R
  created_at: string;
}
```

---

## 8. MÁQUINAS DE ESTADO

### 8.1 Inscripcion.estado

```
BORRADOR → RECIBIDA → EN_REVISION → VALIDADA → CONFIRMADA
                ↓           ↓
            OBSERVADA ←──┘
                ↓
           RECHAZADA
                ↓
           CANCELADA
```

**Nota:** Las transiciones exactas y roles autorizados están pendientes de confirmación de producto.

### 8.2 Compra.estado

```
PENDIENTE → PAGADA
    ↓
  CANCELADA
```

### 8.3 AsignacionCupo.estado

```
ACTIVA → LIBERADA
  ↓        ↓
  └─→ REVOCADA
```

### 8.4 AcreditacionEvento.estado

```
PENDIENTE → ACTIVA
    ↓         ↓
  SUSPENDIDA ←┘
    ↓
  REVOCADA
```

### 8.5 Participacion.estado

```
A (Activa) → R (Retirada)
```

### 8.6 ControlAcceso.resultado

```
PERMITIDO | DENEGADO
```

---

## 9. INVARIANTES Y REGLAS DE NEGOCIO

| # | Regla | Descripción |
|---|-------|-------------|
| R1 | `(evento, responsable, paquete)` único | Una persona no puede tener dos inscripciones al mismo evento con el mismo paquete |
| R2 | `minimo_compra_inicial` para INICIAL | La cantidad inicial debe ser >= el mínimo del paquete |
| R3 | Precio congelado | El precio no cambia aunque el precio del paquete cambie después |
| R4 | No filas vacías de AsignacionCupo | Solo se crea cuando una persona ocupa un cupo pagado |
| R5 | R11: Unique `(evento, disciplina, persona)` WHERE ACTIVA | Una persona no puede participar dos veces en la misma disciplina del mismo evento |
| R6 | Fecha límite de modificación | Después de `evento.fecha_limite_modificacion` no se permiten cambios de roster/equipos/cupos |
| R7 | QR single-use per day | Un QR solo permite un acceso PERMITIDO por día de evento |
| R8 | Precedencia override admin | `estado=REVOCADA` o `habilitado=False` > `autorizacion_fiesta=BLOQUEADA` > `AUTORIZADA` > `AUTOMATICA` |
| R9 | AMPLIACION no duplica beneficios | Al comprar más cupos, los beneficios existentes no se multiplican |
| R10 | Acreditación via otra inscripción | Una persona puede mantener su acreditación si está en otra inscripción aunque se retire de una |
| R11 | Partial unique constraint | La constraint parcial `(evento, disciplina, persona)` WHERE `estado=A` + `select_for_update` previene race conditions |

---

## 10. REGLAS DIFERIDAS (DEFERRED)

| # | Regla | Estado |
|---|-------|--------|
| D1 | 1 Compra → 1 OrdenPago (OneToOne) | ✅ Implementado |
| D2 | Precio congelado al momento de creación de Compra | ✅ Implementado |
| D3 | `acceso_box` en AcreditacionEvento es nullable/deferred | ⚠️ Campo existe pero lógica no implementada |
| D4 | Transiciones de estado de Inscripcion (CONFIRMADA, etc.) | ⚠️ Pendiente de confirmación de producto |
| D5 | Fusión de promociones (politica pendiente) | ⚠️ Campo `fusion_promocion` existe sin validación |

---

## 11. GAPS CONOCIDOS Y RIESGOS

### 11.1 RESUELTO: Editar Participante

| Tema | Detalle |
|------|---------|
| **Endpoint** | `PATCH /api/participaciones/{id}` |
| **Estado backend** | `PATCH /participaciones/{id}` usa `ActualizarParticipacionIn` y `actualizar_participacion_proceso`. |
| **Estado frontend** | `editarParticipante()` llama a `PATCH /participaciones/${participanteId}` con los nombres de campo alineados. |
| **Impacto** | Permite actualizar rol, `talla_camiseta` y notas de un participante. |
| **Fuente** | `backend/modules/salesianos_fest/presentation/controllers/inscripcion_controller.py` y `participacion_orchestrator.py`. |
| **Cobertura** | `test_actualizar_participacion` en `test_inscripcion.py`. |

**Verificado:** ✅ Corregido después del Explore inicial; la documentación refleja el estado posterior al Apply.

---

### 11.2 MEDIUM: Dashboard Auth Guard

| Tema | Detalle |
|------|---------|
| **Endpoint** | `GET /api/inscripciones/` |
| **Backend** | `auth=JWTAuth()` — JWT requerido |
| **Frontend** | `DashboardPage` llama `getMisInscripciones()` sin verificar auth primero |
| **Impacto** | Usuario no autenticado recibe 401 a nivel de red, no redirect graceful |
| **Fuente** | `frontend/src/features/.../DashboardPage.tsx` |

---

### 11.3 LOW: Multi-step Creation Flow No Verificado

| Tema | Detalle |
|------|---------|
| **Flujo** | Crear inscripción → crear equipos → agregar participantes |
| **Backend** | Implementado |
| **Frontend** | No verificado que el wizard encadene correctamente los pasos |
| **Impacto** | Puede haber inconsistencias si el frontend no sigue la secuencia correcta |

---

### 11.4 MEDIUM: Campo `acceso_box` Deferred

| Tema | Detalle |
|------|---------|
| **Campo** | `AcreditacionEvento.acceso_box` (Boolean, nullable) |
| **Descripción** | Control individual de zona box |
| **Estado** | Campo existe en modelo, pero la lógica de cálculo y sync NO está implementada |
| **Impacto** | El acceso a zona box no se calcula correctamente |

---

### 11.5 LOW: Campo `fusion_promocion` Sin Validación

| Tema | Detalle |
|------|---------|
| **Campo** | `Inscripcion.fusion_promocion` (FK nullable a Promocion) |
| **Descripción** | Promoción secundaria opcional para fusión |
| **Estado** | Campo existe, sin validación de política de fusión |
| **Impacto** | No hay reglas de negocio para fusión de promociones |

---

### 11.6 MEDIUM: Version Hardcoded de Documento de Bases

| Tema | Detalle |
|------|---------|
| **Ubicación** | `AgregarPersonaFlujo.DOCUMENTO_VERSION_BASES = "BASES-SF26-2026-09-06"` |
| **Descripción** | Versión del documento de aceptación hardcoded |
| **Impacto** | Si cambia la versión de las bases, hay que cambiar código |

---

## 12. GUÍA DE DIAGNÓSTICO PARA DESAJUSTES FRONTEND/BACKEND

### 12.1 Checklist de Verificación

| # | Pregunta | Si la respuesta es NO |
|---|----------|----------------------|
| 1 | ¿El endpoint existe en el backend? | Verificar `ParticipacionController` |
| 2 | ¿El schema de request coincide con el payload del frontend? | Comparar `ActualizarParticipacionIn` vs `EditarParticipantePayload` |
| 3 | ¿Los nombres de campos coinciden (snake_case vs camelCase)? | Los servicios transforman automáticamente |
| 4 | ¿El tipo de dato es correcto (string vs number vs boolean)? | Verificar en el schema Pydantic y Zod |
| 5 | ¿Los valores posibles del enum son correctos? | Comparar choices de Django con Zod literals |
| 6 | ¿La autenticación es la correcta (JWT vs AllowAny)? | Verificar `auth=` en el controller |
| 7 | ¿El campo es nullable en backend y opcional en frontend? | Verificar `Optional` en Schema y `?` en TypeScript |

### 12.2 Errores Comunes y Causas

| Error frontend | Causa probable |
|----------------|-----------------|
| 404 en `PATCH /participaciones/{id}` | Verificar UUID, slash final y que el servidor haya recargado las rutas actuales. |
| 401 en `GET /inscripciones/` | Falta JWT en el request |
| Campo undefined en respuesta | El selector no está haciendo `prefetch_related` o `select_related` |
| Lista vacía de equipos | La inscripción no tiene equipos creados, o no se hizo `prefetch_related('equipos')` |
| `talla_camiseta` null | El campo existe pero no se está enviando desde el frontend |
| Precio diferente al del catálogo | El precio se congeló al momento de la compra, no se actualiza dinámicamente |

### 12.3 Comandos de Verificación

```bash
# Verificar qué endpoints están registrados
python manage.py show_urls

# Ver estado de la base de datos
python manage.py dbshell
# SELECT * FROM ventas.inscripciones;

# Ver contenido del catálogo
python manage.py shell
# from modules.salesianos_fest.domain.models import *
# Paquete.objects.all().count()
# Disciplina.objects.all().values('nombre', 'sigla')

# Reconstruir catálogo (riesgo: limpia datos)
python manage.py seed_catalogo_fest --clear
```

---

## 13. FUENTES DE VERIFICACIÓN POR ARCHIVO

| Componente | Archivos fuente |
|------------|----------------|
| Modelos | `backend/modules/salesianos_fest/domain/models/*.py` |
| Constants/Choices | `backend/modules/salesianos_fest/domain/constants.py` |
| Controllers | `backend/modules/salesianos_fest/presentation/controllers/*.py` |
| Orchestrators | `backend/modules/salesianos_fest/domain/services/orchestrators/*.py` |
| Flujos | `backend/modules/salesianos_fest/domain/services/flujos/*.py` |
| Selectors | `backend/modules/salesianos_fest/domain/selectors/*.py` |
| Schemas HTTP | `backend/modules/salesianos_fest/presentation/schemas/*.py` |
| Presenters | `backend/modules/salesianos_fest/presentation/presenters/*.py` |
| Seed | `backend/modules/salesianos_fest/management/commands/seed_catalogo_fest.py` |
| Frontend services | `frontend/src/features/inscripciones/services/inscripcion.service.ts` |
| Frontend hooks | `frontend/src/features/inscripciones/hooks/*.ts` |
| Frontend schemas | `frontend/src/features/inscripciones/schemas/*.ts` |
| API Router | `backend/config/api.py` |

---

## 14. CONTRATOS APLICABLES

| Contrato | Ubicación | Relevancia |
|----------|----------|------------|
| `django-app-architecture-contract.md` | `contract/` | Define la estructura de módulos Django |
| `next-app-architecture-contract.md` | `contract/` | Define la estructura de Next.js frontend |
| `api-wrapper-presenter-contract.md` | `contract/` | Define cómo retornan las APIs y cómo se transforman los datos |
| `TEST_ARCHITECTURE_CONTRACT.md` | `contract/` | Define cómo estructurar tests |

---

## 15. RESUMEN DE ESTADO DE VERIFICACIÓN

| Área | Estado | Notas |
|------|--------|-------|
| Catálogo (disciplinas, promociones, categorías, paquetes) | ✅ VERIFICADO | Completo en Fase 2 |
| Inscripciones (creación, listado, detalle) | ✅ VERIFICADO | Completo en Fase 3 |
| Equipos y roster | ✅ VERIFICADO | Completo en Fase 3 |
| Participaciones (crear, retirar, mover) | ✅ VERIFICADO | Retire y mover OK |
| Participaciones (editar) | ❌ CRITICAL GAP | Endpoint PATCH faltante |
| Compras y pagos Izipay | ✅ VERIFICADO | Completo en Fase 4 |
| Asignación de cupos | ✅ VERIFICADO | Completo en Fase 5 |
| Acreditaciones y QR | ✅ VERIFICADO | Completo en Fase 5 |
| Consentimientos (bases, aptitud, imagen) | ✅ VERIFICADO | Completo en Fase 6 |
| Seeds idempotentes | ✅ VERIFICADO | `seed_catalogo_fest` |
| Frontend → Backend contract | ⚠️ PARCIAL | Editar participante roto |

---

*Documento generado automáticamente via SDD Explore. Para actualizar, re-ejecutar el flujo de exploración.*
