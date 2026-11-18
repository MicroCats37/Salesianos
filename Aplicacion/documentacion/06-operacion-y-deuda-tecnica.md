# 06 — Operación y deuda técnica

> **Ámbito:** topología operativa (contenedores, puertos, healthchecks, arranque), estrategia de base de datos, ausencia de planificador de tareas, y el **registro de hallazgos y deuda técnica** detectados durante la exploración.
> **Método:** verificación directa en `docker-compose.yml`, `proxy/`, `backend/docker/entrypoint.sh`, `backend/config/settings/base.py` y los comandos de gestión de Django.
> **Documentos hermanos:** [01 — Arquitectura y runtime](./01-arquitectura-y-runtime.md) · [03 — Frontend](./03-frontend.md) · [04 — Datos y dominio](./04-datos-y-dominio.md) · [05 — Flujos end-to-end](./05-flujos-end-to-end.md) · [07 — Guía para el agente de UI/UX](./07-guia-para-ui-ux.md)

---

## 1. Alcance y criterio

Este documento tiene dos mitades:

1. **Operación** — cómo se levanta, se monitorea, se degrada y se revierte el sistema hoy.
2. **Deuda técnica** — los defectos verificados, registrados aquí **como hallazgos**, no como tareas de corrección.

> **Criterio aplicado:** ninguno de los hallazgos de § 6 ha sido corregido. Este documento **constata**; no propone parches ni modifica código de aplicación ni de runtime. Cada hallazgo incluye la evidencia y el impacto, para que la decisión de resolverlo sea explícita y posterior a la congelación de la superficie pública.

---

## 2. Topología operativa

### 2.1 Ciclo de vida del compose raíz

El archivo `docker-compose.yml` (raíz del repositorio) define **cinco servicios** con dos volúmenes:

```
docker compose up -d
   │
   ├─ db        (postgres:16-alpine)      volume postgres_data   healthcheck: pg_isready
   ├─ scraper   (worker/scraper)          sin puerto publicado   healthcheck: GET /health
   ├─ backend   (gunicorn x2)             volume backend_static  healthcheck: manage.py check
   │     └─ depends_on: db healthy AND scraper healthy
   ├─ frontend  (Next.js standalone)       expose 3000            sin healthcheck
   └─ proxy     (nginx:1.27-alpine)       ÚNICO puerto publicado
```

| Servicio | Puerto host | Puerto interno | `depends_on` | Healthcheck | Volumen |
|---|---|---|---|---|---|
| `db` | — | 5432 | — | `pg_isready` (intervalo 5 s, timeout 5 s, 5 reintentos, `start_period` 10 s) | `postgres_data` → `/var/lib/postgresql/data` |
| `scraper` | — (`SCRAPER_PORT=7004` declarado en `.env`, **no mapeado**) | 8001 | — | `urllib` a `http://localhost:8001/health` (intervalo 30 s, timeout 5 s, 3 reintentos) | — |
| `backend` | — | 8000 | `db` sano **y** `scraper` sano | `manage.py check` (30 s) | `backend_static` → `/app/staticfiles` |
| `frontend` | — | `expose 3000` (`PORT=3000`) | `backend` | — | — |
| `proxy` | **`${PROXY_PORT:-7000}`** → 80 | — | `frontend`, `backend` | — en el compose raíz (la ruta `/proxy-health` sí existe en `nginx.conf`) | — |

Todos los servicios declaran `restart: unless-stopped`.

### 2.2 Puertos publicados — ambigüedad registrada

| Fuente | Puerto del proxy | Puerto del scraper | Notas |
|---|---|---|---|
| `docker-compose.yml` (raíz) | `${PROXY_PORT:-7000}` | — | El compose raíz solo publica el proxy |
| `.env` (raíz) | `PROXY_PORT=7000` | `SCRAPER_PORT=7004` | `SCRAPER_PORT` no lo usa ningún servicio |
| `.env.example` | **`PROXY_PORT=7005`** | `SCRAPER_PORT=7004` | El ejemplo no coincide con el `.env` real ni con el valor por defecto del compose |
| `proxy/docker-compose.yml` | **`8011:80`** (fijo) | — | Compose nginx **aislado**, con `extra_hosts: host.docker.internal:host-gateway` y su propio healthcheck contra `/proxy-health` |
| `frontend/Dockerfile` | `EXPOSE ${PORT:-7000}` | — | El compose fija `PORT=3000`; el `EXPOSE` por defecto no describe el puerto real |

