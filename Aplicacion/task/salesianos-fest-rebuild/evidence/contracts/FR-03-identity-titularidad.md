# FR-03 — Persona, Usuario, roles y titularidad

**Freeze:** `FREEZE-ID-1.0.0` · **Propietario:** A1 (módulo `usuarios`) · **Estado:** FROZEN (GOV-01)
**Trazabilidad:** `RN-U01`..`RN-U04` · `DEC-02`, `DEC-03`, `DEC-04` · plan `contratos/02-autenticacion-y-permisos.md`, `funcional/02` §1, `funcional/04` FL-02

---

## 1. Decisiones congeladas

### 1.1 `Persona` — identidad civil

| Atributo | Regla congelada |
|---|---|
| Clave natural | `(tipo_documento, numero_documento)` — **única**, con `UniqueConstraint` |
| `tipo_documento` | vocabulario cerrado del módulo de identidad (`DNI`, `CE`, `PAS`) |
| `numero_documento` | string normalizado (sin espacios ni separadores), case-insensitive en la comparación |
| Existen sin cuenta | **Sí**. `Persona` no exige `Usuario` |
| Igual documento en años distintos | **Sí**: la misma `Persona` participa en distintas ediciones (`RN-U01`) |
| Uso del DNI | El DNI es **identificador, no credencial**. No autoriza ver compras de terceros (`RN-U04`) |

### 1.2 `Usuario` — cuenta opcional

| Atributo | Regla congelada |
|---|---|
| Relación con `Persona` | FK `persona` **opcional** y **única** (1:1 opcional). Una `Persona` puede no tener `Usuario`; un `Usuario` puede no tener `Persona` (cuentas técnicas, superusuario) |
| Grupos Django | `Normal` y `Administrador` — **dos** grupos funcionales. `is_superuser` es técnico (`DEC-02`) |
| Nacimiento de cuenta | **Prohibido** crear `Usuario` automáticamente al consultar un documento, al asignar un pase o al prellenar datos de RENIEC (`contratos/02` §1) |
| Credenciales | Django Ninja + JWT (`django-ninja-jwt`). Sin cookie de rol: la autorización se resuelve en backend |

**Prohibido** crear un tercer grupo por defecto. La política de operadores de validación queda abierta (`GOV-01-OPEN-04`, ver `FR-09`).

### 1.3 `Comprador` y `Responsable` — roles derivados, no entidades

| Rol | Definición congelada | No es |
|---|---|---|
| `Comprador` | La `Persona` que figura en `Compra.persona_id`. Puede no tener `Usuario` | un tipo de cuenta |
| `Responsable` | La `Persona` legitimada para gestionar una `Inscripcion` concreta. Se verifica por **titularidad** sobre ese recurso | un permiso global |

## 2. Titularidad — interfaz congelada

`RN-U02`: "La autorización también comprueba **titularidad**, no solo rol". Este freeze congela las **cuatro** formas de titularidad y su comprobación. Cada módulo implementa su comprobación sobre su recurso; la interfaz y los códigos son comunes.

| `#` | Titularidad | Sujeto | Recurso | Verificación |
|---|---|---|---|---|
| 1 | `TITULARIDAD_RESPONSABLE` | `Persona` | `Inscripcion` | `inscripcion.responsable_id == persona.id` **y** la `Persona` está vinculada a la `Usuario` autenticada (si la cuenta existe) |
| 2 | `TITULARIDAD_COMPRADOR` | `Persona` | `Compra` | `compra.persona_id == persona.id` |
| 3 | `TITULARIDAD_BENEFICIARIO` | `Persona` | `PaseBeneficiario` / lote de pases | `pase_beneficiario.persona_id == persona.id` **y** el derecho no está revocado |
| 4 | `TITULARIDAD_ADMIN` | `Usuario` | cualquier recurso | pertenencia al grupo `Administrador` **y** la acción está habilitada para el rol |

### 2.1 Reglas de la interfaz

