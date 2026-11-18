# 04a - Seeds y datos iniciales

> **Estado:** provisional (documento derivado de una exploración de solo lectura).
> **Fuente de verdad del código:** `backend/` (rama `master`, commit `eb17e7b`).
> **Alcance:** todos los mecanismos de siembra, carga inicial, bootstrap y datos de referencia del repositorio —backend, frontend, worker, compose, scripts y assets— con su comportamiento real, sus dependencias y su riesgo.
> **Fecha de verificación:** 2026-11-18.
> **Destinatarios:** backend, operación, agentes que reconstruyan `Aplicacion/`.

## Convenciones de lectura

| Marcador | Significado |
|---|---|
| ✅ | **Verificado** en esta sesión contra el código, los archivos de migración o una lectura de solo lectura de la base SQLite (`mode=ro`). |
| 🔍 | **Supuesto** o inferido; plausible pero no comprobado contra una fuente primaria. |
| ⚠️ | **Brecha o conflicto** detectado, sin resolver en esta exploración. |

Precedencia de fuentes: **código > base de datos aplicada > contrato > documentación histórica**. Cuando un contrato y el código discrepan, este documento describe el código y señala la discrepancia.

**Método de lectura de la base:** `sqlite3.connect("file:<ruta>?mode=ro", uri=True)`. Ninguna sentencia de este documento modifica la base ni el código. Los scripts `check_*.py` y los comandos `verificar_*` / `auditar_*` se ejecutaron **solo por lectura de su código fuente**, no por invocación.

## Documentos hermanos

| Documento | Relación con este documento |
|---|---|
| [`README.md`](./README.md) | Índice navegable del conjunto documental. |
| [`00-cobertura-y-trazabilidad.md`](./00-cobertura-y-trazabilidad.md) | Auditoría de cobertura: recuentos verificados y checklist reejecutable. |
| [`01-arquitectura-y-runtime.md`](./01-arquitectura-y-runtime.md) | Topología de servicios y arranque. Establece que el `entrypoint.sh` no siembra nada. |
| [`04-datos-y-dominio.md`](./04-datos-y-dominio.md) | Propiedad de datos, modelos y migraciones. Este documento se especializa en **quién puebla esas tablas**. |
| [`06-operacion-y-deuda-tecnica.md`](./06-operacion-y-deuda-tecnica.md) | Topología operativa y registro de deuda. Su § 3.3 resume las semillas; este documento las detalla en profundidad y las audita. |
| [`02-backend-y-api.md`](./02-backend-y-api.md) | Superficie HTTP. Los comandos de gestión se listan en su § de comandos propios. |
| [`05a-matriz-pagina-flujo-endpoint-datos.md`](./05a-matriz-pagina-flujo-endpoint-datos.md) | Encadena cada flujo de pantalla con las tablas que escribe. |

Los contratos normativos son [`../../contract/`](../../contract/). Ninguno de los siete contratos leídos define un mecanismo de siembra: el contrato de arquitectura Django deja la decisión a cada módulo, y `PLAN_REFACTORIZACION.md` y `TEST_ARCHITECTURE_CONTRACT.md` no mencionan semillas de producción.

---

## 1. Panorama: qué mecanismos de siembra existen

✅ Verificado sobre `backend/`, `frontend/`, `worker/`, `proxy/`, `docker-compose.yml` y los siete archivos de `contract/`.

| # | Mecanismo | Ubicación | Dominio | Naturaleza | Estado |
|---|---|---|---|---|---|
| 1 | `create_admin` | `backend/core/management/commands/create_admin.py` | `core` | Siembra de superusuario | **Activo** |
| 2 | `seed_admin` | `backend/modules/usuarios/management/commands/seed_admin.py` | `usuarios` | Siembra de superusuario | **Activo y redundante** con #1 |
| 3 | `seed_catalogo_fest` | `backend/modules/salesianos_fest/management/commands/seed_catalogo_fest.py` | `salesianos_fest` + `eventos` | Siembra de catálogo comercial | **Activo — canónico** |
| 4 | `seed_commerce` | `backend/modules/commerce/management/commands/seed_commerce.py` | `commerce` + `pagos` + `salesianos_fest` + `usuarios` | Fixtures de compra | **Activo — solo desarrollo** |
| 5 | `reset_dev` | `backend/core/management/commands/reset_dev.py` | `core` | Reinicio destructivo de entorno | **Activo con opción rota** |
| 6 | `seed_colegiados` | `backend/modules/usuarios/management/commands/seed_colegiados.py` | `usuarios` | Siembra desde JSON CIP | ⚠️ **Muerto** (imports rotos + asset ausente) |
| 7 | `seed_perfiles_ingeniero_faltantes` | `backend/modules/usuarios/management/commands/seed_perfiles_ingeniero_faltantes.py` | `usuarios` | Siembra por llamada al CIP | ⚠️ **Muerto** (imports rotos + asset ausente) |
| 8 | `import_sqlite_to_postgres.py` | `backend/scripts/import_sqlite_to_postgres.py` | transversal | Migración de datos entre motores | ⚠️ **Residuo CAM** |
| 9 | `old_seed/cam_db_20260811.{dump,sql}` | `backend/old_seed/` | — | Dump de base de datos de CAM | ⚠️ **Residuo CAM** |
| 10 | `utils/ubigeo.json` + `utils/ubigeo_constants.py` | `backend/utils/` | — | Catálogo ubigeo del Perú | ⚠️ **Residuo CAM** (sin consumidor) |
| 11 | `FALLBACK_PAQUETES` | `frontend/src/components/landing/Paquetes.tsx` | frontend | Catálogo comercial estático | **Activo — espejo del seed #3** |
| 12 | `VENTAS` / `ORDEN_DISCIPLINAS` | `frontend/src/features/portada/config/festival.ts`, `.../hooks/useCatalogo.ts` | frontend | Calendario comercial y orden editorial | **Activo — duplica decisiones del seed** |
| 13 | Fixtures y factories de test | `backend/modules/*/tests/` | todos | Datos de prueba | **Activo — no es seed de runtime** |
| 14 | `pagos/0006_transpaccionpago_intento_activo_unico.py` | `backend/modules/pagos/migrations/` | `pagos` | Migración con **gate** de datos | **Activo — no siembra, condiciona** |
| 15 | `worker/scraper` | `worker/scraper/` | worker | Microservicio de consulta DNI/RUC | **Activo — no siembra** (solo lectura) |

### 1.1 Lo que NO existe (verificado por búsqueda exhaustiva)