> **Hallazgo H-3.** Existen **cuatro** declaraciones de puerto para el mismo proxy (`7000`, `7005`, `8011` y el `EXPOSE 7000` del Dockerfile) y **dos** puntos de entrada al mismo `nginx.conf` (el compose raíz y `proxy/docker-compose.yml`). La copia que se consolide en la raíz reconstruida debe fijar un valor único y documentarlo.

### 2.3 Secuencia de arranque del backend

`backend/docker/entrypoint.sh`:

| Paso | Acción | Modo | Resultado |
|---|---|---|---|
| 1 | Sondeo de `psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)` en bucle de 2 s | `root` | Espera a que PostgreSQL acepte conexiones |
| 2 | `manage.py migrate --noinput` | root | Aplica la cadena de migraciones |
| 3 | `chown -R appuser:appuser /app/staticfiles` | root | Corrige permisos del volumen (tolera fallo) |
| 4 | `manage.py collectstatic --noinput` | root | Recolecta estáticos al volumen |
| 5 | `exec gosu appuser uv run gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2` | `appuser` | Servidor de aplicación |

**Lo que el arranque NO hace:** no crea el superusuario, no ejecuta semillas, no lanza ningún planificador, no verifica la coherencia de precios ni repara estados.

### 2.4 Imagen del frontend

Tres etapas: `deps` (`npm ci`) → `builder` (`npm run build`) → `runner` (standalone, usuario `nextjs` uid 1001, `NODE_ENV=production`).

| Variable | Fase declarada | Efectivo en la imagen |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `ARG` + `ENV` (build) | Horneada en el bundle del navegador |
| `NEXT_PUBLIC_COOKIE_SECURE` | `ARG` + `ENV` (build) | Horneada |
| `NEXT_PUBLIC_IS_TEST_UUID` | `ARG` + `ENV` (build) | Horneada |
| `NEXT_PUBLIC_DEBUG_GENERIC_FORM_ERRORS` | `ARG` + `ENV` (build) | Horneada |
| `NEXT_PUBLIC_IZIPAY_ENABLED` | `ARG` + `ENV` (build) | Horneada |
| `NEXT_PUBLIC_AUTH_STORAGE_PREFIX` | **sin `ARG`** — `ENV NEXT_PUBLIC_AUTH_STORAGE_PREFIX=salesianos_auth` literal | **Valor fijo en la imagen**; el `args:` del compose se ignora |
| `NEXT_PUBLIC_FRONTEND_URL` | **ausente por completo** | El compose lo pasa como `args`, pero el Dockerfile no lo declara: no llega al bundle |
| `BACKEND_INTERNAL_URL` | `ARG` + `ENV` (runtime) | Solo en el servidor; nunca en el navegador |

---

## 3. Base de datos operativa

### 3.1 Selección de motor

`backend/config/settings/base.py` selecciona el motor por la variable `USE_SQLITE`:

| Condición | Motor | Nombre |
|---|---|---|
| `USE_SQLITE` ∈ {`1`, `true`, `yes`} | `django.db.backends.sqlite3` | `SQLITE_PATH` (por defecto `:memory:`) |
| En cualquier otro caso | `django.db.backends.postgresql` | `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` (por defecto `localhost`), `DB_PORT` (por defecto `5432`) |

**Dos bases de datos distintas conviven en el repositorio:**

| Instancia | Ruta | Motor | Estado |
|---|---|---|---|
| Desarrollo | `backend/db.sqlite3` | SQLite | Copia local; el `entrypoint.sh` de Docker **no** la usa |
| Contenedor | volumen `postgres_data` | PostgreSQL 16 | La que migra el `entrypoint.sh` |
| Copia de trabajo | `Aplicacion/backend/db.sqlite3` | SQLite | Copia de la anterior |

> **Deuda registrada (no bloqueante pero relevante).** `backend/config/settings/development.py` fija la ruta SQLite de forma absoluta y **no consulta `SQLITE_PATH`**. Un flujo verificado contra SQLite puede no reproducirse contra PostgreSQL. Solo el módulo `competencias` dispone de una prueba de portabilidad de migraciones.

### 3.2 Migraciones

- Se aplican **automáticamente** en el arranque del contenedor (`migrate --noinput`), antes de que gunicorn levante el socket.
- La cadena de migraciones **es** el contrato de esquema. Una base de datos copiada no es una base migrada.
- No hay proceso automatizado de generación de migraciones en CI (deuda heredada del contrato Django, § 16.3).

### 3.3 Semillas y datos iniciales