1. La comprobación de titularidad es **una función del módulo dueño del recurso**. No hay un servicio central de titularidad que consulte modelos de otros módulos (`api-wrapper-presenter-contract.md` §6).
2. **Prohibido** inferir titularidad del conocimiento del documento (`RN-U04`). Conocer un DNI no da acceso a la cuenta ni al historial de compras de otra persona.
3. **Prohibido** que el grupo sustituya la titularidad: ser `Administrador` no hace a alguien responsable de una inscripción ajena, y ser responsable no da administración.
4. Un fallo de titularidad responde `403` con código estable (`ACCESO_NO_AUTORIZADO`) y **nunca** revela la existencia del recurso de otro actor: se responde `404` cuando revelar el recurso ya sería una fuga (`contratos/02` §5 punto 6).
5. `acciones_disponibles` **no** implementa la titularidad. Es proyección de UX; la comprobación real ocurre en el comando (`contratos/01` §6).

### 2.2 Matriz de autenticación vs autorización (congelada)

Recoge `contratos/02` §2 sin ratificar sus pendientes:

| Caso | Autenticación | Autorización adicional |
|---|---|---|
| Ver catálogo público | Ninguna | Edición publicada + módulo habilitado |
| Inscribir equipo | Cuenta de responsable inicialmente | Titularidad y reglas deportivas |
| Gestionar inscripción | Cuenta o canal autorizado | `TITULARIDAD_RESPONSABLE` o `TITULARIDAD_ADMIN` |
| Comprar pase/tienda como invitado | Puede ser anónimo en checkout | Datos mínimos y protección del flujo |
| Recuperar compra invitada | Vínculo seguro/token vigente | Scope limitado a esa compra |
| Asignar beneficiarios de un lote | Cuenta titular o vínculo seguro | `TITULARIDAD_COMPRADOR`, compra pagada, cupos libres |
| Cambiar rol de usuario | Cuenta admin autorizada | Control de elevación + auditoría |
| Validar ticket | Operador autenticado | Permiso operativo + derecho validable |
| Administración general | Grupo `Administrador` | Comando autorizado + reglas de negocio |

## 3. Resolución local → RENIEC (congelada)

`RN-U03` / `DEC-03` / `FL-02`. La interfaz queda congelada; la fuente externa concreta ya existe como servicio HTTP independiente y es referenciada por `usuarios` (`contratos/03` §3).

### 3.1 Resultado del resolver — discriminante obligatorio

`ResolverPersona` devuelve un resultado con **origen explícito**, nunca una `Persona` ambigua:

| `origen` | Significado | Efecto |
|---|---|---|
| `LOCAL` | La `Persona` ya existía en la base | Devuelve la `Persona` persistida |
| `EXTERNO` | Datos obtenidos de la fuente externa, **no persistidos** | Devuelve datos precargados + `persona_id = null`. **No** habilita escritura por sí solo |
| `NO_ENCONTRADO` | La fuente externa no tiene el documento | Error de dominio `PERSONA_NO_ENCONTRADA` (404) |
| `FUENTE_NO_DISPONIBLE` | La fuente externa falló o excedió el tiempo de espera | Error de dominio con código propio. **Prohibido** fabricar identidades (`contratos/03` §7) |

### 3.2 Reglas

1. **Orden obligatorio:** buscar local primero; consultar la fuente externa **solo** si no existe localmente.
2. **Persistencia diferida:** una `Persona` externa se persiste **únicamente** al confirmar la operación real (inscripción, compra, asignación). Antes de eso, no se escribe.
3. **Anti-duplicado:** la creación de una `Persona` por documento debe ser segura ante solicitudes concurrentes (`RN-U03`). Se resuelve con `UniqueConstraint` + reintento controlado ante `IntegrityError`, no con `get_or_create` silencioso que oculte la carrera.
4. **Volumen de consultas:** se aplican límites de frecuencia a las consultas externas. Una consulta externa **no** se registra como registro definitivo.
5. **Origen y fecha de los datos** se conservan cuando se requiere control de calidad (`contratos/03` §3).
6. **Prohibido** usar el resolver para validar titularidad. Resolver un documento no autoriza a comprar ni a consultar.