| Mecanismo buscado | Resultado |
|---|---|
| `loaddata` / `FIXTURE_DIRS` / fixtures JSON de Django | **Sin coincidencias** en todo `backend/` |
| `RunPython` / `RunSQL` con creación de filas | **Una sola** ocurrencia: `pagos/0006`, que **valida** y no crea (#14) |
| Migraciones de datos por app | **Ninguna.** Los 6 directorios `migrations/` (`commerce` 4, `competencias` 2, `eventos` 3, `pagos` 7, `salesianos_fest` 16, `usuarios` 4) solo crean esquema |
| `entrypoint.sh` ejecutando `seed_*` | **No.** El arranque solo hace `migrate --noinput` + `collectstatic --noinput` + gunicorn |
| `docker-compose.yml` con servicio de seed | **No.** Los 5 servicios son `db`, `scraper`, `backend`, `frontend`, `proxy` |
| `npm run db:seed` / `db:push` / `admin:create` en el frontend | **No existen.** `frontend/package.json` solo declara `dev`, `build`, `start`, `lint`, `format`, `test`, `test:watch` |
| Directorio `backend/modules/*/seeds/` | **No existe.** Ninguna carpeta `seeds/` en el repositorio (excluyendo `.venv`) |
| Fixtures JSON/CSV de seed en el repositorio | **Ninguno.** El único JSON de datos es `backend/utils/ubigeo.json` (residuo CAM) |
| MSW / mock server / `faker` en el frontend | **Sin coincidencias.** No hay mocking por red |
| `seed_inscripciones` (comando documentado en `backend/README.md`) | ⚠️ **No existe** como archivo. Ver § 8, brecha B-1 |

### 1.2 Configuración que gobierna las semillas

| Variable / constante | Ubicación | Valor por defecto | Efecto sobre las semillas |
|---|---|---|---|
| `DEBUG` | `config/settings/base.py`, `development.py`, `test.py` | `False` / `True` / `True` | **Guarda de entorno de `seed_commerce`** (#4): se niega a correr con `DEBUG=False` |
| `USE_SQLITE` | `config/settings/base.py:182` | ausente → PostgreSQL | `development.py` solo usa SQLite si `USE_SQLITE` está activo |
| `DJANGO_SETTINGS_MODULE` | `docker-compose.yml:45` | `config.settings.production` | En producción `DEBUG=False` → `seed_commerce` se niega a correr |
| `EVENTO_ACTIVO_NOMBRE` | `config/settings/base.py:141` | `"Salesianos FEST 2026"` | **Debe coincidir** con el nombre de evento que crea `seed_catalogo_fest` (#3) |
| `CIP_USE_SIMULATOR` | `config/settings/development.py:51` / `test.py:24` | `False` / `True` | Irrelevante para #3 y #4; relevante solo para el comando muerto #7 |
| `EVENTO_ACTIVO_NOMBRE` ausente en `.env` | `.env` | usa el default | ⚠️ Una **segunda edición** exigiría cambiarlo; el seed #3 seguiría creando `"Salesianos FEST 2026"` fijo |

---

## 2. Fichas por mecanismo

### 2.1 `create_admin` — superusuario fijo de `core`

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/core/management/commands/create_admin.py` (96 líneas) |
| **Invocación** | `python manage.py create_admin --settings=config.settings.development` · `python manage.py create_admin --force` · en contenedor: `docker exec -it salesianos_backend uv run python manage.py create_admin` |
| **Dominio propietario** | `core` (núcleo compartido). Crea datos en `usuarios` (Persona + Usuario) y en `auth_permission` indirectamente. |
| **Propósito** | Materializar un superusuario determinista: `username=admin`, `password=admin`, DNI `00000000`, email `admin@example.com`, `is_staff=True`, `is_superuser=True`, `is_active=True`. |
| **Prerrequisitos y orden** | Solo requiere el esquema aplicado (`manage.py migrate`). **No depende de ninguna otra semilla.** Puede ejecutarse en cualquier momento. |
| **Modelos / tablas** | `usuarios.Persona` → tabla `usuarios_persona`; `usuarios.Usuario` → tabla `usuarios_usuario`. |
| **Registros creados** | 1 `Persona` (`tipo_documento=DNI`, `numero_documento=00000000`, nombres `Admin Sistema`, género `M`) + 1 `Usuario` (`username=admin`). |
| **Naturaleza de la escritura** | **Crea y actualiza.** `Persona.objects.update_or_create(tipo_documento=DNI, numero_documento=00000000, defaults={nombres, apellidos, genero})` y `Usuario.objects.update_or_create(username="admin", defaults={persona_fk, email, is_staff, is_superuser, is_active})`. Luego **siempre** ejecuta `user.set_password("admin")` + `user.save(update_fields=["password"])`. |
| **Idempotencia y riesgo de duplicados** | ✅ **Idempotente.** La clave de `update_or_create` es determinista (`DNI 00000000` / `username=admin`). No genera duplicados. **Riesgo real: reinicia la contraseña del admin en cada ejecución**, incluso si el operador la cambió — por eso existe `--force`, aunque `--force` **solo cambia el texto del log**, no el comportamiento: el código fija la contraseña siempre (`create_admin.py:73-74`). El flag `--force` es **decorativo**. |
| **Restricciones de entorno y seguridad** | ⚠️ **Ninguna.** No verifica `DEBUG`, ni entorno, ni perfil. Se puede ejecutar contra **producción**. Contraseña débil hardcodeada (`admin`/`admin`) y email ficticio (`admin@example.com`). Debe ejecutarse **solo** en desarrollo o ser seguido inmediatamente de un cambio de contraseña. |
| **Dependencias de usuarios / catálogos / eventos / configuración** | Ninguna. Es autocontenido. |
| **Evidencia de uso actual** | ✅ **Activo.** Documentado en `backend/README.md` § "Inicialización y Seeds" § 1, con el flag `--force` recomendado para resetear la contraseña. `reset_dev --with-admin` lo invoca (`reset_dev.py:234`). Estado actual en la base: el usuario `admin` existe con `is_staff=1`, `is_superuser=1`, `is_active=1`. |
| **Verificación segura** | `python manage.py shell -c "from modules.usuarios.domain.models import Usuario; u=Usuario.objects.get(username='admin'); print(u.email, u.is_staff, u.is_superuser, u.is_active, u.persona_fk.numero_documento)"` — solo lectura. Para comprobar la contraseña sin cambiarla: `u.check_password('admin')` (no escribe). |

### 2.2 `seed_admin` — superusuario fijo de `usuarios` (duplicado de `create_admin`)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/modules/usuarios/management/commands/seed_admin.py` (95 líneas) |
| **Invocación** | `python manage.py seed_admin` · `python manage.py seed_admin --username root --password secret123` · `--email` · `--dni` |
| **Dominio propietario** | `usuarios`. |
| **Propósito** | El mismo superusuario determinista que `create_admin`, con parametrización de `username`, `password`, `email` y `dni`. |
| **Prerrequisitos y orden** | Esquema aplicado. **Autocontenido**, como #1. |
| **Modelos / tablas** | `usuarios_persona`, `usuarios_usuario`. |
| **Registros creados** | 1 `Persona` (`numero_documento` = `--dni`, default `00000000`, nombres `Administrador Sistema`, género `M`) + 1 `Usuario` (`username` = `--username`, default `admin`). |
| **Naturaleza de la escritura** | **Crea y actualiza.** `Persona.objects.get_or_create(numero_documento=dni, ...)` (⚠️ **no** filtra por `tipo_documento`, a diferencia de `create_admin`) y `Usuario.objects.get_or_create(username=username, ...)`, seguido de `set_password` + `save()` sin `update_fields`. Envoltura en `@transaction.atomic`. |
| **Idempotencia y riesgo de duplicados** | ✅ **Idempotente** por `username` y por `numero_documento`. ⚠️ **Divergencia de clave con `create_admin`:** este comando busca la `Persona` **solo** por `numero_documento` (sin `tipo_documento`), mientras `create_admin` la busca por la pareja `(tipo_documento=DNI, numero_documento=00000000)`. Con el mismo DNI y distinto tipo de documento, los dos comandos **no se reconocen entre sí** y pueden crear **dos `Persona`** con el mismo número de documento, además de dos `Usuario` con el mismo `username` si difieren los parámetros. Con los valores por defecto (ambos `DNI`/`00000000`/`admin`) **no ocurre**: reutilizan las mismas filas. |
| **Restricciones de entorno y seguridad** | ⚠️ **Ninguna.** Ejecutable en producción. Acepta contraseña por línea de comandos (`--password secret123`), que queda expuesta en el historial del shell y en `ps`. Sin validación deRobustez de contraseña. |
| **Dependencias de usuarios / catálogos / eventos / configuración** | Ninguna. |
| **Evidencia de uso actual** | 🔍 **Activo pero sin evidencia de uso real.** Aparece en `sdd/admin-user-management/exploration.md` como segundo punto de creación del superusuario y en `Aplicacion/documentacion/06-operacion-y-deuda-tecnica.md` § 4.2. **No está documentado en `backend/README.md`** (que solo menciona `create_admin`). En la base actual el usuario `admin` tiene `email = admin@admin.com`, que **no coincide** ni con el default de `seed_admin` (`admin@salesianos.local`) ni con el de `create_admin` (`admin@example.com`) → el superusuario fue **editado después** por el admin de Django (`django_admin_log` tiene 1 entrada, `action_flag=2` = cambio). |
| **Verificación segura** | `python manage.py shell -c "from modules.usuarios.domain.models import Persona; print(list(Persona.objects.filter(numero_documento='00000000').values('id','tipo_documento','nombres')))"` — comprueba si hay una o dos `Persona` para el DNI del admin. |
| **Nota de diseño** | ⚠️ **Duplicación funcional.** Dos comandos con el mismo propósito, distinta clave de búsqueda y distinto email por defecto, en dos dominios distintos. Esto es exactamente lo que el `sdd/admin-user-management/exploration.md` ya señaló. |

### 2.3 `seed_catalogo_fest` — catálogo comercial del festival (CANÓNICO)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/modules/salesianos_fest/management/commands/seed_catalogo_fest.py` (431 líneas) |
| **Invocación** | `python manage.py seed_catalogo_fest` · `python manage.py seed_catalogo_fest --clear` ("Borra y recrea") |
| **Dominio propietario** | `salesianos_fest` (paquetes, promociones, categorías, disciplinas, pases) **y** `eventos` (el `Evento`). |
| **Propósito** | Materializar todo el catálogo comercial de la edición: evento, 56 promociones, 4 categorías, 4 disciplinas, 8 paquetes con sus precios y beneficios, y el pase de fiesta con sus dos precios. |
| **Prerrequisitos y orden** | 1. Esquema aplicado (`migrate`). 2. **Debe ejecutarse antes que `seed_commerce` (#4)**: este último lee `Evento` activo, `Paquete` activo, `PaqueteDisciplina`, `Promocion` activa y `PaquetePrecio` activo, y **aborta** si no los encuentra (`seed_commerce.py:94-107`). 3. No depende de ningún usuario. |
| **Modelos / tablas** | `eventos` · `promociones` · `categorias` · `disciplinas` · `paquetes` · `paquetes_precios` · `paquetes_beneficios` · `paquetes_disciplinas` · `pases` · `pases_precios`. (10 tablas.) |
| **Registros y categorías creados** | **Evento** (1): `nombre="Salesianos FEST 2026"`, `fecha_inicio=2026-11-15`, `fecha_fin=2026-11-20`, `esta_activo=True`. **Promociones** (56): una por año de 1970 a 2025, con el nombre derivado del rango etario — *Junior* 2012-2025, *Senior* 1998-2011, *Master* 1985-1997, *Super Master* 1970-1984; `activa=True`. **Categorías** (4): las 4 oficiales, con `promocion_desde`/`promocion_hasta` coincidentes con los rangos. Además **borra** las categorías obsoletas `Sub-14`, `Sub-16`, `Sub-18`, `Sub-20` del evento. **Disciplinas** (4): `F7M` Fútbol 7 Masculino (7-10 jugadores), `F7F` Fútbol 7 Femenino (7-10), `VOL` Vóley Mixto (6-8), `BAS` Básquet Masculino (5-10). **Paquetes** (8): `Reencuentro + Fiesta` (PACK/ELEGIBLE, mín. 10, S/40-50), `Pichanga + Fiesta` (PACK/FIJO, mín. 10, S/45-55), `Dúo + Fiesta Box` (PACK/ELEGIBLE, mín. 15, S/60-70), `Trío + Fiesta Box` (PACK/ELEGIBLE, mín. 20, S/60-70), `Fútbol 7 Masculino` (DISCIPLINA, mín. 7, S/40-50), `Fútbol 7 Femenino` (DISCIPLINA, mín. 7, S/40-50), `Vóley Mixto` (DISCIPLINA, mín. 6, S/40-50), `Básquet Masculino` (DISCIPLINA, mín. 5, S/40-50). **Beneficios** (8 filas): FIESTA/INDIVIDUAL/FIJO_INICIAL en Reencuentro y Pichanga; en Dúo y Trío: FIESTA/INDIVIDUAL/POR_CUPO, BOX/GRUPAL/FIJO_INICIAL y CERVEZA(6)/GRUPAL/FIJO_INICIAL. **Vínculos disciplina** (13 filas) reconciliados por paquete. **Pase** (1): `Pase de Fiesta`, `cantidad_maxima=0` (inventario ilimitado, centinela `CANTIDAD_MAXIMA_SIN_LIMITE`), **`activo=False`**, más `PasePrecio` PREVENTA S/25.00 y REGULAR S/35.00, ambos **`activo=False`**. |
| **Naturaleza de la escritura** | **Mixta: crea, actualiza y borra.** `@transaction.atomic` en `handle`. Con `--clear` **borra en cascada manual** `PaqueteBeneficio` → `PaquetePrecio` → `PaqueteDisciplina` → `Paquete` → `PasePrecio` → `Pase` → `Disciplina` → `Promocion` → `Categoria` → `Evento` (el orden respeta el `PROTECT` de `Pase.evento`). Sin `--clear`: `update_or_create` en `Promocion` (56), `Categoria` (4), `Paquete` (8), `PaquetePrecio` (16) y `PaqueteBeneficio` (8); `get_or_create` en `Evento` (1), `Disciplina` (4), `PaqueteDisciplina` (13) y `Pase` (1); **borrado** de las 4 categorías obsoletas; y **reconciliación** que borra los `PaqueteDisciplina` que no están en la lista oficial. |
| **Idempotencia y riesgo de duplicados** | ✅ **Idempotente por diseño**, con dos matices verificados: **(a)** `Evento` no tiene `UniqueConstraint` sobre `nombre` en el modelo (`eventos.Evento.Meta` solo define `db_table`, `ordering` y `verbose_name`), por lo que `get_or_create(nombre=...)` depende de un filtro no garantizado por la base: si existieran dos eventos con ese nombre, `get_or_create` lanzaría `MultipleObjectsReturned`; y una carga concurrente podría duplicar el evento. **(b)** El bloque del pase usa `get_or_create` **a propósito** (comentario explícito en `seed_catalogo_fest.py:41-47`): un pase que el operador ya activó o cuyos precios ajustó **no se sobrescribe ni se vuelve a inactivar**. ✅ **Re-ejecución segura por diseño**, pero con un efecto lateral comercial: `PaquetePrecio` se reescribe con `vigente_desde = date.today()` en **cada** ejecución, lo que **desplaza hacia adelante la ventana de precio PREVENTA** del paquete. Reejecutar el seed un mes después de la preventa reabre artificialmente la preventa con `vigente_desde` reciente. |
| **Restricciones de entorno y seguridad** | ⚠️ **Ninguna.** No verifica `DEBUG` ni entorno: **es ejecutable contra producción**. Es el único mecanismo del proyecto que **escribe precios de negocio**, y los precios son literales hardcodeados en el código fuente. `--clear` es **destructivo sobre datos de negocio**: borra el evento, todos los paquetes, todas las promociones y **todas las categorías** del sistema, no solo los del FEST 2026. Como `Evento.evento` es `PROTECT` en `Pase`, `Paquete` y `PaqueteDisciplina`, un `--clear` sobre una base con inscripciones registradas **falla con `ProtectedError`** y la transacción se revierte completa (es `@transaction.atomic`). El propio archivo advierte: *"Los montos son un supuesto de producto pendiente de confirmación"* (`seed_catalogo_fest.py:49`). |
| **Dependencias de usuarios / catálogos / eventos / configuración** | **No depende de usuarios.** Sí depende de: (i) el `Evento` — su nombre literal `"Salesianos FEST 2026"` **debe coincidir** con `EVENTO_ACTIVO_NOMBRE` de `config/settings/base.py:141`, porque el backend resuelve el evento activo por ese nombre y el frontend no envía `evento_id`; (ii) las 4 disciplinas que el seed crea, de las que el `Pase` y los paquetes dependen; (iii) las fechas de etapa del seed (`fecha_limite_preventa = 2026-10-31`), que **no coinciden** con el calendario comercial del frontend (§ 2.11). |
| **Evidencia de uso actual** | ✅ **Activo y con evidencia de ejecución.** Es el mecanismo más referenciado del proyecto: `backend/README.md` (§ "Cargar Promociones y Paquetes" — ⚠️ aunque allí con el nombre **incorrecto** `seed_inscripciones`), `sdd/salesianos-fest-fase-8-release/exploration.md` y `final-explore.md`, `Aplicacion/documentacion/06-operacion-y-deuda-tecnica.md` § 3.3, y 6 tests de integración que lo invocan (`test_catalogo.py`, `test_pase_catalogo.py`, `test_pase_compra.py`). Sus efectos son **verificables en la base actual**: `promociones` = 56 exactamente en el rango 1970-2025 y ninguna fuera de rango; `categorias` = 4 con los rangos oficiales; `disciplinas` = 4 (`F7M`/`F7F`/`VOL`/`BAS`); `paquetes` = 8 con los nombres y `minimo_compra_inicial` del seed; `paquetes_precios` = 16; `paquetes_beneficios` = 8; `paquetes_disciplinas` = 13; `eventos` = 1 con las fechas del seed. ⚠️ **Pero `pases` = 0 y `pases_precios` = 0**: el bloque del pase (añadido en el commit `eb17e7b`, 2026-10-28 18:58:51) **no se ha ejecutado contra esta base**. La base sí tiene aplicados los 4 esquemas de migraciones del pase (`salesianos_fest 0012`–`0015`), de modo que el catálogo de pases está **migrado pero vacío**. |
| **Verificación segura** | `python manage.py shell -c "from modules.salesianos_fest.domain.models import *; from modules.eventos.domain.models import Evento; print(Evento.objects.count(), Promocion.objects.count(), Categoria.objects.count(), Disciplina.objects.count(), Paquete.objects.count(), PaquetePrecio.objects.count(), PaqueteBeneficio.objects.count(), PaqueteDisciplina.objects.count(), Pase.objects.count(), PasePrecio.objects.count())"` — solo lectura. Para los precios vigentes: `python manage.py check_etapas.py` (script de solo lectura en `backend/`). |
| **Uso de las pruebas** | El propio archivo afirma *"Idempotente: usa get_or_create para no duplicar datos"*. La idempotencia está **cubierta por tests**: `test_catalogo.py::test_seed_catalogo_fest_idempotent` y `test_pase_catalogo.py::test_seed_catalogo_fest_crea_pase_inactivo_e_idempotente` invocan el comando dos veces y afirman que la segunda no crea registros nuevos. |

### 2.4 `seed_commerce` — fixtures de compra (SOLO DESARROLLO)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/modules/commerce/management/commands/seed_commerce.py` (425 líneas) |
| **Invocación** | `python manage.py seed_commerce` · `python manage.py seed_commerce --clear` (reset + re-siembra) |
| **Dominio propietario** | `commerce` (compras). **Cruza** `usuarios` (Persona), `pagos` (OrdenPago, TransaccionPago) y `salesianos_fest` (Inscripcion, Equipo, InscripcionPersona, CompraInscripcion, Promocion, Participacion, AsignacionCupo). |
| **Propósito** | Crear un ciclo de vida comercial de prueba: 3 responsables, inscripciones, equipos, y por cada uno **3 compras** que cubren los tres estados (`PENDIENTE`, `PAGADA`, `CANCELADA`), con su `OrdenPago` y su `TransaccionPago`. |
| **Prerrequisitos y orden** | 1. Esquema aplicado. 2. **`seed_catalogo_fest` (#3) debe ejecutarse antes**: el comando busca `Evento.objects.filter(esta_activo=True).first()` y `Paquete.objects.filter(evento=evento, activo=True).first()`; si no los encuentra imprime error y **termina sin sembrar** (`seed_commerce.py:94-107`). 3. No necesita usuarios previos: crea sus propias `Persona`. |
| **Modelos / tablas** | `usuarios_persona` · `inscripciones` · `equipos` · `inscripciones_personas` · `commerce_compra` · `salesianos_fest_compra_inscripcion` · `pagos_ordenpago` · `pagos_transaccionpago` · (lectura de `eventos`, `paquetes`, `paquetes_disciplinas`, `promociones`, `paquetes_precios`). |
| **Registros creados** | **3 `Persona`**: DNI `00000001` Juan Perez, `00000002` Maria Garcia, `00000003` Carlos Rodriguez — todos `tipo_documento=DNI`, `genero=M`, `telefono=999000001`. El prefijo `0000000` está declarado como constante `COMMERCE_TEST_DNI_PREFIX` y marca los datos de prueba. **Por cada persona**: 1 `Inscripcion` (estado `RECIBIDA`), 1 `Equipo` (estado `EQUIPO_ACTIVO`, nombre `Equipo <nombre>`), `InscripcionPersona` (estado `ACTIVO`), y **3 `Compra`**: `INICIAL`/`PENDIENTE` por `paquete.minimo_compra_inicial` unidades, `AMPLIACION`/`PAGADA` por 5 unidades, `AMPLIACION`/`CANCELADA` por 3 unidades — cada una con su `OrdenPago` (`ORD-<10 hex>`), su `CompraInscripcion` y, en el caso `PAGADA`, una `TransaccionPago` (`TXN-<DNI>-001`, `currency=PEN`, `status=EXITO`, `amount=total`). El `OrdenPago` pagada lleva `pagada_en=timezone.now()`; la `metadata` se filtra por `METADATA_ALLOWED_KEYS` (`source`, `inscripcion_id`, `paquete_id`, `paquete_nombre`, `evento_id`, `buyer_documento`, `buyer_nombres`, `buyer_apellidos`). |
| **Naturaleza de la escritura** | **Crea y actualiza.** `@transaction.atomic` en `handle`. Con `--clear` **borra** en orden de dependencia inverso: `Participacion` → `AsignacionCupo` → `CompraInscripcion` → `TransaccionPago` → `Compra` → `OrdenPago` → `InscripcionPersona` → `Equipo` → `Inscripcion` (`Compra.orden_pago` es `PROTECT`, por eso `Compra` va antes que `OrdenPago`). Sin `--clear`: `get_or_create` en `Persona`, `Inscripcion`, `Equipo`, `InscripcionPersona`, `TransaccionPago`, `Compra`, `OrdenPago` y `CompraInscripcion`; y **actualiza** la `OrdenPago` existente (metadata + backfill de `pagada_en`). |
| **Idempotencia y riesgo de duplicados** | ✅ **Idempotente en el caso normal**, y verificado con tests (`test_seed_commerce_idempotent_second_run_creates_no_new_records`, `..._idempotent_three_personas_each_with_three_compras`). ⚠️ **Dos matices verificados en el código**: **(a)** La clave de `Compra` es `(estado, total, referencia_externa)`. Si el precio unitario del paquete cambia entre dos ejecuciones (por ejemplo, porque se reejecutó `seed_catalogo_fest`, que reescribe `PaquetePrecio`), el `total` cambia y la misma `referencia_externa` **crea una compra duplicada** en lugar de reutilizarse. **(b)** ⚠️ **Defecto real:** el bucle de `InscripcionPersona` itera 3 veces (`for i in range(cantidad)` con `cantidad = 3`) pero **siempre con la misma `persona`**, y `get_or_create(inscripcion=..., persona=...)` resuelve contra el `UniqueConstraint("unique_inscripcion_persona", fields=["inscripcion", "persona"])`. Resultado: **se crea 1 sola `InscripcionPersona` por inscripción, no 3**; los iterations 2 y 3 recuperan la fila existente y no imprimen log. El código aparenta crear 3 participantes y crea 1. **No es un riesgo de duplicación sino un defecto de cobertura de datos.** |
| **Restricciones de entorno y seguridad** | ✅ **Único comando con guarda de entorno real**: `_check_development_environment()` aborta con `SystemExit` si `settings.DEBUG` es `False` (`seed_commerce.py:65-75`). El mensaje redirige a "migration scripts or deployment tooling". En el compose de producción `DJANGO_SETTINGS_MODULE=config.settings.production` → `DEBUG=False` → el comando **no puede ejecutarse**. Su docstring lo declara: *"DEVELOPMENT-ONLY"*. ⚠️ Advertencia adicional: `--clear` **borra TODAS las compras, órdenes de pago, transacciones, inscripciones, equipos y participaciones de la base**, no solo las del prefijo `0000000` — el borrado es global, aunque el filtro de "datos de prueba" solo exista para las `Persona`. **Es el comando más destructivo del proyecto.** |
| **Dependencias de usuarios / catálogos / eventos / configuración** | Depende del **catálogo** (#3): `Evento` activo, `Paquete` activo, `PaqueteDisciplina` (para obtener la `Disciplina`), `Promocion` activa y `PaquetePrecio` activo. Si no hay `Promocion` activa, **crea una de respaldo** con `get_or_create(anio=<año actual>, defaults={"nombre": "Senior", "activa": True})` — una promoción con el **nombre fijo "Senior"** para un año que normalmente sería *Junior*, *Master* o *Super Master*. Si no hay `PaquetePrecio` activo, usa el literal `Decimal("40.00")`. No depende de usuarios previos ni de configuración de entorno más allá de `DEBUG`. |
| **Evidencia de uso actual** | ✅ **Activo, con evidencia de ejecución en la base actual.** Las compras con `referencia_externa` `INIT-0000000{1,2,3}-001`, `AMP-0000000{1,2,3}-001` y `AMP-0000000{1,2,3}-002` (9 filas) corresponden exactamente al patrón del seed, y las 3 `Persona` con DNI `00000001/2/3` existen con los nombres y teléfonos del seed. Las 3 inscripciones en estado `RECIBIDA` (de un total de 12: 9 en `BORRADOR`) son las del seed. El resto de las 18 compras (`FEST-<8 hex>`) provienen del flujo real de la aplicación, no del seed — el seed **no duplicó** compras en la práctica. Cubierto por 12 tests en `backend/modules/commerce/tests/integration/test_seed_commerce.py`. |
| **Verificación segura** | `python manage.py shell -c "from modules.commerce.domain.models import Compra; from modules.usuarios.domain.models import Persona; print(list(Compra.objects.filter(referencia_externa__startswith='INIT-').values('referencia_externa','estado','total')))"` — solo lectura. Para aislar las filas del seed: `referencia_externa__startswith__in=['INIT-','AMP-']` y `Persona.objects.filter(numero_documento__startswith='0000000')`. |

### 2.5 `reset_dev` — reinicio destructivo del entorno de desarrollo

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/core/management/commands/reset_dev.py` (279 líneas) |
| **Invocación** | `python manage.py reset_dev --settings=config.settings.development` (dry-run por defecto) · `--yes` (ejecuta) · `--migrations` `--cache` `--database` `--all` · `--skip-migrate` · `--with-admin` · `--with-real-seed` |
| **Dominio propietario** | `core`. |
| **Propósito** | Utilidad de reinicio local: borra migraciones locales, caché de Python y el estado de la base de datos de desarrollo. |
| **Prerrequisitos y orden** | Esquema aplicado. Es un **orquestador**: llama internamente a `create_admin` (#1) y a `seed_real_all`. |
| **Modelos / tablas** | No es un siembro directo: borra el **archivo** SQLite completo (`db.sqlite3`) o hace `flush` en bases no-SQLite, y luego reconstruye el esquema con `migrate --run-syncdb --noinput`. |
| **Registros creados** | Ninguno propio. Delega: `--with-admin` → `create_admin` (#1); `--with-real-seed` → `seed_real_all` (⚠️ **no existe**, ver § 8, brecha B-2). |
| **Naturaleza de la escritura** | ⚠️ **Puramente destructiva.** Sin `--yes` es **dry-run**: no borra nada y solo informa. Con `--yes`: borra los archivos `migrations/*.py` de las apps locales (`core` y `modules.*`), borra `__pycache__` y `.pyc`/`.pyo`, y **borra el archivo SQLite** (o ejecuta `flush --noinput` en PostgreSQL). Cuando también borra migraciones, desactiva `MIGRATION_MODULES` para las apps locales y reconstruye con `--run-syncdb`. |
| **Idempotencia y riesgo de duplicados** | ✅ **Idempotente** (repetir el reinicio produce el mismo estado). No hay riesgo de duplicados: no inserta filas. ⚠️ **Riesgo de pérdida**: borra **toda** la base de desarrollo, incluidas las 26 `Persona`, 18 `Compra` y 12 `Inscripcion` que hoy hay en `backend/db.sqlite3`. |
| **Restricciones de entorno y seguridad** | ✅ **Guarda de entorno real**: `raise CommandError` si no está en un settings de desarrollo (`settings.DEBUG` o `DJANGO_SETTINGS_MODULE` que termine en `.development`). Además, para SQLite **verifica que la ruta de la base esté dentro del `BASE_DIR` del backend** y aborta si está fuera (`_sqlite_db_path`, `reset_dev.py:249-261`). Es el único comando del proyecto con doble protección (entorno + ruta). ⚠️ El borrado de migraciones locales es **irreversible para el historial**: se deben regenerar con `makemigrations`. |
| **Dependencias de usuarios / catálogos / eventos / configuración** | Depende de `settings.BASE_DIR`, `settings.DATABASES`, `settings.MIGRATION_MODULES` y del registro de apps. |
| **Evidencia de uso actual** | ✅ **Activo.** Introducido en el commit `fe38f3c`. Es la herramienta canónica de "empezar de cero" y está implícitamente en `backend/README.md` (sección "Inicialización y Seeds": *"Para inicializar el sistema desde cero ... es necesario cargar los datos base (seeds)"*). ⚠️ Su uso real es **improbable**: el README **no lo menciona**, y suBandera más relevante (`--with-real-seed`) está rota. |
| **Verificación segura** | `python manage.py reset_dev --settings=config.settings.development` **sin `--yes`**: dry-run que enumera qué borraría. Es el único comando del proyecto cuyo modo seguro es el valor por defecto. Para auditar sin ejecutar: `python manage.py reset_dev --settings=config.settings.development --database` (sigue siendo dry-run). |

### 2.6 `seed_colegiados` — siembra de colegiados CIP (⚠️ MUERTO)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/modules/usuarios/management/commands/seed_colegiados.py` (148 líneas) |
| **Invocación** | `python manage.py seed_colegiados --settings=config.settings.development` · `--dry-run` · `--seed-path <ruta>` |
| **Dominio propietario** | `usuarios`. |
| **Propósito declarado** | Sembrar `PerfilIngeniero` + `EspecialidadIngeniero` + `Capitulo` + `IngenieroHabilitacion` desde `seeds/colegiados_reales.json`, materializado desde el endpoint CIP. |
| **Prerrequisitos y orden** | ⚠️ **Insatisfechos e insatisfacibles.** El comando **no puede cargarse**. |
| **Modelos / tablas** | Pretendidos: `PerfilIngeniero`, `Capitulo`, `EspecialidadIngeniero`, `IngenieroHabilitacion`. |
| **Entradas y registros** | `SEEDS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "liquidaciones" / "seeds"` → `backend/modules/liquidaciones/seeds/colegiados_reales.json`. ⚠️ **La ruta no existe**: no hay módulo `liquidaciones` ni directorio `seeds/` en el repositorio. El comando terminaría con `No se encontró <ruta>` si llegara a ejecutarse. |
| **Naturaleza de la escritura** | Pretendida: crea (`get_or_create` por `cip` para el perfil; `get_or_create` por `registro_id` para capítulo; `get_or_create` por `(codigo, capitulo)` para especialidad) y **actualiza** (el bloque `if not was_created` reescribe todos los campos del perfil y lo guarda). `IngenieroHabilitacion` con `update_or_create(perfil_ingeniero=..., fecha_busqueda=None)` — `fecha_busqueda=None` significa "registro actual", por lo que **cada ejecución crea una fila nueva** de habilitación si cambian los datos: **el modelo sí acumula histórico por fecha_busqueda, y el seed no es idempotente en esa tabla**. |
| **Idempotencia y riesgo de duplicados** | ⚠️ **Irrelevante: el comando es inejecutable.** En abstracto, `get_or_create` por `cip` es idempotente para el perfil, pero `IngenieroHabilitacion` **no lo es** (véase arriba). |
| **Restricciones de entorno y seguridad** | ⚠️ **Ninguna.** Ni guarda de `DEBUG`, ni validación del asset. EscribIRía datos personales (DNI, nombres, correos, dirección, ubigeo) en una base de producción sin ninguna freno. |
| **Dependencias de usuarios / catálogos / eventos / configuración** | Depende de los modelos `Capitulo`/`PerfilIngeniero`/`IngenieroHabilitacion` y del asset JSON. |
| **Evidencia de uso actual** | ⚠️ **MUERTO — residuo de otro proyecto (CAM/CIP).** Tres fallos independientes, todos verificados: **(1)** `backend/modules/usuarios/domain/models/perfil_ingeniero.py` contiene **únicamente un docstring de deprecación** ("*All CIP-specific models have been removed from the active app*"); no define ninguna clase. El import `from ...perfil_ingeniero import (Capitulo, EspecialidadIngeniero, PerfilIngeniero, IngenieroHabilitacion)` **falla con `ImportError` al cargar el comando**. **(2)** El directorio `backend/modules/liquidaciones/seeds/` **no existe**. **(3)** `PerfilIngeniero` tampoco es un modelo gestionado: no hay tabla `perfil_ingeniero` en `backend/db.sqlite3`. Además, `backend/modules/usuarios/admin/catalogo_admin.py` y `perfil_admin.py` registran `ModelAdmin` para esos mismos modelos inexistentes, pero **no están importados** por `admin/__init__.py` (que solo importa `UsuarioAdmin`), por lo que el arranque del admin no se rompe: son archivos muertos que nadie carga. `doc/USUARIOS_MODULE_EXPLORE.md` los documenta todavía como activos — documentación obsoleta. |
| **Verificación segura** | Comprobar que no es ejecutable sin tocar datos: `python manage.py seed_colegiados --help` (falla con `ImportError` antes de tocar la base). Comprobar el estado del modelo: `python manage.py shell -c "from django.apps import apps; print(apps.get_app_config('usuarios').get_models())"`. |
| **Recomendación** | Eliminar el comando, `perfil_ingeniero.py`, `catalogo_admin.py`, `perfil_admin.py` y `perfil_ingeniero_core_service.py` (que también importa los modelos inexistentes), o marcarlos de forma explícita. No son ejecutables: son trampas de mantenimiento. |

### 2.7 `seed_perfiles_ingeniero_faltantes` — siembra de perfiles por llamada al CIP (⚠️ MUERTO)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/modules/usuarios/management/commands/seed_perfiles_ingeniero_faltantes.py` (384 líneas) |
| **Invocación** | `python manage.py seed_perfiles_ingeniero_faltantes --settings=config.settings.development` · `--cips=243475,065257,095196` · `--delegados-seed <ruta>` · `--inspectores-seed <ruta>` · `--dry-run` · `--retries 3` · `--delay 0.1` · `--force` |
| **Dominio propietario** | `usuarios`. |
| **Propósito declarado** | Crear `PerfilIngeniero` para los CIPs que aparecen en `delegados_reales.json` / `inspectores_reales.json` pero que nunca se materializaron en `colegiados_reales.json`, consultando cada CIP en la API del CIP. |
| **Prerrequisitos y orden** | ⚠️ **Insatisfechos e insatisfacibles.** El comando **no puede cargarse**. |
| **Modelos / tablas** | Pretendidos: `PerfilIngeniero`, `Capitulo`, `IngenieroHabilitacion`. |
| **Entradas y registros** | `SEEDS_DIR` apunta a `backend/modules/liquidaciones/seeds/` (**inexistente**); defaults `delegados_reales.json` e `inspectores_reales.json` (**inexistentes**). En modo `--cips`, no necesita archivos: normaliza los CIP a 6 dígitos con ceros a la izquierda y los consulta en `RealCipClient.get_colegiado(cip)`. |
| **Naturaleza de la escritura** | Pretendida: **crea** (`PerfilIngeniero.objects.create(**perfil_fields)`) y, con `--force`, **actualiza** los existentes. `Capitulo` con `update_or_create(registro_id=...)`, `IngenieroHabilitacion` con `update_or_create(perfil_ingeniero=..., fecha_busqueda=None)`. **A diferencia de `seed_colegiados`, este comando sí realiza llamadas de red** (con reintento exponencial y rate-limiting por `--delay`). |
| **Idempotencia y riesgo de duplicados** | ⚠️ **Irrelevante: el comando es inejecutable.** En abstracto: sin `--force`, los perfiles existentes se saltan (`return existing, False`) → idempotente; con `--force` se sobrescriben. `IngenieroHabilitacion` volvería a acumular filas por `fecha_busqueda`. |
| **Restricciones de entorno y seguridad** | ⚠️ **Ninguna.** No hay guarda de `DEBUG`. Es el único mecanismo del proyecto que **haría peticiones salientes a un servicio externo** (el CIP) y **escribiría datos personales** (DNI, nombre completo, correo, dirección, ubigeo) sin ninguna freno de entorno. En `development.py` el simulador está desactivado (`CIP_USE_SIMULATOR = False`), de modo que apuntaría al CIP real. |
| **Dependencias de usuarios / catálogos / eventos / configuración** | Depende de `RealCipClient` (servicio externo), de los modelos `PerfilIngeniero`/`Capitulo`/`IngenieroHabilitacion` y de los assets JSON. |
| **Evidencia de uso actual** | ⚠️ **MUERTO — residuo CAM/CIP.** Tres fallos verificados: **(1)** El import `from modules.usuarios.domain.models.perfil_ingeniero import PerfilIngeniero` **falla** (el módulo solo tiene el docstring de deprecación). **(2)** El import `from modules.usuarios.domain.services.core.perfil_ingeniero_core_service import PerfilIngenieroCoreService` **falla en cascada**: ese servicio importa `from modules.usuarios.domain.models.perfil_ingeniero import PerfilIngeniero, Capitulo`. **(3)** El import `from modules.usuarios.infrastructure.services import (RealCipClient, CipServiceUnavailableError)` **falla**: en `backend/modules/usuarios/infrastructure/services.py` **no existe ninguna clase `RealCipClient` ni `CipServiceUnavailableError`** (las únicas clases son `ConsultaExternaSimulator` e `RealConsultaExternaClient`). En total, **tres imports rotos** en el mismo archivo. `doc/USUARIOS_MODULE_EXPLORE.md` § "Mapa de seeds" lo describe aún como activo. |
| **Verificación segura** | `python manage.py seed_perfiles_ingeniero_faltantes --help` (falla con `ImportError` antes de tocar la base o la red). Para confirmar la ausencia de los símbolos: buscar `RealCipClient` en `backend/modules/usuarios/` → sin coincidencias. |
| **Recomendación** | Eliminar junto con #2.6 y los archivos de modelo dead asociados. |

### 2.8 `import_sqlite_to_postgres.py` — migración de datos entre motores (⚠️ RESIDUO CAM)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/scripts/import_sqlite_to_postgres.py` (120 líneas) |
| **Invocación** | `SQLITE_IMPORT_PATH=<ruta.sqlite3> SQLITE_IMPORT_REPORT=<salida.json> python scripts/import_sqlite_to_postgres.py` (usa `config.settings.production` por defecto) |
| **Dominio propietario** | Transversal — recorre `apps.get_models()` e importa **todos** los modelos gestionados salvo `contenttypes.ContentType` y `auth.Permission`. |
| **Propósito** | Volcar el contenido de una base SQLite a PostgreSQL: `flush` del destino, `bulk_create` por modelo, `SET session_replication_role = replica` para desactivar triggers, y `sequence_reset_sql` para realinear las secuencias. |
| **Prerrequisitos y orden** | Base SQLite origen existente y legible; base destino con el esquema ya aplicado (`migrate`); variables `SQLITE_IMPORT_PATH` / `SQLITE_IMPORT_REPORT`; permiso de escritura en la base destino. |
| **Modelos / tablas** | **Todos los modelos gestionados** de las apps instaladas (en el árbol actual: `usuarios`, `eventos`, `salesianos_fest`, `commerce`, `pagos`, `competencias` + framework). Genera un informe JSON por modelo con `status` (`loaded` / `skipped`), `count` y `reason`. |
| **Registros creados** | Todos los registros de la base origen. Se salta los modelos cuya tabla no exista en SQLite o a los que les falten columnas requeridas (`missing_required_columns`). |
| **Naturaleza de la escritura** | ⚠️ **Destruye y reconstruye:** `call_command("flush", interactive=False)` **borra la base destino por completo** antes de importar. |
| **Idempotencia y riesgo de duplicados** | ⚠️ **No idempotente en el sentido de "sin efectos":** cada ejecución hace `flush` y luego importa. Solo es idempotente si se repite sobre el mismo par origen/destino y el destino está limpio (lo garantiza el `flush`). ⚠️ `bulk_create` **no respeta `auto_now_add`/`auto_now`** de forma fiable en algunos casos y **no dispara señales `pre_save`/`post_save`** → los campos de auditoría de `BaseModel` (`created_at`, `updated_at`) viajan como los que tuviera el origen, y los efectos colaterales de `save()` quedan fuera. Riesgo real si se usa como procedimiento de producción en lugar de una migración única. |
| **Restricciones de entorno y seguridad** | ⚠️ **Ninguna.** Usa `config.settings.production` por defecto y **hace `flush` de la base de producción** sin confirmar nada (`interactive=False`). No hay `--dry-run`, ni verificación del origen, ni respaldo. **Es la operación más destructiva de todo el repositorio.** |
| **Dependencias de usuarios / catálogos / eventos / configuración** | Depende de `DJANGO_SETTINGS_MODULE` (default `production`), de `SQLITE_IMPORT_PATH` y `SQLITE_IMPORT_REPORT`. |
| **Evidencia de uso actual** | ⚠️ **Residuo CAM.** Ya está señalado como residuo en `Aplicacion/documentacion/04-datos-y-dominio.md` § 1.2 y § 6. Es una **herramienta de migración de un proyecto anterior** (el nombre `cam_db_*` de `old_seed/` y los 114 tablas CAM mentioned en el mismo documento lo confirman). No aparece en `backend/README.md` ni en la documentación operativa vigente. ⚠️ **Peligro residual:** permanece ejecutable y `flush` es irreversible; quien lo descubra por `ls scripts/` podría ejecutarlo contra producción por error. |
| **Verificación segura** | **No hay ejecución segura.** Solo puede inspeccionarse el código. Un `--dry-run` no existe. La única forma de probarlo es sobre bases desechables: un SQLite temporal y un PostgreSQL de prueba, nunca con `DJANGO_SETTINGS_MODULE=config.settings.production`. |
| **Recomendación** | Retirar del árbol o mover a `scripts/legacy/` con un `README` que explique que es un residuo no soportado. Alternativa: añadir un `--dry-run` y un guard de entorno. |

### 2.9 `old_seed/cam_db_20260811.{dump,sql}` — dump de base de datos de CAM (⚠️ RESIDUO CAM)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/old_seed/cam_db_20260811.dump` y `backend/old_seed/cam_db_20260811.sql` (presentes en `backend/` y en la copia `Aplicacion/backend/old_seed/`) |
| **Invocación** | ⚠️ **Ninguna documentada.** `pg_restore -d <db> cam_db_20260811.dump` o `psql -d <db> -f cam_db_20260811.sql`. |
| **Dominio propietario** | Ninguno: pertenece al proyecto CAM, no a Salesianos FEST. |
| **Propósito** | Conservar el estado de la base de datos del proyecto CAM en la fecha 2026-08-11, presumably como respaldo antes del refactor. |
| **Modelos / tablas** | Las 114 tablas CAM (`entidades_*`, `finanzas_*`, `liquidaciones_*`, etc.), según `Aplicacion/documentacion/04-datos-y-dominio.md` § 1.2. **Ninguna coincide con el esquema actual de Salesianos.** |
| **Naturaleza de la escritura** | ⚠️ **Si se restaura, es una sobrescritura completa** de la base destino con un esquema incompatible. |
| **Restricciones de entorno y seguridad** | ⚠️ **Ninguna.** Un `pg_restore` sin `--clean` sobre una base con el esquema actual fallará por objetos existentes; con `--clean` borra el esquema actual. Es un artefacto con **capacidad de destruir el esquema de producción** si alguien lo restaura por error. |
| **Evidencia de uso actual** | ⚠️ **Residuo CAM inerte.** No hay ningún script, comando ni compose que lo invoque. Ya señalado como residuo en `Aplicacion/documentacion/04-datos-y-dominio.md` § 1.2 y § 6. |
| **Verificación segura** | Inspección del encabezado del `.sql` para leer el esquema, sin ejecutar nada: `Get-Content backend/old_seed/cam_db_20260811.sql -TotalCount 40`. |
| **Recomendación** | Retirar del árbol o archivar fuera del repositorio. Su valor real es histórico (procede del refactor de CAM), no operativo. |

### 2.10 `utils/ubigeo.json` + `utils/ubigeo_constants.py` — catálogo ubigeo (⚠️ RESIDUO CAM, sin consumidor)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/utils/ubigeo.json` (196 994 bytes) y `backend/utils/ubigeo_constants.py` (constante `UBIGEO` en Python). Copias idénticas en `Aplicacion/backend/utils/`. |
| **Invocación** | Ninguna. `ubigeo.json` es la **fuente** de la que `ubigeo_constants.py` fue generado ("*GENERATED FILE — do not edit manually / Source: utils/ubigeo.json*"). |
| **Dominio propietario** | Ninguno en Salesianos FEST. Es un catálogo de ubigeos del Perú (departamento → provincia → distrito, con `ubigeo`, `id` e `inei`). |
| **Propósito** | Referencia geográfica. En CAM servía para el módulo de liquidaciones. |
| **Modelos / tablas** | **Ninguna.** No hay tabla `ubigeo` ni `ubigeo_departamento` en `backend/db.sqlite3` (verificado en el inventario de 56 tablas). |
| **Naturaleza de la escritura** | **Ninguna en tiempo de ejecución.** Es un asset estático. |
| **Idempotencia y riesgo de duplicados** | No aplica. |
| **Restricciones de entorno y seguridad** | No aplica. |
| **Dependencias** | Ninguna en el código vigente. ✅ La **única** referencia a `ubigeo.json` en todo `backend/` es el **comentario de provenance** de `ubigeo_constants.py:2`. No hay ningún `import` de `ubigeo_constants` ni ninguna lectura del JSON: se verificó que el único archivo que menciona la ruta es el propio comentario. |
| **Evidencia de uso actual** | ⚠️ **Residuo CAM muerto.** Ya señalado en `Aplicacion/documentacion/04-datos-y-dominio.md` § 1.2 y § 6 como parte del residuo heredado. |
| **Verificación segura** | `Select-String -Path "backend\**\*.py" -Pattern "ubigeo"` — devuelve solo el comentario de provenance y `ubigeo_constants.py`. |
| **Recomendación** | Retirar o archivar. Si en el futuro se necesita ubigeo, debe ser un modelo + migración + comando de seed propio, no una constante Python de 197 KB. |

### 2.11 `FALLBACK_PAQUETES` — catálogo comercial estático del frontend

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `frontend/src/components/landing/Paquetes.tsx:135-272` (constante `FALLBACK_PAQUETES`, con los ayudantes `crearPaqueteFallback` y `crearPrecios`). Copia equivalente en `Aplicacion/frontend/`. |
| **Invocación** | No es un comando. Se activa **automáticamente**: `const paquetesVisibles = paquetes && paquetes.length > 0 ? paquetes : FALLBACK_PAQUETES;` (`Paquetes.tsx:276-277`). Es decir, **si la API devuelve cero paquetes, la landing muestra el catálogo estático**. |
| **Dominio propietario** | Frontend, feature `landing`. |
| **Propósito** | Evitar una landing vacía si el backend no tiene catálogo sembrado o no responde. |
| **Prerrequisitos y orden** | Ninguno. Es una constante de compilación. |
| **Modelos / tablas** | Ninguna. Es un array de objetos con la forma del contrato `Paquete` del frontend (`frontend/src/features/landing/paquetes.service.ts`). |
| **Registros creados** | **8 paquetes**, con los **mismos nombres, tipos, modos, mínimos y precios** que crea `seed_catalogo_fest` (#3): Reencuentro + Fiesta (40/50, ELEGIBLE, 1 disciplina, F7F+VOL+BAS), Pichanga + Fiesta (45/55, FIJO, F7M), Dúo + Fiesta Box (60/70, ELEGIBLE, 2, VOL+BAS), Trío + Fiesta Box (60/70, ELEGIBLE, 3, F7M+VOL+BAS), Fútbol 7 Masculino (40/50), Fútbol 7 Femenino (40/50), Vóley Mixto (40/50), Básquet Masculino (40/50). Con **4 disciplinas** (`F7M`, `F7F`, `VOL`, `BAS`, con ids `fallback-*`), **4 beneficios** (`FIESTA_FIJO`, `FIESTA_POR_CUPO`, `BOX`, `CERVEZA` de cantidad 6) y **2 etapas de precio** por paquete con `vigente_desde="2026-10-19"` / `vigente_hasta="2026-10-31"` para PREVENTA y `vigente_desde="2026-10-31"` / `vigente_hasta=null` para REGULAR. `evento_id` sintético: `"fallback-salesianos-fest-2026"`. |
| **Naturaleza de la escritura** | **Ninguna.** No escribe en la base ni en ningún almacenamiento. Solo renderiza. |
| **Idempotencia y riesgo de duplicados** | No aplica. ⚠️ **Riesgo de divergencia, no de duplicación:** el fallback es una **tercera copia** de las decisiones comerciales del seed. Un cambio de precio en `seed_catalogo_fest` **no** se refleja aquí, y el frontend seguiría mostrando el precio viejo cuando la API devuelva una lista vacía. Además, el fallback **no incluye el pase de fiesta**, que sí crea el seed. |
| **Restricciones de entorno y seguridad** | Ninguna. |
| **Dependencias** | Depende de la forma del contrato `Paquete` del frontend y del hook `useLandingPaquetes`. |
| **Evidencia de uso actual** | ✅ **Activo.** Importado y usado en `frontend/src/components/landing/Paquetes.tsx`; el componente `Paquetes` se usa en `frontend/src/app/informacion/page.tsx`. Sin tests detectados en el radio de 3 saltos (CodeGraph). ⚠️ **Divergencia de calendario verificada:** el fallback declara la preventa del **2026-10-19** al **2026-10-31**, mientras `seed_catalogo_fest` fija `fecha_limite_preventa = 2026-10-31` y `vigente_desde = date.today()` (es decir, **la fecha de ejecución del seed**) — tres fechas distintas para la misma ventana. |
| **Verificación segura** | Inspección estática: `Select-String -Path "frontend\src\components\landing\Paquetes.tsx" -Pattern "FALLBACK_PAQUETES"`. Para contrastar en caliente: llamar a `GET /api/.../paquetes` y verificar que devuelve 8 filas; si devuelve 0, la landing está mostrando el fallback. |

### 2.12 Calendario comercial y orden editorial del frontend

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `frontend/src/features/portada/config/festival.ts` (constante `VENTAS`) · `frontend/src/features/portada/hooks/useCatalogo.ts:38` (`ORDEN_DISCIPLINAS = ["F7M", "F7F", "VOL", "BAS"]`) · `frontend/src/features/portada/pricing-stage.ts` (etiquetas y notas de etapa) |
| **Invocación** | Automática en render. `pricing-stage.ts` documenta explícitamente: *"el calendario de venta vive en el frontend (el backend solo expone `precio_preventa` y `precio_regular`, sin hora de corte)"*. |
| **Dominio propietario** | Frontend, feature `portada`. |
| **Propósito** | Decidir la etiqueta y el precio aplicables según la fecha actual. **Es una fuente de verdad comercial que el backend no conoce.** |
| **Registros creados** | Ninguno (constantes). Ventanas: preventa hasta el 25 de octubre a las 20:00 (Lima), regular del 26 de octubre al 8 de noviembre a las 20:00, extemporánea del 9 al 18 de noviembre a las 20:00, cierre el 18 de noviembre a las 20:00. `ORDEN_DISCIPLINAS` fija las 4 siglas en el orden editorial de las tabs del campeonato. |
| **Naturaleza de la escritura** | Ninguna. |
| **Idempotencia y riesgo de duplicados** | No aplica. ⚠️ Riesgo de **divergencia con `seed_catalogo_fest`**: el backend fecha la preventa con `vigente_desde = date.today()` y `vigente_hasta = 2026-10-31`; el frontend cierra la preventa el **25 de octubre a las 20:00**. Hay **6 días** entre ambos cortes y la hora exacta solo existe en el frontend. |
| **Restricciones de entorno y seguridad** | Ninguna. |
| **Evidencia de uso actual** | ✅ **Activo.** `useLandingPaquetes` y `useCatalogo` son los hooks de la landing; `pricing-stage.ts` lo consumen `Portada` y `TicketsSection`. `ORDEN_DISCIPLINAS` replica el orden de las siglas del seed, lo que lo convierte en una **cuarta duplicación** de la lista de disciplinas. |
| **Verificación segura** | Inspección estática de `config/festival.ts` y contraste con `python manage.py check_etapas.py`. |

### 2.13 Fixtures y factories de test (no son semillas de runtime)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | 28 archivos: `backend/modules/{administracion,commerce,competencias,pagos,salesianos_fest,usuarios}/tests/{fixtures,conftest.py,factories.py}` |
| **Invocación** | `pytest` con `DJANGO_SETTINGS_MODULE = config.settings.test` (`backend/pytest.ini`), `--nomigrations`, base SQLite **en memoria** (`:memory:`), `asyncio_mode = auto`. |
| **Dominio propietario** | Cada módulo, en su propia carpeta `tests/`. |
| **Propósito** | Proveer datos deterministas a los tests. **Nunca se ejecutan en runtime ni en producción.** |
| **Modelos / tablas** | Los mismos modelos de dominio, pero sobre una base **en memoria** que se destruye al terminar la sesión. |
| **Naturaleza de la escritura** | Crea filas **solo** en la base de test. El marcador `@pytest.mark.django_db` envuelve cada test en una transacción que se revierte. |
| **Idempotencia y riesgo de duplicados** | ✅ Sin riesgo para la base de desarrollo: la base de test es `:memory:`. Los fixtures usan `get_or_create` o `create` según el caso. |
| **Restricciones de entorno y seguridad** | ✅ Separación estricta: `config.settings/test.py` fuerza `DEBUG=True`, `SECRET_KEY` de prueba, `CIP_USE_SIMULATOR=True` y `NOTI_EMULATOR_ENABLED=True`. Los datos personales son ficticios. |
| **Dependencias** | `contract/TEST_ARCHITECTURE_CONTRACT.md` (los fixtures de `liquidaciones` que ese contrato describe **no existen** en este repositorio: no hay módulo `liquidaciones` — brecha B-4). |
| **Evidencia de uso actual** | ✅ **Activo.** `seed_catalogo_fest` y `seed_commerce` son invocados por 6 + 12 tests respectivamente. |
| **Verificación segura** | `pytest backend/modules/commerce/tests/integration/test_seed_commerce.py -q` — corre contra `:memory:`, sin tocar `db.sqlite3`. |

### 2.14 Migración con gate de datos (`pagos/0006`)

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `backend/modules/pagos/migrations/0006_transpccionpago_intento_activo_unico.py` |
| **Invocación** | `python manage.py migrate` (automático en el arranque del contenedor). |
| **Dominio propietario** | `pagos`. |
| **Propósito** | Instalar el índice único parcial de "un intento vivo por orden" **solo si los datos están limpios**. |
| **Modelos / tablas** | Lee `pagos.TransaccionPago`; añade la constraint `uniq_transpago_activo_orden` (`UniqueConstraint(condition=Q(status="PENDIENTE"), fields=["orden_pago"])`). |
| **Naturaleza de la escritura** | ⚠️ **No crea filas.** `RunPython(exigir_datos_limpios, RunPython.noop)` — la función forward **solo cuenta** y lanza `RuntimeError` si encuentra una orden con más de un intento `PENDIENTE`; el reverse es `noop`, así que **deshacer la migración no toca datos**. |
| **Idempotencia y riesgo de duplicados** | ✅ Es una guarda, no un siembro. |
| **Restricciones de entorno y seguridad** | ✅ Falla cerrado: si los datos no están limpios, la migración se revierte y la base conserva su forma actual. |
| **Dependencias** | Requiere `pagos.0005_aprobacion_pago_manual`. |
| **Evidencia de uso actual** | ✅ **Aplicada** en la base actual (`django_migrations` contiene `('pagos', '0006_transpaccionpago_intento_activo_unico')` — ⚠️ el nombre tiene un typo, `transpccionpago`). Estado actual: 4 `TransaccionPago` en estado `PENDIENTE` (intentos vivos), 3 `CAPTURED`, 5 `EXITO`. Ninguna orden con más de un intento vivo → el índice se pudo instalar. |
| **Verificación segura** | `python manage.py verificar_intentos_pago` — comando **de solo lectura** por diseño (documentado como tal), devuelve 0 si no hay órdenes inseguras. |

### 2.15 `worker/scraper` — microservicio sin siembra

| Dimensión | Detalle verificado |
|---|---|
| **Ruta** | `worker/scraper/` (`main.py`, `documento_scraper.py`, `capturar_dni_inexistente.py`, `explorar_dni_click_flow.py`, `verificar_consulta_dni.py`, `test_worker_live.py`, `tests/`) |
| **Invocación** | Servicio en el compose (`container_name: salesianos_scraper`), healthcheck `GET /health` en el puerto interno 8001. Los demás scripts son utilidades **manuales** de exploración contra el portal externo. |
| **Dominio propietario** | Worker. |
| **Propósito** | `GET /consultar/{documento}`: consulta un DNI (8 dígitos) o RUC (11 dígitos) en un portal externo y devuelve el dato, o un error tipificado (404 / 422 / 502 / 503 / 504). |
| **Modelos / tablas** | **Ninguna.** Es un microservicio FastAPI **sin base de datos**: no importa Django, no importa `psycopg2`, no escribe en ningún almacén. Verificado: no hay ninguna referencia a modelos, ORM ni conexión de datos en sus 5 módulos Python. |
| **Naturaleza de la escritura** | **Ninguna.** El servicio es de lectura sobre un portal externo. |
| **Idempotencia y riesgo de duplicados** | No aplica. |
| **Restricciones de entorno y seguridad** | Solo lectura de un portal público. Los scripts auxiliares (`capturar_dni_inexistente.py`, `explorar_dni_click_flow.py`, `verificar_consulta_dni.py`) son **instrumentación de desarrollo** que hacen peticiones al portal real; `test_worker_live.py` es un test **live** que **requiere red** y es **incompatible con una ejecución offline** de la suite. |
| **Dependencias** | `SCRAPER_URL` (env, configurado en el compose del servicio `backend`). |
| **Evidencia de uso actual** | ✅ **Activo en runtime** (es dependencia declarada del servicio `backend` con `condition: service_healthy`). 🔍 Los tres scripts de exploración manual no tienen evidencia de uso reciente; son herramientas de una investigation puntual. |
| **Verificación segura** | `curl http://localhost:<puerto>/health` o `docker compose exec scraper python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8001/health').read())"`. |

---

## 3. Orden de ejecución recomendado

Derivado **únicamente** de dependencias verificadas en el código. No incluye atajos ni pasos sin respaldo.

### 3.1 Base nueva, entorno vacío

| Paso | Comando | Depende de | Motivo verificado |
|---|---|---|---|
| 0 | `python manage.py migrate` | — | Crea el esquema. Ninguna semilla puede correr antes. |
| 1 | `python manage.py create_admin` | paso 0 | No depende de ninguna otra semilla. Da acceso al admin para operar el catálogo. |
| 2 | `python manage.py seed_catalogo_fest` | paso 0 | Crea `Evento`, `Promocion`, `Categoria`, `Disciplina`, `Paquete`, `PaquetePrecio`, `PaqueteBeneficio`, `PaqueteDisciplina` y `Pase`. |
| 3 | `python manage.py seed_commerce` | pasos 0 **y 2** | Lee `Evento` activo y `Paquete` activo: aborta sin ellos (`seed_commerce.py:94-107`). Solo si se necesitan fixtures de compra en desarrollo. |

**Orden inverso inválido:** `seed_commerce` antes de `seed_catalogo_fest` termina sin error de proceso pero **sin sembrar nada** (imprime el error y hace `return`).

### 3.2 Reinicio completo del entorno de desarrollo

| Paso | Comando | Nota |
|---|---|---|
| 1 | `python manage.py reset_dev --settings=config.settings.development --yes` | Borra el SQLite y reconstruye el esquema. **Modo dry-run si se omite `--yes`.** |
| 2 | `python manage.py create_admin` | Alternativa a `reset_dev --with-admin`. |
| 3 | `python manage.py seed_catalogo_fest` | Alternativa a `reset_dev --with-real-seed` (⚠️ rota, brecha B-2). |
| 4 | `python manage.py seed_commerce` | Opcional. |

⚠️ **`reset_dev --with-real-seed` no debe usarse**: invoca `call_command("seed_real_all")`, un comando que **no existe**. La llamada lanzaría `CommandError: Unknown command: seed_real_all` **después** de haber borrado y recreado la base.

### 3.3 Catálogo comercial ya sembrado, solo actualizar

| Paso | Comando | Efecto |
|---|---|---|
| 1 | `python manage.py seed_catalogo_fest` | Reconcilia promociones, categorías, paquetes, precios, beneficios y vínculos de disciplina. **Reescribe `vigente_desde = hoy` de los precios** — revisar § 4.4 antes de ejecutarlo en una base con preventa en curso. |
| — | `python manage.py seed_catalogo_fest --clear` | ⚠️ **No recomendado** contra una base con inscripciones: `Evento` es `PROTECT` en `Paquete` y `Pase`, por lo que la transacción se revierte con `ProtectedError`. Contra una base limpia, borra el evento, los 8 paquetes, las 56 promociones y las 4 categorías **de todo el sistema**, no solo del FEST 2026. |

### 3.4 Comandos que **no** forman parte de ningún flujo

| Comando | Motivo |
|---|---|
| `seed_colegiados` | No cargable (imports rotos + asset inexistente). |
| `seed_perfiles_ingeniero_faltantes` | No cargable (3 imports rotos). |
| `seed_admin` | Funciona, pero duplica `create_admin` con claves de búsqueda distintas. Preferir `create_admin`. |
| `import_sqlite_to_postgres.py` | Destruye la base destino con `flush`. Procedimiento de migración de un proyecto anterior. |
| `old_seed/cam_db_20260811.*` | Esquema incompatible. Restaurarlo sobrescribe el esquema vigente. |

---

## 4. Matriz seed → tabla

✅ Verificado contra `db_table` en los modelos y contra el inventario de 56 tablas de `backend/db.sqlite3`.

| Tabla | `create_admin` | `seed_admin` | `seed_catalogo_fest` | `seed_commerce` | `reset_dev` | Fixtures de test | Estado actual en `db.sqlite3` |
|---|---|---|---|---|---|---|---|
| `usuarios_persona` | ✅ crea/actualiza | ✅ crea/actualiza | — | ✅ crea | (flush) | ✅ | 26 |
| `usuarios_usuario` | ✅ crea/actualiza | ✅ crea/actualiza | — | — | (flush) | ✅ | 5 |
| `eventos` | — | — | ✅ crea (get_or_create) | ⚪ lee | (flush) | ✅ | 1 |
| `promociones` | — | — | ✅ crea/actualiza (56) | ⚪ lee/crea respaldo | (flush) | ✅ | 56 |
| `categorias` | — | — | ✅ crea/actualiza (4) + 🗑️ borra 4 obsoletas | — | (flush) | ✅ | 4 |
| `disciplinas` | — | — | ✅ crea (4) | ⚪ lee | (flush) | ✅ | 4 |
| `paquetes` | — | — | ✅ crea/actualiza (8) | ⚪ lee | (flush) | ✅ | 8 |
| `paquetes_precios` | — | — | ✅ crea/actualiza (16) | ⚪ lee | (flush) | ✅ | 16 |
| `paquetes_beneficios` | — | — | ✅ crea/actualiza (8) | — | (flush) | ✅ | 8 |
| `paquetes_disciplinas` | — | — | ✅ crea + reconcilia (13) | ⚪ lee | (flush) | ✅ | 13 |
| `pases` | — | — | ✅ crea (1, inactivo) | — | (flush) | ✅ | **0** ⚠️ |
| `pases_precios` | — | — | ✅ crea (2, inactivos) | — | (flush) | ✅ | **0** ⚠️ |
| `pases_beneficiarios` | — | — | — | — | (flush) | ✅ | 0 |
| `salesianos_fest_compra_pase` | — | — | — | — | (flush) | ✅ | 0 |
| `inscripciones` | — | — | — | ✅ crea (3) | (flush) | ✅ | 12 |
| `equipos` | — | — | — | ✅ crea (3) | (flush) | ✅ | 20 |
| `inscripciones_personas` | — | — | — | ✅ crea (1 por inscripción, **no 3**) | (flush) | ✅ | 25 |
| `commerce_compra` | — | — | — | ✅ crea (9) | (flush) | ✅ | 18 |
| `salesianos_fest_compra_inscripcion` | — | — | — | ✅ crea (9) | (flush) | ✅ | 18 |
| `pagos_ordenpago` | — | — | — | ✅ crea (9) | (flush) | ✅ | 18 |
| `pagos_transaccionpago` | — | — | — | ✅ crea (3) | (flush) | ✅ | 12 |
| `asignaciones_cupo` | — | — | — | 🗑️ borra (con `--clear`) | (flush) | ✅ | 23 |
| `participaciones` | — | — | — | 🗑️ borra (con `--clear`) | (flush) | ✅ | 22 |
| `django_migrations` | — | — | — | — | ✅ reconstruye | — | 76 |
| `django_admin_log` | — | — | — | — | (flush) | ✅ | 1 |
| `auth_permission` | — | — | — | — | (flush) | ✅ | 216 |
| `auth_group` / `*_group_permissions` / `*_user_permissions` | — | — | — | — | (flush) | ✅ | 0 / 0 / 0 |
| Tablas `*_historical*` (10) | — | — | — | ⚪ historia de `Compra` | (flush) | ✅ | 171 en total |
| Tablas `django_q_*`, `token_blacklist_*`, `django_session` | — | — | — | — | (flush) | ✅ | 0 / 27 / 2 |

**Leyenda:** ✅ escribe · ⚪ solo lee · 🗑️ borra · — no participa.

⚠️ **Tablas sin ningún mecanismo de siembra en el repositorio** (verificado por inventario de las 56 tablas y por búsqueda de `get_or_create`/`bulk_create`/`create(` en todo `backend/`):

| Tabla | Cómo se puebla en la realidad |
|---|---|
| `pagos_aprobacion_pago_manual` (2 filas) | Aprobaciones manuales creadas por el admin de Django (`AprobacionPagoManual`). Sin seed. |
| `acreditaciones_evento` (21) | Flujo normal de acreditación al resolver la inscripción. Sin seed. |
| `asignaciones_cupo` (23) | Flujo de liquidación de compra (`reparar_cupos` los materializa si el pago se marcó por fuera). Sin seed directo. |
| `aceptaciones_inscripcion` (0) | Flujo de aceptación del participante. Sin seed. |
| `controles_acceso` (0) | Flujo de acreditación. Sin seed. |
| `competencias`, `competencia_equipos`, `rondas`, `encuentros` (0) | Módulo `competencias` **completo pero vacío**. Sin seed. ⚠️ El módulo tiene schema aplicado y API; la_seed no existe. |
| `auth_group` (0) | Los roles de negocio se resuelven con `is_staff`/`is_superuser` + `core/capacidades.py`, **no** con grupos de Django. Sin seed. |

---

## 5. Estado actual de los datos de desarrollo vs. definiciones canónicas

Esta sección separa **dos cosas distintas** que la lectura de la base puede confundir.

### 5.1 Definiciones canónicas (lo que el código declara)

| Elemento | Fuente canónica | Valor declarado |
|---|---|---|
| Evento | `seed_catalogo_fest.py:86-93` | `"Salesianos FEST 2026"`, 2026-11-15 → 2026-11-20, `esta_activo=True` |
| Promociones | `seed_catalogo_fest.py:98-119` | 56, años 1970-2025, rangos Junior/Senior/Master/Super Master |
| Categorías | `seed_catalogo_fest.py:131-147` | 4 oficiales; se borran `Sub-14`, `Sub-16`, `Sub-18`, `Sub-20` |
| Disciplinas | `seed_catalogo_fest.py:150-155` | 4: F7M, F7F, VOL, BAS |
| Paquetes | `seed_catalogo_fest.py:248-374` | 8, con mínimos 10/10/15/20/7/7/6/5 y precios 40-50, 45-55, 60-70, 60-70, 40-50, 40-50, 40-50, 40-50 |
| Beneficios | `seed_catalogo_fest.py:259-312` | 8 filas: 2 FIESTA/FIJO, 2 FIESTA/POR_CUPO + 2 BOX + 2 CERVEZA(6) |
| Pase de fiesta | `seed_catalogo_fest.py:50-53, 384-420` | 1 pase, `cantidad_maxima=0`, **inactivo**; precios S/25.00 y S/35.00, **inactivos** |
| Personas de prueba | `seed_commerce.py:188-192` | 3: DNI `00000001/2/3`, Juan Perez / Maria Garcia / Carlos Rodriguez, tel. `999000001` |
| Superusuario | `create_admin.py:15-16` | `admin` / `admin`, DNI `00000000` |
| Superusuario (variante) | `seed_admin.py:43-48` | `admin` / `admin`, DNI `00000000`, email `admin@salesianos.local` |
| Catálogo del frontend | `frontend/src/components/landing/Paquetes.tsx` | 8 paquetes con los mismos precios; preventa del **2026-10-19** al **2026-10-31** |
| Calendario del frontend | `frontend/src/features/portada/config/festival.ts` | preventa hasta **25-oct 20:00**; regular 26-oct a 8-nov; extemporánea 9 a 18-nov; cierre 18-nov 20:00 |

### 5.2 Estado real de `backend/db.sqlite3` (observación, no definición)

⚠️ **Esta base es un artefacto de desarrollo, no un catálogo de referencia.** Es una copia mutable que nadie ha regenerado; su contenido mezcla sembrado, datos manuales y datos de la aplicación real. Sirve para verificar *qué se ejecutó*, **no** para derivar el catálogo canónico.

| Observación | Lectura | Interpretación |
|---|---|---|
| `promociones` = 56, todas en 1970-2025, ninguna fuera | ✅ | Coincide exactamente con la definición del seed. `seed_catalogo_fest` **sí se ejecutó** (o se replicó su efecto). |
| `categorias` = 4 (Senior, Master, Super Master, Junior) con los rangos oficiales | ✅ | Coincide. Las 4 obsoletas `Sub-*` no están: el borrado del seed corrió. |
| `disciplinas` = 4 (`F7M`/`F7F`/`VOL`/`BAS`) | ✅ | Coincide. |
| `paquetes` = 8 con los nombres y `minimo_compra_inicial` del seed | ✅ | Coincide. |
| `paquetes_precios` = 16, `paquetes_beneficios` = 8, `paquetes_disciplinas` = 13 | ✅ | Coincide exactamente con el seed. |
| `eventos` = 1, `"Salesianos FEST 2026"`, 2026-11-15 → 2026-11-20 | ✅ | Coincide. |
| **`pases` = 0, `pases_precios` = 0** | ⚠️ | **El bloque del pase del seed NO se ha ejecutado contra esta base.** El commit que lo añadió (`eb17e7b`) es del 2026-10-28 18:58; el esquema del pase sí está migrado (`salesianos_fest 0012`–`0015`), de modo que **el catálogo de pases está migrado pero vacío**. |
| `usuarios_persona` = 26: 3 con prefijo `0000000` (los del seed) + `00000000` (admin) + 22 con DNIs de 8 dígitos | ✅ / 🔍 | **4 filas** corresponden a semillas (`00000000` del admin + `00000001/2/3` de `seed_commerce`). Las **22 restantes** son de la app o registro manual: 4 coinciden con los usuarios `dni_*` (`74827847`, `11111111`, `56893455`, `99999999`) y 18 no tienen usuario asociado. |
| `usuarios_usuario` = 5: `admin` (staff+superuser), `dni_74827847`, `dni_11111111`, `dni_56893455`, `dni_99999999` | ⚠️ | Solo **1 usuario** procede de un seed (`admin`). Su `email = admin@admin.com` **no coincide** con ninguno de los dos defaults (`admin@example.com` de `create_admin` / `admin@salesianos.local` de `seed_admin`) → fue **editado por el admin de Django** (`django_admin_log` tiene 1 entrada, `action_flag=2`). Los otros 4 usuarios son de la app, no de seeds. |
| `inscripciones` = 12: 3 `RECIBIDA` + 9 `BORRADOR` | ✅ / 🔍 | Las 3 `RECIBIDA` corresponden al seed (`EstadoInscripcionChoices.RECIBIDA`); las 9 `BORRADOR` son manuales. |
| `inscripciones_personas` = 25 | ✅ | El seed **crea 1 por inscripción**, no 3: 3 de las 25 filas son del seed (confirmando el defecto del bucle, § 2.4). |
| `commerce_compra` = 18: 9 con `referencia_externa` `INIT-/AMP-` + 9 con `FEST-<8 hex>` | ✅ / 🔍 | Las 9 del seed corresponden al patrón exacto del comando. Las 9 `FEST-*` son del flujo real de la app. **El seed no duplicó compras.** |
| `pagos_ordenpago` = 18: 9 `ORD-<10 hex>` (formato del seed) + 9 `ORD<10 dígitos>` (formato de la app) | ✅ | Confirma la cohabitación de datos sembrados y datos reales. |
| `pagos_transaccionpago` = 12: 4 `PENDIENTE`, 3 `CAPTURED`, 5 `EXITO` | ✅ | 4 intentos vivos, ninguno por encima del límite de uno por orden → la migration `pagos/0006` pudo instalarse. |
| `asignaciones_cupo` = 23 (todas `ACTIVA`), `participaciones` = 22 (20 `A`, 2 `R`), `acreditaciones_evento` = 21 | 🔍 | Estados de la app, no del seed. `seed_commerce` **no** crea asignaciones ni participaciones (solo las borra con `--clear`). |
| `competencias`, `competencia_equipos`, `rondas`, `encuentros` = 0 | ⚠️ | El módulo `competencias` tiene schema aplicado y **nunca se ha sembrado**. No existe comando de seed para él. |
| `django_migrations` = 76 | ✅ | Esquema completo, incluido el módulo de pases y `pagos.0006`. |
| `auth_group` = 0 | ✅ | Confirma que los roles se resuelven con `is_staff`/`is_superuser`, no con grupos. |

**Conclusión de § 5**: el estado actual de la base es **consistente con una ejecución de `seed_catalogo_fest` anterior al commit `eb17e7b`** (sin el bloque de pases) **y una ejecución de `seed_commerce`**, coexistiendo con datos manuales y del flujo real. La base **no** es una fuente de verdad: el catálogo canónico es el código del seed.

---

## 6. Verificación segura sin modificar datos

Todas las opciones de esta sección son de **solo lectura**.

### 6.1 Comandos del proyecto que son de solo lectura por diseño

| Comando | Qué responde | Escritura |
|---|---|---|
| `python manage.py verificar_pagos [--json]` | Compras y órdenes "pagadas" sin evidencia verificable (6 códigos de anomalía). | Ninguna |
| `python manage.py verificar_intentos_pago [--json]` | Órdenes con más de un intento vivo `PENDIENTE`. Código de salida 1 si las hay. | Ninguna |
| `python manage.py verificar_pases [--dry-run] [--json]` | Coherencia del catálogo de pases (7 códigos `V-P1`…`V-P7`). | Ninguna |
| `python manage.py auditar_genero_disciplinas [--evento-id <uuid>]` | Participaciones activas con género/modalidad incompatibles. Salida determinista `VIOLATION\|...` y `SUMMARY\|scanned=N\|violations=N`. | Ninguna |

Los cuatro están documentados en su propio docstring como *"READ-ONLY"* / *"never writes"*, y `backend/README.md` lo reitera para `auditar_genero_disciplinas`: *"El comando **nunca escribe**: el SHA-256 de la base y su `mtime` quedan idénticos antes y después."*

### 6.2 Scripts de inspección de solo lectura en `backend/`

| Script | Qué muestra |
|---|---|
| `python manage.py check_count.py` | Totales de `PaquetePrecio` (activos/inactivos, con `vigente_hasta`), y conteo de precios por paquete. |
| `python manage.py check_precios.py` | Los precios activos con su vigencia frente a la fecha de hoy. |
| `python manage.py check_etapas.py` | Tabla `ETAPA \| vigente_desde \| vigente_hasta \| cierre \| vigente_hoy` de los precios activos. |
| `python manage.py check_insc.py`, `check_equipos.py`, `check_estados.py` | Sondas HTTP de solo lectura contra `/api/inscripciones/<uuid>/detalle` con un UUID **hardcodeado** (`5208d884-9925-4d30-85b5-cede31828fd2`). |

⚠️ Los tres últimos usan `django.test.Client` contra la API y **dependen de que ese UUID exista**; con otra base fallan o devuelven datos de otra inscripción. No modifican datos.

### 6.3 Consultas directas de solo lectura

```bash
# Desde el shell de Django (solo lectura)
python manage.py shell -c "
from modules.salesianos_fest.domain.models import *
from modules.eventos.domain.models import Evento
print('evento     ', Evento.objects.count())
print('promociones', Promocion.objects.count())
print('categorias ', Categoria.objects.count())
print('disciplinas', Disciplina.objects.count())
print('paquetes   ', Paquete.objects.count())
print('precios    ', PaquetePrecio.objects.count())
print('beneficios ', PaqueteBeneficio.objects.count())
print('vinculos   ', PaqueteDisciplina.objects.count())
print('pases      ', Pase.objects.count())
print('pase_precios', PasePrecio.objects.count())
"
```

### 6.4 Verificar el resultado de un seed **antes** de ejecutarlo

1. `python manage.py seed_catalogo_fest --help` — confirma que el comando carga (los comandos muertos fallan aquí, antes de tocar la base).
2. `python manage.py seed_commerce --help` — idem; y confirma que `DEBUG=True` en el entorno activo (si no, el comando aborta).
3. Snapshot de conteos antes/después (el bloque anterior).
4. Para `seed_commerce`: `--dry-run` **no existe**. La verificación previa es `python manage.py shell -c "from modules.commerce.domain.models import Compra; print(Compra.objects.count())"`.

### 6.5 Verificación del propio entorno

```bash
# ¿Estoy en desarrollo? (determina si seed_commerce puede correr)
python manage.py shell -c "from django.conf import settings; print(settings.DEBUG, settings.DATABASES['default']['ENGINE'])"

# ¿A qué base apunta?
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['NAME'])"

# ¿El superusuario existe y con qué flags?
python manage.py shell -c "from modules.usuarios.domain.models import Usuario; u=Usuario.objects.get(username='admin'); print(u.email, u.is_staff, u.is_superuser, u.is_active)"
```

---

## 7. Hallazgos transversales

| # | Hallazgo | Evidencia | Impacto |
|---|---|---|---|
| H-1 | **Ninguna siembra es automática.** Ni el `entrypoint.sh`, ni el compose, ni los scripts npm. | `backend/docker/entrypoint.sh` (solo `migrate` + `collectstatic` + gunicorn); `docker-compose.yml` (5 servicios, ninguno de seed); `frontend/package.json` (7 scripts, ninguno `db:*`) | Una base nueva queda **sin evento, sin catálogo y sin superusuario** hasta que alguien ejecute 3 comandos a mano. El único camino documentado (`backend/README.md`) **nombra un comando inexistente** (brecha B-1). |
| H-2 | **El catálogo comercial está duplicado en tres lugares**: `seed_catalogo_fest` (backend), `FALLBACK_PAQUETES` (frontend) y las filas de la base. Los tres deben coincidir y **no hay mecanismo que lo garantice**. | `seed_catalogo_fest.py:248-374` vs. `frontend/src/components/landing/Paquetes.tsx:135-272` | Un cambio de precio en el seed **no** llega al fallback. El fallback se muestra cuando la API devuelve una lista vacía, es decir, **precisamente cuando el seed no se ha ejecutado**: el usuario ve precios de un catálogo que no existe en la base. |
| H-3 | **El calendario de venta existe solo en el frontend.** El backend solo expone `precio_preventa`/`precio_regular`, sin hora de corte. | `frontend/src/features/portada/pricing-stage.ts:4-6` (documentado en el propio archivo) | El backend no puede decidir la etapa vigente. Las tres ventanas declaradas no coinciden entre sí: seed (`vigente_desde` = fecha de ejecución, `vigente_hasta` = 2026-10-31), fallback (`2026-10-19` → `2026-10-31`) y frontend (preventa cierra el **25-oct 20:00**). |
| H-4 | **Dos comandos de superusuario con claves de búsqueda distintas.** | `create_admin.py:31` (`update_or_create(tipo_documento=DNI, numero_documento=...)`) vs. `seed_admin.py:57` (`get_or_create(numero_documento=...)`) | Con parámetros por defecto reconcilian bien. Con parámetros distintos (p. ej. `--dni` distinto o el mismo DNI con otro `tipo_documento`) pueden dejar **dos `Persona` con el mismo número de documento**. Además, `create_admin` **siempre** reinicia la contraseña; el flag `--force` es decorativo. |
| H-5 | **Dos comandos de seed con guardas de entorno opuestas.** `seed_commerce` se niega a correr con `DEBUG=False`; `seed_catalogo_fest` no verifica nada. | `seed_commerce.py:65-75` vs. ausencia de guarda en `seed_catalogo_fest.py` | El único seed que **escribe precios de negocio** es el único que **no puede ejecutarse en producción**. En la práctica, la siembra del catálogo en un entorno real es manual y sin protección. |
| H-6 | **`seed_commerce --clear` borra toda la base de negocio, no solo los datos de prueba.** | `seed_commerce.py:158-182` (borra `Participacion`, `AsignacionCupo`, `CompraInscripcion`, `TransaccionPago`, `Compra`, `OrdenPago`, `InscripcionPersona`, `Equipo`, `Inscripcion` — sin filtro por el prefijo `0000000`) | El `COMMERCE_TEST_DNI_PREFIX` solo está definido (`seed_commerce.py:52`) pero **nunca se usa como filtro de borrado**. Es el comando más destructivo del proyecto, y su nombre no lo insinúa. |
| H-7 | **Defecto de cobertura en `seed_commerce`:** el bucle crea 3 iteraciones de `InscripcionPersona` con la **misma** `persona`, contra un `UniqueConstraint(inscripcion, persona)`. Resultado: **1 fila, no 3**. | `seed_commerce.py:255-267` vs. `backend/modules/salesianos_fest/domain/models/inscripcion_persona.py:49-52` | Los datos de prueba de inscripción tienen **una sola persona** por inscripción, pese a que el log anuncia tres. El fixture no representa el escenario que pretende representar. |
| H-8 | **`seed_catalogo_fest` reescribe `vigente_desde = date.today()` en cada ejecución.** | `seed_catalogo_fest.py:199-218` | Reejecutar el seed durante la preventa **desplaza la ventana de precio hacia adelante**, reabriendo la preventa. Es un efecto secundario comercial de un seed que se presenta como idempotente. |
| H-9 | **`Evento` no tiene `UniqueConstraint` sobre `nombre`.** | `backend/modules/eventos/domain/models/evento.py`, `Meta` sin `constraints` | `Evento.objects.get_or_create(nombre=...)` no está protegido por la base: una carga concurrente puede duplicar el evento, y un duplicado previo haría fallar el comando con `MultipleObjectsReturned`. |
| H-10 | **Dos comandos `seed_*` son inejecutables por imports rotos, y tres archivos muertos los acompañan.** | `perfil_ingeniero.py` (solo docstring de deprecación); `seed_colegiados.py:17-22`; `seed_perfiles_ingeniero_faltantes.py:32-40`; `RealCipClient`/`CipServiceUnavailableError` inexistentes en `modules/usuarios/infrastructure/services.py` | `manage.py seed_colegiados` falla con `ImportError` antes de tocar la base. `admin/catalogo_admin.py` y `admin/perfil_admin.py` registran `ModelAdmin` para modelos inexistentes, pero no se importan (el `admin/__init__.py` solo carga `UsuarioAdmin`) → son trampas de mantenimiento que un refactor podría activar por accidente. |
| H-11 | **El módulo `competencias` tiene schema, API y README, pero ninguna semilla.** | 4 tablas de competencias en `db.sqlite3`, todas con 0 filas; `backend/modules/competencias/README.md` documenta la secuencia de despliegue sin paso de seed | No es un defecto (un cuadro eliminatorio se crea por operación, no por seed), pero **debe constar** para que nadie lo busque como una omisión. |
| H-12 | **El contrato de testing describe fixtures de un módulo que no existe.** | `contract/TEST_ARCHITECTURE_CONTRACT.md` § 1–3 especifica `modules/liquidaciones/tests/fixtures/*`; no hay módulo `liquidaciones` | La fuente de verdad del testing describe una estructura de referencia de otro proyecto. Las fixtures reales de este repositorio siguen el mismo patrón, pero con otros módulos. |

---

## 8. Brechas no resueltas

| # | Brecha | Evidencia | Estado |
|---|---|---|---|
| B-1 | `backend/README.md` § "Cargar Promociones y Paquetes" documenta `manage.py seed_inscripciones`, **un comando que no existe**. El comando real es `seed_catalogo_fest`. | `backend/README.md` (comando `seed_inscripciones`); búsqueda exhaustiva: no hay archivo `seed_inscripciones*` en el repositorio | ⚠️ **Abierta.** Un operador que siga el README ejecuta un comando inexistente y cree que el catálogo quedó cargado. |
| B-2 | `reset_dev --with-real-seed` invoca `call_command("seed_real_all")`, **un comando que no existe**. | `backend/core/management/commands/reset_dev.py:236-237`; no hay ningún `seed_real_all*` en el repositorio | ⚠️ **Abierta.** La opción falla **después** de borrar y recrear la base, con el `flush`/`migrate` ya ejecutados. |
| B-3 | El **README de `backend/` no menciona** `reset_dev`, `seed_catalogo_fest` (con su nombre real), `seed_admin` ni `seed_commerce`. | `backend/README.md` solo documenta `create_admin` y `seed_inscripciones` | ⚠️ **Abierta.** El único mecanismo de reinicio completo (`reset_dev`) es invisible para el operador, y el único comando de fixtures de desarrollo (`seed_commerce`) no aparece por ningún lado pese a existir con su propia suite de tests. |
| B-4 | `contract/TEST_ARCHITECTURE_CONTRACT.md` es la "fuente de verdad" del testing pero describe `modules/liquidaciones/tests/`, un módulo inexistente en este repositorio. | `contract/TEST_ARCHITECTURE_CONTRACT.md` § 1, § 3.1, § 10.2 | ⚠️ **Abierta.** El patrón que sigue el repositorio es equivalente, pero el contrato apunta a un árbol que no está. |
| B-5 | Los **precios del pase de fiesta** (`25.00` / `35.00`) están declarados como *"un supuesto de producto pendiente de confirmación"* y el **rollout** exige `PASES_FIESTA_ENABLED=True` + activación manual, según el propio comentario del seed. | `seed_catalogo_fest.py:41-53` | 🔍 **Abierta.** No es un defecto de código sino una decisión de negocio pendiente: nadie ha confirmado el precio del pase. |
| B-6 | `PASES_FIESTA_ENABLED` **no existe como constante** en el código: el seed lo menciona en su comentario pero el flaggable real no está. El pase se crea inactivo y su activación es manual por el admin. | `seed_catalogo_fest.py:380-384` (comentario) frente a la ausencia del símbolo en `backend/` | 🔍 **Abierta.** El "rollout explícito" descrito en el comentario no tiene un interruptor de código: solo la activación manual. |
| B-7 | **El calendario de preventa no tiene una fuente única.** Tres fechas distintas (seed, fallback, frontend) para la misma ventana comercial. | `seed_catalogo_fest.py:173` (`2026-10-31`), `Paquetes.tsx:97` (`2026-10-19`), `config/festival.ts` (25-oct 20:00) | ⚠️ **Abierta.** Requiere una decisión de diseño: mover el calendario al backend o alinear las tres constantes. |
| B-8 | **La categoría `Sub-*` obsolete se borra por nombre**, no por rango: si el backend creara una categoría legítima llamada `Sub-18`, el seed la eliminaría. | `seed_catalogo_fest.py:123-128` | 🔍 **Abierta.** Riesgo bajo con el modelo actual (4 categorías fijas), real si el catálogo se vuelve editable por el admin. |
| B-9 | `Evento.objects.get_or_create(nombre="Salesianos FEST 2026")` está acoplado al literal, mientras el backend resuelve el evento activo por `EVENTO_ACTIVO_NOMBRE`. Una **segunda edición** exigiría cambiar el seed y la variable de entorno por separado. | `seed_catalogo_fest.py:87` vs. `config/settings/base.py:141` | 🔍 **Abierta.** `Aplicacion/documentacion/06-operacion-y-deuda-tecnica.md` § 4.3 ya lo señala para la variable de entorno; aquí se añade el segundo punto de acoplamiento. |
| B-10 | No hay **ningún comando de seed para `competencias`**, pese a que el módulo tiene schema aplicado, API pública y README con secuencia de despliegue. | `backend/modules/competencias/README.md`; `backend/modules/competencias/management/` **no existe** | 🔍 **Abierta.** Probablemente intencional (los cuadros se crean por operación), pero no está declarado como tal en ninguna parte. |

---

## 9. Anexo: comandos de gestión del proyecto no relacionados con siembra

Los siguientes comandos **no** son seeds, pero se confunden con ellos al ser "comandos de gestión propios" y están registrados en `Aplicacion/documentacion/06-operacion-y-deuda-tecnica.md` § 4.2. Se listan aquí para que la frontera sea explícita.

| Comando | Naturaleza | Escribe datos | Por qué no es un seed |
|---|---|---|---|
| `reconciliar_pagos` | **Reparación** | Sí — liquida compras pendientes de órdenes ya pagadas y asigna derechos de cupo | Cierra una brecha de un flujo ya ejecutado; no crea un catálogo base. Idempotente. Documenta que contra datos reales liquida compras reales: revisar `--dry-run` antes. |
| `reparar_cupos` | **Reparación** | Sí — materializa los cupos pagados nunca asignados | Igual que el anterior: cierra una brecha, no siembra un catálogo. Idempotente. |
| `verificar_pagos` | Solo lectura | No | Diagnóstico de evidencia de pago. |
| `verificar_intentos_pago` | Solo lectura | No | Preflight de la garantía de "un intento vivo por orden". |
| `verificar_pases` | Solo lectura | No | Diagnóstico del catálogo de pases (7 códigos de anomalía). |
| `auditar_genero_disciplinas` | Solo lectura | No | Auditoría de compatibilidad género/modalidad. |

> Los cuatro de solo lectura son, por diseño, las **herramientas de verificación seguras** de este proyecto para confirmar el estado de los datos sembrados (§ 6.1).