No hay siembra automática. El `entrypoint.sh` no ejecuta `seed_*`. Las semillas son **comandos manuales** (§ 4.2). Dos de ellas fijan datos de negocio de forma literal:

| Comando | Efecto |
|---|---|
| `seed_catalogo_fest` | Siembra el catálogo del festival **con precios hardcodeados** (`PASE_FIESTA_PREVENTA=25.00`, `REGULAR=35.00`) |
| `seed_commerce` | Siembra fixtures genéricos de compras |

El superusuario se crea con `manage.py create_admin` o `manage.py seed_admin`, **nunca** en el arranque.

---

## 4. Trabajos programados

### 4.1 No existe planificador

Verificación exhaustiva sobre `backend/`, `backend/config/`, `backend/core/`, `backend/modules/`, `frontend/src/`, `proxy/` y `worker/scraper/`:

| Patrón buscado | Resultado |
|---|---|
| `async_task` (django-q2) | **Sin coincidencias** |
| `schedule(` | **Sin coincidencias** |
| `crontab` / `cron` | **Sin coincidencias** |
| Consumidor `qcluster` | **Sin coincidencias** |
| `Q_CLUSTER` | **Presente** en `backend/config/settings/base.py` (4 workers, `recycle 500`, `timeout 60`, `queue_limit 50`, `bulk 10`) |

> **Configuración muerta.** `django_q` está instalado y `Q_CLUSTER` está configurado, pero **no existe ningún consumidor ni ninguna tarea programada**. Todo el trabajo en segundo plano es **manual**.

**Consecuencias operativas directas:**

1. Una confirmación de pago cuyo relay se perdió queda **sin reconciliar** hasta que una persona ejecute `reconciliar_pagos`.
2. Un cupo en estado inconsistente requiere `reparar_cupos`.
3. Un pase vendido sin asignar exige `verificar_pases` (y su salida es un diagnóstico, no una reparación).
4. La **única** recuperación automática del sistema es el sondeo acotado del navegador (2 s × 15 = 30 s) descrito en el flujo 18 de [05 — Flujos end-to-end](./05-flujos-end-to-end.md). Fuera de esa ventana de 30 s y con la pestaña cerrada, no queda ninguna red de seguridad.
5. Documentar estos comandos como "el planificador" sería incorrecto: son herramientas de intervención a demanda.

### 4.2 Comandos manuales disponibles

**13 comandos de gestión propios del proyecto** (excluyendo los de Django, `ninja_jwt`, `django_q`, `simple_history` e `import_export`):

| Comando | Módulo | Naturaleza | Función |
|---|---|---|---|
| `create_admin` | `core` | Escritura | Crea el superusuario fijo de administración |
| `reset_dev` | `core` | **Destructivo** | Restablece artefactos locales y estado de base de datos de desarrollo |
| `seed_commerce` | `commerce` | Escritura | Siembra fixtures genéricos de compra |
| `seed_catalogo_fest` | `salesianos_fest` | Escritura | Siembra el catálogo del festival (con precios literales) |
| `reconciliar_pagos` | `salesianos_fest` | **Reparación** | Repara órdenes pagadas cuya liquidación comercial quedó pendiente |
| `reparar_cupos` | `salesianos_fest` | **Reparación** | Materializa los cupos pagados que nunca se asignaron |
| `verificar_pases` | `salesianos_fest` | **Solo lectura** | Diagnóstico de los pases de fiesta |
| `auditar_genero_disciplinas` | `salesianos_fest` | **Solo lectura** | Auditoría de compatibilidad disciplina/género |
| `verificar_pagos` | `pagos` | **Solo lectura** | Diagnóstico de la evidencia de pago |
| `verificar_intentos_pago` | `pagos` | **Solo lectura** | Preflight de la garantía de "un intento vivo por orden" |
| `seed_admin` | `usuarios` | Escritura | Crea o actualiza el superusuario por defecto del admin de Django |
| `seed_colegiados` | `usuarios` | Escritura | Siembra colegiados desde `seeds/colegiados_reales.json` |
| `seed_perfiles_ingeniero_faltantes` | `usuarios` | Escritura | Siembra `PerfilIngeniero` faltantes a partir de los listados reales |

### 4.3 Variables de entorno de la operación