### 3.3 Estados de fallo distinguibles

Tiempo de espera agotado · datos incompletos · fuente no disponible · documento no encontrado. Son **cuatro** estados distintos, no uno. El frontend debe poder diferenciar "reintentable" de "no existe".

## 4. Compra sin cuenta y recuperación (congelado el mecanismo)

`DEC-04` / `RN-U04` / `contratos/02` §5 / `FL-06`.

| Regla | Contenido congelado |
|---|---|
| Datos mínimos | Documento, email y los datos que el dominio exija. El checkout es **por dominio** (`DEC-10`): no hay carrito conjunto |
| Email | Es un **contacto**, no un activador. El email **no** activa el derecho ni confirma el pago |
| Vínculo de acceso | Token suficientemente aleatorio, con **vencimiento**, **ámbito por compra** y **revocabilidad**. El token **no** tiene por qué viajar en la ruta (`frontend/01` §2 nota) |
| Reenvío | **No revela** si existe una compra para un DNI. Respuesta neutra idéntica en ambos casos |
| Alcance del vínculo | Limitado a esa compra. Un invitado **nunca** consulta el historial completo de otra persona solo por documento |
| Email fallido | **No** anula el pago ni revierte derechos. Notificación reintentable (`contratos/03` §4) |

**Pendiente que este freeze NO resuelve:** la política exacta de expiración, rotación de enlaces y verificación de contacto sigue `[PENDIENTE]` en `contratos/02` §5 → `GOV-01-OPEN-05`.

## 5. Auditoría de acciones sensibles

Toda acción sensible registra: **actor** (usuario y/o persona), **momento**, **motivo** (cuando el caso lo exige) y **referencia** al recurso afectado (`RN-A02`, `contratos/02` §6).

Excepciones de dominio con código estable, nunca prosa interpolada. Los mensajes públicos salen del catálogo de `core/exceptions.py`.

## 6. Consumo del freeze

| Consumidor | Depende de | Acción |
|---|---|---|
| FND-03 (`T-011`, `T-012`) | este freeze | Implementar `Persona`/`Usuario`, la interfaz de titularidad, el resolver local→RENIEC con los cuatro orígenes |
| FND-01 (`T-018`) | este freeze | `core/permissions.py` y capacidades: consumidores de la interfaz de titularidad |
| DOM-01..DOM-08 | `T-011`, `T-012` | Cada módulo implementa su propia comprobación de titularidad sobre su recurso |
| XCT-01 (`T-080`) | este freeze | Validación de ticket: el derecho autoriza a canjear; el grupo autoriza a operar (`contratos/02` §6) |

## 7. Criterios de aceptación de este freeze

- [x] `Persona` única por `(tipo_documento, numero_documento)`, existente sin cuenta.
- [x] `Usuario` con cuenta opcional 1:1 y exactamente dos grupos funcionales.
- [x] Cuatro titularidades nombradas con reglas de verificación y prohibiciones.
- [x] Resolver con origen explícito, persistencia diferida y anti-duplicado concurrente.
- [x] Compra invitada con token acotado, reenvío neutro y email no activador.
- [x] Ninguna `[PENDIENTE]` del plan ratificada sin_owner.

## 8. Decisiones abiertas relacionadas

| ID | Pendiente | Owner |
|---|---|---|
| `GOV-01-OPEN-04` | Grupo o política interna para operadores de validación | A0 + producto |
| `GOV-01-OPEN-05` | Expiración, rotación y verificación de los enlaces de compra invitada | A1 + A0 + producto |
| `PD-07` | Ámbito definitivo del guest checkout (inscripción vs pases/tienda) | A1 + A7 + producto |