| Variable | Valor en `.env` | Efecto operativo |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Perfil de Django activo en los contenedores |
| `DEBUG` | `False` | Fuerza la verificación de permisos y el simulador de consulta externa queda desactivado |
| `SECRET_KEY` | `change-me-in-production` | **Marcador de posición en un archivo de entorno real** — ver § 6, nota de riesgo |
| `ALLOWED_HOSTS` | `salesianosfest.pe,www.salesianosfest.pe` | Hosts admitidos |
| `CORS_ALLOWED_ORIGINS` | `https://salesianosfest.pe,https://www.salesianosfest.pe` | Orígenes CORS; `CORS_ALLOW_ALL_ORIGINS=False` |
| `SECURE_SSL_REDIRECT` | `True` | Redirección a HTTPS; exige que el proxy termine TLS |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | `True` | Cookies de sesión Django y CSRF solo por HTTPS |
| `CSRF_TRUSTED_ORIGINS` | Los dos dominios anteriores | Orígenes de confianza CSRF |
| `EVENTO_ACTIVO_NOMBRE` | ausente en `.env` → `"Salesianos FEST 2026"` | Evento activo. **Una segunda edición exige cambiar este valor** |
| `PAGO_MANUAL_APROBACION_ENABLED` | `true` | Interruptor **activo** (el default del código es `False`) |
| `PASES_FIESTA_ENABLED` | ausente → `False` | Interruptor **inactivo**: la compra de pases no está habilitada |
| `IZIPAY_*` | comentados en `.env` | `IZIPAY_KEY_HASH` vacío ⇒ la notificación del proveedor **falla cerrado** |
| `SCRAPER_URL` | `http://scraper:8001` | Único modo de alcanzar el scraper |

---

## 5. Despliegue y reversibilidad

### 5.1 Interruptores de despliegue

Dos capacidades se despliegan con el patrón "primero el modelo y la auditoría, después la acción":

| Interruptor | Default del código | Valor en `.env` | Reversión |
|---|---|---|---|
| `PAGO_MANUAL_APROBACION_ENABLED` | `False` | `true` | Desactivar el flag; la auditoría nunca se borra |
| `PASES_FIESTA_ENABLED` | `False` | ausente (`False`) | Desactivar el flag; las tablas conservan la auditoría de venta |

Ambos interruptores están pensados para que el rollback sea **un cambio de flag**, nunca la eliminación de una tabla.

### 5.2 Secuencia de despliegue y reversión

**Despliegue:**

1. `docker compose up -d` (el proxy es el único puerto publicado).
2. El backend espera a PostgreSQL, migra, recolecta estáticos y levanta gunicorn.
3. El frontend sirve el bundle horneado; `BACKEND_INTERNAL_URL` se resuelve en runtime.
4. Semillas y verificaciones **manualmente**, si la edición lo requiere.

**Reversión:** los tres interruptores (`PAGO_MANUAL_APROBACION_ENABLED`, `PASES_FIESTA_ENABLED`, `NEXT_PUBLIC_IZIPAY_ENABLED`) permiten desactivar capacidades sin tocar el esquema. La reversión del esquema no está automatizada.

### 5.3 Verificación mínima tras un despliegue

| # | Verificación | Flujo relacionado |
|---|---|---|
| 1 | `GET /proxy-health` responde `200 ok` | — |
| 2 | `GET /backend/catalogo/paquetes/` responde con el sobre `ApiResponse` esperado | Flujo 1 |
| 3 | `POST /backend/auth/login/{username}` y las 4 cookies quedan escritas | Flujo 3 |
| 4 | `GET /backend/inscripciones/` con cookie de sesión responde 200 y 401 sin ella | Flujo 11 |
| 5 | `POST /backend/pagos/izipay/confirmar` rechaza con 403 a un tercero | Flujo 16 |
| 6 | `GET /backend/pagos/transacciones/{id}` responde el estado persistido | Flujo 18 |
| 7 | `GET /backend/administracion/catalogos` responde los vocabularios de estado | Flujo 26 |
| 8 | `GET /backend/personas/busqueda/{dni}` responde con el scraper sano | Flujos 8 y 27 |

---

## 6. Hallazgos registrados (no corregidos)

Los nueve hallazgos siguientes están **constatados y registrados**. Ninguno se ha corregido en esta exploración. Se listan con evidencia, impacto y una indicación de decisión pendiente.

### H-1 — El cierre de sesión es exclusivamente del lado del cliente

| | |
|---|---|
| **Evidencia** | `frontend/src/app/api/auth/logout/route.ts` (8 líneas) llama `clearAuthCookies()` y **no invoca ningún endpoint del backend**. `frontend/src/lib/auth/actions.ts` → `clearAuthCookies()` borra las 4 cookies y nada más. `ninja_jwt` no expone un endpoint de logout. |
| **Consecuencia** | El refresh token **no se lista en la blacklist** al cerrar sesión. Con `ROTATE_REFRESH_TOKENS=True` y `BLACKLIST_AFTER_ROTATION=True`, la rotación lista el token *anterior*, pero el token vigente sigue siendo utilizable hasta que expira (7 días) o hasta la siguiente rotación. |
| **Impacto** | Una copia del refresh token capturada antes del logout permanece válida y utilizable. No se verificó que exista middleware o comando que lo liste. |
| **Naturaleza** | **Decisión de seguridad, no refactor.** Corregirlo implica un endpoint de backend, es decir un **cambio de la superficie congelada**. Debe decidirse **antes** de mover el código, no después. |
| **Decisión pendiente** | ¿Se acepta el logout exclusivamente del cliente? Si no, se añade `POST /api/auth/logout/blacklist` y se documenta en la lista de congelación. |

### H-2 — Tres definiciones divergentes de las mismas cuatro cookies

| Definición | `httpOnly` | `maxAge` access | `maxAge` refresh | `secure` |
|---|---|---|---|---|
| `lib/auth/cookies.ts` → `COOKIE_OPTIONS` + opciones derivadas | `false` | 30 d | 7 d | `NEXT_PUBLIC_COOKIE_SECURE === "true"` |
| `features/auth/hooks/useLogin.ts` (`persistAuthAndReturnUser`) | `false` | **7 d** | **7 d** | mismo criterio |
| `features/auth/hooks/useRegister.ts` (`persistAuthTokens`) | `false` | **7 d** | **7 d** | mismo criterio |

| | |
|---|---|
| **Evidencia adicional** | `app/api/auth/refresh/route.ts` línea 88 comenta *"Set rotated tokens as httpOnly cookies"*, pero las opciones aplicadas declaran `httpOnly: false`. `lib/auth/actions.ts` → `setAuthCookies()` (server action) existe pero **no se usa**: los escritores reales son los dos hooks de cliente. `lib/api.ts` y `app/api/auth/refresh/route.ts` tienen comentarios que describen cookies `httpOnly`, cuando el valor efectivo es `false`. |
| **Consecuencia** | El access token de la cookie vive 30 días si lo establece el refresh del servidor, y 7 días si lo establece el login del navegador. El logout borra las cookies por nombre, así que la discrepancia de `maxAge` no rompe el cierre de sesión, pero sí vuelve impredecible la ventana de validez percibida. |
| **Naturaleza** | **Inconsistencia de contrato.** El valor `httpOnly: false` es una decisión deliberada y documentada; lo que no lo es es que tres archivos distintos declaren el mismo conjunto de cookies con parámetros diferentes. |
| **Decisión pendiente** | Consolidar en una sola fuente (`lib/auth/cookies.ts`) o declarar explícitamente por qué los hooks de cliente usan una ventana de 7 días. |

### H-3 — Ambigüedad del puerto publicado del proxy

| | |
|---|---|
| **Evidencia** | Compose raíz: `${PROXY_PORT:-7000}`. `.env`: `PROXY_PORT=7000`. `.env.example`: `PROXY_PORT=7005`. `proxy/docker-compose.yml`: `8011:80` fijo, con `host.docker.internal` y su propio healthcheck. `frontend/Dockerfile`: `EXPOSE ${PORT:-7000}` frente a `PORT=3000` real. `SCRAPER_PORT=7004` no lo usa ningún servicio. |
| **Consecuencia** | Dos puntos de entrada al mismo `nginx.conf`; cuatro valores declarados para el mismo puerto. Un operador no puede deducir el puerto correcto sin leer tres archivos. |
| **Decisión pendiente** | Fijar **un** puerto canónico y **un** punto de entrada. Eliminar `proxy/docker-compose.yml` o declararlo como variante de desarrollo con su puerto documentado. |

### H-4 — El directorio `doc/` histórico describe una arquitectura que ya no existe

| Documento | Qué afirma | Realidad verificada |
|---|---|---|
| `doc/DEVELOPMENT.md` | "Entorno local con **SQLite** (no requiere Docker)", `npm run db:push:sqlite`, `npm run db:seed`, `npm run admin:create` | `frontend/package.json` **no tiene ningún script `db:*`, `seed` ni `admin:create`**. Scripts reales: `dev`, `build`, `start`, `lint`, `format`, `test`, `test:watch` |
| `doc/DEPLOYMENT.md` | "La aplicación es un **Next.js fullstack** […] **No existe un backend separado**", puertos `4000` y `5433`, `npm run db:seed`, roles `admin_comite`/`admin_finanzas` | **Es exactamente lo contrario**: hay un backend Django independiente, el compose publica solo el proxy (`7000`), y los roles del backend son los grupos de Django (`is_staff`/`is_superuser` + `core/capacidades.py`) |
| `doc/ENVIRONMENT.md` | Variables `DB_DIALECT`, `DATABASE_URL`, `DB_EXTERNAL_PORT=5433` | El contrato real es `DB_*` + `USE_SQLITE` + `SQLITE_PATH` + `NEXT_PUBLIC_*` + `BACKEND_INTERNAL_URL` + `SCRAPER_URL` |
| `doc/IZIPAY_MODULE.md` | Blueprint del 2026-09-21; su propio estado dice *"Salesianos FEST **aún NO**"* tiene el módulo | El módulo `modules/pagos/` **existe y está activo** (4 endpoints, 3 canales, orquestador, flujos, adaptador de liquidación) |
| `doc/BACKEND_DOMAIN_PLAN.md`, `doc/BACKEND_CREATEAPP_PLAN.md` | Planifican `modules.inscripciones` y una plantilla `modules.entidades` | Ninguno de los dos módulos existe con esos nombres |
| `doc_dev/DOCUMENTACION_LOGICA_Y_TABLAS_SALESIANOS_FEST.md` | Lógica y tablas del festival | Anterior a las tablas de competencias → ver [04 — Datos y dominio](./04-datos-y-dominio.md) |

| | |
|---|---|
| **Consecuencia** | Copiar `doc/` dentro de la raíz reconstruida propagaría una descripción falsa de la arquitectura. Un agente que lo lea puede concluir que el arranque local es un `npm run db:seed` sin Docker. Además, `.env.example` sigue titulado "CAM Environment Example" y activa banderas de depuración (`NEXT_PUBLIC_IS_TEST_UUID=true`, `NEXT_PUBLIC_DEBUG_GENERIC_FORM_ERRORS=true`) que un operador podría tomar como configuración válida. |
| **Reutilizables** | `doc/ADMINISTRACION_OPERATIVA_FEST.md` **sí** está vigente y coincide con `modules/administracion/`. `backend/README.md` y `backend/modules/competencias/README.md` son referencias válidas. |
| **Decisión pendiente** | Marcar el conjunto `doc/` como **deprecado** de forma explícita (cabecera de estado) o retirarlo. No copiar su contenido a la nueva raíz. |

### H-5 — El artefacto previo de inventario de rutas era incompleto

| | |
|---|---|
| **Evidencia** | El artefacto de exploración de backend (`sdd/explore/rebuild-backend-api-map`) construyó una tabla de rutas que **omitía por completo** `CompraController` (`/compras`, 5 rutas) y `AsignacionController` + `InscripcionSaldoController` (`/asignaciones`, 5 rutas). |
| **Consecuencia** | Una lista de verificación de reconstrucción derivada solo de ese artefacto habría omitido `POST /compras/{compra_id}/iniciar-pago` (**el inicio de pago que el navegador invoca**) y `POST /asignaciones/liberar` (**la liberación de cupo**), rompiendo los flujos 15 y 14 sin señal visible. |
| **Mitigación aplicada** | [05 — Flujos end-to-end](./05-flujos-end-to-end.md) § 3 contiene el inventario **extraído del código** (decoradores `@route.*` + `@api_controller`), no heredado del artefacto. § 4 documenta la omisión. |
| **Regla derivada** | El inventario de rutas se regenera desde `backend/config/api.py` cada vez que cambie. No se reutiliza un artefacto de exploración como fuente de verdad de rutas. |

### H-6 — Variables de entorno declaradas como `args` de build que el Dockerfile ignora

| Variable | Declarada como `args:` en el compose | ¿`ARG` en `frontend/Dockerfile`? | Efectivo |
|---|---|---|---|
| `NEXT_PUBLIC_AUTH_STORAGE_PREFIX` | Sí (`salesianos_auth`) | **No** — `ENV ... =salesianos_auth` literal | Fijo en la imagen; cambiarlo exige reconstruir |
| `NEXT_PUBLIC_FRONTEND_URL` | Sí | **No** — ausente del Dockerfile | No llega al bundle; además **no se referencia en `frontend/src/` ni en `next.config.ts`** (variable muerta en su totalidad) |

| | |
|---|---|
| **Consecuencia** | Un cambio de prefijo de cookies o de URL pública se aplicaría **solo** si además se reconstruye la imagen con el Dockerfile actualizado. El `.env` aparenta controlar esas variables, pero no es así. |
| **Decisión pendiente** | Declarar los `ARG` correspondientes, o retirar las variables del compose para que la configuración efectiva sea evidente. |

### H-7 — El árbol `Aplicacion/` contiene una copia parcial del backend

| | |
|---|---|
| **Evidencia** | `Aplicacion/backend/` contiene `config/`, `core/`, `docker/`, `scripts/`, `utils/`, `old_seed/`, `db.sqlite3` y `modules/__init__.py` — **pero no los módulos de negocio**. `Aplicacion/backend/config/api.py` importa controladores de `modules.usuarios`, `modules.pagos`, `modules.salesianos_fest`, `modules.competencias` y `modules.administracion`, que **no existen** en ese árbol. |
| **Consecuencia** | El backend de `Aplicacion/` no arranca. Además arrastra residuo heredado de otro proyecto: `old_seed/cam_db_20260811.{dump,sql}`, `utils/ubigeo.json`, `utils/ubigeo_constants.py`, `scripts/import_sqlite_to_postgres.py`, `scripts/strip_*_tests.py`, `diferencias_calculo.csv`, `check_*.py`, `fix_*.py`, `reporte_ingesta_legacy.{csv,xlsx}`. |
| **Nota** | Ninguno de esos archivos está cubierto por los flujos de [05](./05-flujos-end-to-end.md); el mapa de flujos **no** puede usarse para justificarlos. |
| **Decisión pendiente** | Copiar `backend/modules/` con lista de archivos (no copia de carpeta) y decidir la disposición del residuo: eliminar o archivar. |

### H-8 — Un controlador definido pero no registrado

| | |
|---|---|
| **Evidencia** | `backend/modules/usuarios/presentation/controllers/ingeniero_habilitado_controller.py` define `GET /ingenieros/habilitados/{cip}` (`auth=None`), pero `backend/config/api.py` **no lo registra** ni lo importa. |
| **Consecuencia** | La ruta **no existe en la API**. El cliente que la consuma recibiría 404. |
| **Decisión pendiente** | Registrar el controlador (cambio de superficie pública, con su flujo correspondiente) o eliminar el archivo como código muerto. |

### H-9 — Resolución de la URL base duplicada y divergente

| Cliente | Cómo resuelve la URL | ¿Usa `lib/server/backend-url.ts`? |
|---|---|---|
| `lib/api.ts` (axios) | `backendPublicUrl()` / `backendInternalUrl()` | **Sí** |
| `features/portada/hooks/useCatalogo.ts` | `NEXT_PUBLIC_API_URL` con fallback `http://backend:8000/api` **hardcodeado** | No |
| `features/landing/paquetes.service.ts` | `NEXT_PUBLIC_API_URL` con fallback `http://backend:8000/api` **hardcodeado** | No |

| | |
|---|---|
| **Consecuencia** | Los dos clientes de `fetch` crudo ignoran `BACKEND_INTERNAL_URL` y, en consecuencia, `admin.session.server.ts` y `proxy.ts` no son las únicas piezas que deciden a qué URL se habla con Django. Si el nombre interno del servicio o el prefijo de la API cambian, esos dos clientes se rompen de forma distinta al resto del sistema. Además, al no pasar por la instancia axios, **no heredan** la cabecera `Authorization`, el refresco proactivo ni el reintento tras 401, y no aplican el parser de errores estándar. |
| **Decisión pendiente** | Que todo cliente HTTP pase por `lib/api.ts` o por un cliente compartido que use `backendInternalUrl()`/`backendPublicUrl()`. |

---

## 7. Registro de deuda técnica

| # | Deuda | Ubicación | Tipo | Riesgo | Estado |
|---|---|---|---|---|---|
| D-1 | Logout sin invalidación del refresh token | `frontend/src/app/api/auth/logout/route.ts` | Seguridad | Alto | **Registrado (H-1)** |
| D-2 | Tres definiciones de las cookies de sesión | `lib/auth/cookies.ts`, `useLogin.ts`, `useRegister.ts` | Contrato | Medio | **Registrado (H-2)** |
| D-3 | Cuatro puertos declarados y dos entradas al proxy | `docker-compose.yml`, `.env`, `.env.example`, `proxy/docker-compose.yml`, `frontend/Dockerfile` | Operación | Medio | **Registrado (H-3)** |
| D-4 | `doc/` describe una arquitectura inexistente | `doc/DEVELOPMENT.md`, `doc/DEPLOYMENT.md`, `doc/ENVIRONMENT.md`, `doc/IZIPAY_MODULE.md` | Documentación | Medio | **Registrado (H-4)** |
| D-5 | Inventario de rutas incompleto en artefacto previo | artefacto Engram de exploración de backend | Documentación | Alto (si se reutiliza) | **Registrado (H-5)** — mitigado en [05](./05-flujos-end-to-end.md) § 3 |
| D-6 | `args:` de build ignorados por el Dockerfile | `frontend/Dockerfile`, `docker-compose.yml` | Configuración | Medio | **Registrado (H-6)** |
| D-7 | Copia parcial del backend y residuo heredado | `Aplicacion/backend/` | Estructura | Alto (arranque) | **Registrado (H-7)** |
| D-8 | Controlador no registrado | `ingeniero_habilitado_controller.py` | Funcional | Bajo | **Registrado (H-8)** |
| D-9 | Resolución de URL duplicada en dos clientes | `useCatalogo.ts`, `landing/paquetes.service.ts` | Arquitectura | Medio | **Registrado (H-9)** |
| D-10 | `Q_CLUSTER` configurado sin tareas ni consumidor | `backend/config/settings/base.py` | Configuración | Bajo | Registrado — sin acción prevista |
| D-11 | `modules.pagos.di.PagosModule` comentado en `INJECTOR_MODULES` | `backend/config/settings/base.py` | Configuración | Medio | Registrado — `IzipayClient` pierde el alcance singleton |
| D-12 | Dos respuestas sin tipar: `POST /inscripciones/{id}/personas` y `POST /inscripciones/{id}/pool/asignar` | `inscripcion_controller.py` | Contrato | Bajo | Registrado |
| D-13 | Invariantes de cupos y de slots solo en la capa de servicio | `asignacion_controller.py`, `pase_controller.py` | Integridad de datos | Medio | Registrado — sin restricción equivalente en base de datos |
| D-14 | `SECRET_KEY=change-me-in-production` en el `.env` real | `.env` (raíz) | Seguridad | **Crítico si este archivo llega a producción** | Registrado — **no verificado** si el entorno productive usa otro archivo |
| D-15 | Dos parametrizaciones del scraper: `python:3.11-slim` (worker) frente a `python:3.10-slim` (backend) | `worker/scraper/Dockerfile`, `backend/Dockerfile` | Consistencia | Bajo | Registrado |
| D-16 | `SCRAPER_PORT=7004` declarado y no usado | `.env`, `.env.example` | Configuración | Bajo | Registrado |

---

## 8. Referencias cruzadas

- [README — Índice de la documentación](./README.md) — punto de entrada navegable del conjunto documental.
- [00 — Cobertura y trazabilidad](./00-cobertura-y-trazabilidad.md) — metodología de auditoría, recuentos verificados y checklist reejecutable.
- [01 — Arquitectura y runtime](./01-arquitectura-y-runtime.md) — topología de cuatro niveles, tabla de enrutamiento nginx, las dos URLs base y la propiedad de las cookies.
- [02 — Backend y API](./02-backend-y-api.md) — arquitectura del servicio Django/Ninja.
- [02a — Inventario de endpoints](./02a-inventario-de-endpoints.md) — catálogo de rutas del backend.
- [02b — Propósito y consumidores de endpoints](./02b-proposito-y-consumidores-de-endpoints.md) — propósito, consumidor real y efectos de cada ruta.
- [03 — Frontend](./03-frontend.md) — arquitectura del frontend, rutas, features y transporte HTTP.
- [03a — Páginas públicas y de compra](./03a-paginas-publicas-y-compra.md) — ficha de cada pantalla no administrativa.
- [03b — Páginas administrativas y operativas](./03b-paginas-administrativas-y-operativas.md) — ficha de cada pantalla administrativa.
- [04 — Datos y dominio](./04-datos-y-dominio.md) — propiedad de datos, modelos, migraciones y fronteras de integración.
- [04a — Seeds y datos iniciales](./04a-seeds-y-datos-iniciales.md) — detalle de los 13 comandos de gestión y de los demás mecanismos de siembra.
- [05 — Flujos end-to-end](./05-flujos-end-to-end.md) — los 27 flujos verificados y el inventario de rutas extraído del código.
- [05a — Matriz página → flujo → endpoint → datos](./05a-matriz-pagina-flujo-endpoint-datos.md) — trazabilidad completa desde la pantalla hasta la base de datos.
- [07 — Guía para el agente de UI/UX](./07-guia-para-ui-ux.md) — qué puede y qué no puede cambiarse en el frontend, y cómo se entrega un cambio.
