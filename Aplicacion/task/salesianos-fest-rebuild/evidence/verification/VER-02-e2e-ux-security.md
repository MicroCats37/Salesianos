# VER-02 — Business E2E, UX, Accessibility, Permission And Secret QA

**Artifact:** `evidence/verification/VER-02-e2e-ux-security.md` ·
**Packet:** `VER-02` · **Original plan tasks:** `T-092`, `T-093`, `T-094` ·
**Change:** `salesianos-fest-rebuild` · **Owner:** A9 + dueño de cada superficie ·
**Mode:** apply (verification + cleanup only) · **Artifact store:** engram + physical evidence ·
**Date:** 2026-11-20

> **ESTADO: `completed` CON BLOQUEOS EXPRESOS ARRASTRADOS.**
>
> Las puertas que este packet puede cerrar en este entorno están **verdes y
> ejecutadas**: los **29** casos de la matriz de QA tienen ejecución real
> (**113** pruebas focales verdes), la **frontera de permisos** está recorrida
> sobre las **79** operaciones vivas, la **auditoría de accesibilidad y
> responsive** está congelada como puerta de regresión, y los **dos** defectos
> que esas puertas probaron están **corregidos**.
>
> **VER-02 NO se firma `completed` sin declarar tres cosas:**
>
> 1. **La pasada de navegador a los cinco anchos NO se ejecutó**: este entorno
>    no tiene motor de navegador (ni Playwright, ni Puppeteer) y la
>    instalación de dependencias está prohibida. Es un **BLOQUEO DE
>    ENTORNO**, no de código (§6.4).
> 2. **La lane PostgreSQL NO se ejecutó**: mismo bloqueo de entorno que
>    VER-01 §12.3, **re-verificado** hoy (§4.3).
> 3. **El techo de Biome sigue rojo** contra el baseline congelado
>    (444/110 vs 105/93): deuda **heredada** de todo el frontend del rebuild,
>   Dueño **A0 + A7** (§6.5). VER-02 **no** la introduce y la **reduce en 1**.

---

## 1. Entorno de verificación

| Elemento | Valor |
|---|---|
| Directorio de trabajo (backend) | `Aplicacion/backend` |
| Directorio de trabajo (frontend) | `Aplicacion/frontend` |
| Gestor | `uv 0.10.9` (f675560f3) · CPython 3.10.0 · Django 5.2.11 · pytest 8.3.4 |
| Base de datos de la suite | SQLite `:memory:` (`config.settings.test`) |
| Frontend | vitest 5.1.1 · TypeScript `tsc --noEmit` · biome 2.2.0 |
| Node | v24.19.0 · npm 11.17.0 |
| HEAD | `2c411cdfc062714cfa7ff39765c4357ddf8267e2` ("betha 6") — **sin commit creado por este packet** |
| Puntos de rollback | `%TEMP%\opencode\ver02\` (fuera del repositorio, nada commiteado) |
| Motor de navegador | **NINGUNO** — `node_modules/@playwright`, `node_modules/playwright`, `node_modules/puppeteer` **no existen**; la instalación de dependencias está prohibida |

**Restricciones respetadas:** `uv run --group dev …` **exclusivamente** para el
backend · nunca `git stash` / `reset` / `checkout` / `commit` / `push` ·
ningún fichero de `contract/**` · ningún `Aplicacion/plan/**` · ningún
`.env*` · ninguna base de datos del repositorio · **cero** instalaciones de
dependencias · el árbol sucio y concurrente **se preservó intacto** fuera de
los 12 ficheros listados en §8.

---

## 2. Comandos / códigos de salida

### 2.1 Backend (workdir `Aplicacion/backend`, **sólo** `uv run --group dev`)

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| B1 | `python -m pytest modules -q -m "e2e or integration"` (**lane DEL PACKET, antes del arreglo**) | **5** | **704 deselected · 0 tests collected** — la lane **no recogía NADA** (§3.1) |
| B2 | `python -m pytest modules -q -m "e2e or integration"` (**lane DEL PACKET, después del arreglo**) | **0** | **711 passed · 6 deselected** · 182.74 s — la lane **corre de verdad** |
| B3 | `python -m pytest modules core -q` (suite completa, **medición de VER-02**) | **0** | **987 passed** · 1086 warnings · 188.14 s (974 de VER-01 + **13** de la puerta de seguridad nueva) |
| B8 | `python -m pytest modules core -q` (suite completa, **corrida de cierre**) | **0** | **1011 passed · 2 skipped** · 1095 warnings · 308.00 s — el recuento **subió** por el trabajo **concurrente** de otro agente (§2.5), **no** por este packet |
| B9 | `python -m pytest modules -q -m "e2e or integration"` (lane DEL PACKET, **corrida de cierre**) | **0** | **732 passed · 2 skipped · 6 deselected** · 316.65 s |
| B4 | `python -m pytest <113 node-ids de la matriz de QA> -q` (**matriz**) | **0** | **113 passed** · 34.63 s — la evidencia de los 29 casos (§3.2) |
| B5 | `python -m pytest modules/administracion/tests/integration/test_ver02_frontera_de_permisos.py -q` (puerta de seguridad) | **0** | **13 passed** · 7.78 s |
| B6 | `python -m pytest modules -q -m "not e2e and not integration" --collect-only -q` | **0** | **6** tests sin marcar: `modules/eventos/tests/test_contrato_eventos.py` — son de contrato unitario y **no** pertenecen a la lane e2e/integración |
| B7 | `python -m pytest modules -q --collect-only -q` | **0** | **717 collected** · 0 errores de recolección |

### 2.2 Frontend (workdir `Aplicacion/frontend`)

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| F1 | `npx vitest run` | **0** | **53 files passed (53)** · **2288 passed (2288)** · 0 fallos — antes: 52/2276 |
| F2 | `npx tsc --noEmit` | **0** | **LIMPIO** — 0 diagnósticos |
| F3 | `npx biome check .` | **1** | `Checked 715 files` · **444 errors** · **110 warnings** — antes: 714/445/110 ⇒ **VER-02 reduce la deuda heredada en 1** (§6.5) |
| F4 | `npx vitest run src/lib/__tests__/ver-02-auditoria-a11y-responsive.test.ts` | **0** | **12 passed** — la puerta de accesibilidad y responsive (§5) |

### 2.3 Escanse de secretos (comando DEL PACKET, salida redactada)

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| S1 | `git grep -n -I -E "(SECRET_KEY\|IZIPAY_KEY\|SMTP_PASSWORD)=" -- Aplicacion` | **0** | **1 coincidencia**, en `Aplicacion/documentacion/06-operacion-y-deuda-tecnica.md:357`: la línea es una **descripción de deuda** (`D-14`), **no un valor**. **Ningún valor de secreto aparece en el repositorio** y **ningún valor se ha copiado aquí** |

### 2.4 Inventario de rutas (registro vivo, `config.api.get_openapi_schema()`)

| Magnitud | Valor |
|---|---:|
| Rutas (paths) | **75** |
| Operaciones (path × método) | **79** |
| Operaciones protegidas por JWT | **53** |
| Operaciones públicas | **26** |
| Controllers registrados | **22** |

`75` paths y `79` operaciones: **coinciden** con el registro vivo medido por
VER-01 §12.2 ⇒ **DRIFT A sigue en 0**.

---

### 2.5 CONCURRENCIA: el árbol cambió bajo este packet

Durante la corrida de cierre **otro agente escribió en el árbol del objetivo**.
**VER-02 no lo tocó, no lo revirtió y no lo fusionó.**

| Momento | Qué pasó | Dónde |
|---|---|---|
| ~05:22 | VER-02 mide la suite completa **verde**: **987 passed** (con los cambios de VER-02 ya aplicados) | — |
| 05:37 → 06:09 | Otro agente añade la identidad `categoria_id` a `Competencia`: **~20 ficheros modificados** + `migrations/0002` + `migrations/0003` + **2 suites nuevas** (`test_identidad_categoria.py`, `test_elegibilidad_categoria.py`) | `modules/competencias/**` |
| 05:58 | Corrida intermedia **ROJA**: `2 failed · 941 passed · 44 errors` — los fallos y errores eran **todos** del trabajo concurrente | `modules/competencias/**` |
| 06:09 | El agente concurrente sigue trabajando (última escritura en `modules/competencias/`) | — |
| 06:16 | `modules/competencias` queda **verde** por su cuenta: **69 passed · 2 skipped** | — |
| 06:26 → 06:27 | El dueño (**A0**) alinea el registro global `core/contract_versions.py` con el MAJOR `2.0.0` del módulo y actualiza su guardián | `core/contract_versions.py` · `core/tests/integration/test_contract_versions.py` |
| 06:32 | Corrida de cierre de VER-02: **1011 passed · 2 skipped · exit 0** | — |

**Aislamiento medido (no supuesto):** con `--ignore=modules/competencias` la
suite daba `940 passed` con **un** único fallo —`test_no_hay_drift_entre_el_registro_y_el_modulo[competencias]`—, o sea
**todo** el rojo estaba **confinado** al trabajo concurrente, y el guardián
detectaba exactamente el drift `2.0.0` (módulo) vs `1.0.0` (registro) que su
dueño corrigió a las 06:26.

**Lo que este packet NO hizo:** no tocó `modules/competencias/**`, no
revirtió nada, no fusionó nada y **no** cuenta el trabajo concurrente como
resultado de VER-02. Las **cifras de VER-02** son las de la **corrida de
cierre** (`B8`/`B9`), sobre el árbol tal como queda; las cifras de la
**medición propia** (`B3`) son `987 passed` sobre el árbol de las 05:22.
Los **113** node-ids de la matriz y los **13** de la puerta de seguridad se
reejecutaron **sobre el árbol final** y ambos siguen **verdes** (`113 passed`,
`13 passed`).

---

## 3. La matriz de QA (29 casos) — T-092

### 3.1 El arreglo que hace posible la lane

La lane que el packet exige es `-m "e2e or integration"`. En el árbol tal
como estaba, **ningún test declaraba esos marcadores**: `pytest.ini` sólo
declara `asyncio` y `django_db`, y los ficheros viven en `tests/e2e/` y
`tests/integration/` **sin** decorador de marcador. Resultado medido: **704
deselected, 0 collected, exit 5** ⇒ **la puerta del packet no producía
evidencia ninguna**.

**Corrección (única, en `Aplicacion/backend/conftest.py`):** el marcador se
DERIVA de la carpeta del test (la convención que el árbol ya usa) y se REGISTRA
en `pytest_configure`, sin tocar `pytest.ini` (raíz compartida que `BL-04` §5
declara prohibited). Una suite nueva entra en su lane sin editar 95
ficheros.

**Antes → después:** `704 deselected · 0 collected · exit 5` ⇒
`711 passed · 6 deselected · exit 0`.

### 3.2 La matriz ejecutada

**Una sola corrida focales de 113 node-ids** cubre los 29 casos
(`B4` → **113 passed · exit 0**). La columna «evidencia» cita los node-ids
exactos; el fichero de node-ids íntegro está en
`%TEMP%\opencode\ver02\qa-matrix-nodeids.txt` (fuera del repositorio).

| ID | Escenario | Precondiciones | Pasos | Resultado esperado | Resultado obtenido | Evidencia (node-id, abreviado) | Estado |
|---|---|---|---|---|---|---|---|
| **QA-E01** | Ediciones 2026/2027: módulos compartidos, datos separados, personas reusadas | 2 eventos, 1 edición `PUBLICADA` por evento | resolver alcance por evento; listar | Un evento NO arrastra la edición de otro; el histórico sigue consultable | 3/3 aislamiento + unicidad de `PUBLICADA` por evento | `test_edicion_scope_service.py::test_aislamiento_*` (3) · `test_edicion_modelos.py::test_solo_una_edicion_publicada_por_evento` · `test_ediciones_controller.py::test_devuelve_la_edicion_publicada_y_sus_modulos` | **PASS** |
| **QA-U01** | Persona sin Usuario: asignar pase/participar sin cuenta | persona sin `usuario`; edición publicada | resolver por documento; asignar participante; comprar pase | Se puede participar y comprar sin crear cuenta | La persona existe sin cuenta; la compra invitada NO crea cuenta | `test_persona_identidad.py::test_persona_puede_existir_sin_cuenta` · `test_asignacion_participante.py::test_la_persona_se_puede_resolver_por_documento` · `test_compra_pase.py::test_la_compra_invitada_no_crea_ninguna_cuenta` | **PASS** |
| **QA-U02** | Documento existe/no existe: local primero; externo sólo si falta | fuente externa simulada | resolver; confirmar | Local NO consulta la externa; la externa NO persiste; el fallo se distingue | 7/7: local sin consulta, externo no persiste, `confirmar` persiste, no-encontrado / no-disponible / timeout distinguidos, fallo recuperable | `test_persona_resolucion.py` (7 casos) | **PASS** |
| **QA-U03** | Compra ajena por DNI: no se puede acceder sólo con DNI | inscripción de otra persona | actor con el documento consulta | Rechazo; el grupo admin NO sustituye la titularidad | 4/4: `INSCRIPCION_NO_AUTORIZADA`, el grupo no sustituye, la cuenta normal no administra | `test_titularidad.py::test_conocer_un_documento_no_autoriza_la_operacion_de_otro` · `test_un_responsable_ajeno_no_es_titular` · `test_el_grupo_no_sustituye_la_titularidad` · `test_una_cuenta_normal_no_administra` | **PASS** |
| **QA-I01** | Inscripción inicial pendiente: 0 cupos habilitados antes del pago | alta de inscripción | crear; leer pool | Nace con 0 cupos pagados; el saldo disponible es 0; la compra queda pendiente y recuperable | 4/4 | `test_inscripcion_pago_pendiente.py` (4) | **PASS** |
| **QA-I02** | Confirmación de compra: aumentan cupos una vez, incluso con callback repetido | compra pagada; webhook duplicado | activar; repetir | Los cupos se conceden una vez; el duplicado no concede dos veces | 8/8: activación idempotente por clave, beneficio fijo no duplicado, webhook duplicado y tardío no conceden dos veces | `test_cupo_activacion.py` (4) · `test_pago_activacion.py::test_un_webhook_duplicado_no_habilita_el_derecho_dos_veces` · `test_la_confirmacion_tardia_no_habilita_el_derecho_dos_veces` | **PASS** |
| **QA-I03** | Ampliación: agrega cupos a la misma inscripción, sin duplicar el beneficio fijo | inscripción pagada | ampliar | Compra separada y pendiente; la ampliación no duplica el beneficio fijo | 4/4 | `test_ampliacion_cupos.py` (3) · `test_cupo_activacion.py::test_la_ampliacion_no_duplica_el_beneficio_fijo_inicial` | **PASS** |
| **QA-I04** | Retiro de participante: cupo libre reutilizable, compra/importe intactos | participante asignado | retirar | El cupo se libera SIN tocar la compra; no se puede retirar el de otra inscripción | 4/4 | `test_cupo_disponibles.py::test_retirar_libera_el_cupo_sin_tocar_la_compra` · `test_cupo_controller.py::test_retirar_un_participante_libera_su_cupo` · `test_asignacion_participante.py` (2) | **PASS** |
| **QA-I05** | Carrera de asignación: no se exceden cupos ni se duplica participación | 2 asignaciones simultáneas | asignar en paralelo | No se sobre-suscribe el pool; la inscripción no se duplica | 4/4 **sobre SQLite** ⇒ la serialización real **NO** está probada (§4.3) | `test_asignacion_participante.py::test_dos_asignaciones_simultaneas_no_sobre_suscriben` · `test_inscripcion_concurrencia.py` (2) | **PASS con BLOQUEO de motor** |
| **QA-P01** | Compra de pase sin cuenta: orden creada sin Usuario y habilitación tras pago | pase con precio vigente | comprar sin sesión | 201; ninguna cuenta creada; lote pendiente; la activación habilita | 4/4 | `test_pase_controller.py::test_comprar_pases_sin_cuenta_responde_201` · `test_compra_pase.py` (2) · `test_activador_pase.py::test_la_activacion_habilita_el_lote` | **PASS** |
| **QA-P02** | Beneficiarios: asignación limitada y sin derecho duplicado | lote pagado | asignar; repetir | No se excede la capacidad; no se duplica el derecho activo ni la cortesía | 3/3 | `test_beneficiario_pase.py` (3) | **PASS** |
| **QA-P03** | Cortesía admin: derecho creado con motivo y sin transacción ficticia | admin con motivo | otorgar cortesía | Acta con actor y motivo; el derecho existe; **no** hay compra, orden ni transacción | 4/4 | `test_cortesia_pase.py` (3) · `test_pase_controller.py::test_otorgar_una_cortesia_registra_el_acta` | **PASS** |
| **QA-C01** | Cerrar/reabrir modal: no cancela ni duplica compra; estado coherente | compra pendiente | cerrar el checkout; reabrir | La compra NO se cancela; el checkout reabierto REUTILIZA la compra y **no** crea otra orden de pago | 4/4 | `test_compra_reutilizacion.py` (3) · `test_pago_intentos.py::test_reabrir_el_checkout_no_crea_otra_orden` | **PASS** |
| **QA-C02** | Doble webhook: un pago y un efecto por compra | webhook duplicado | notificar dos veces | Un pago; un efecto; una notificación | 4/4 | `test_pago_confirmacion.py` (2) · `test_notificacion_independencia.py::test_un_webhook_duplicado_no_genera_dos_notificaciones` · `test_activacion_compra.py::test_un_reintento_concurrente_no_habilita_el_derecho_dos_veces` | **PASS** |
| **QA-C03** | Fallo posterior a pago: el cobro persiste; incidencia visible y recuperación idempotente | la activación falla | reintentar; conciliar | El cobro **persiste**; hay incidencia; el reintento habilita; la conciliación converge **sin** revertir el cobro | 6/6 | `test_activacion_compra.py` (2) · `test_reconciliacion_pago.py` (3) · `test_notificacion.py::test_el_intento_queda_registrado_aunque_no_se_envie` | **PASS** |
| **QA-M01** | Pedido y stock: el pedido pendiente no vende más del stock disponible | stock limitado | 2 pedidos pendientes | No se sobre-vende; la reserva aparta; la activación repetida no descuenta dos veces | 4/4 | `test_inventario_reserva.py` (2) · `test_activador_marketplace.py::test_una_activacion_repetida_no_descuenta_dos_veces` | **PASS** |
| **QA-M02** | Salida administrativa sin pago: movimiento −5 con actor/motivo, sin compra ficticia | inventario con existencias | registrar salida | No se crea compra ni pago; el movimiento es inmutable | 3/3 | `test_inventario_movimientos.py` (2) · `test_inventario_controller.py::test_una_venta_no_se_puede_registrar_a_mano` | **PASS** |
| **QA-M03** | Precio de oferta cambiado: la compra antigua mantiene el snapshot | producto con oferta | cambiar el precio; releer | El pedido conserva el snapshot; el cambio posterior no lo altera | 2/2 | `test_pedido_snapshot.py::test_un_cambio_de_precio_posterior_no_altera_el_pedido` · `test_el_snapshot_de_la_compra_es_el_mismo_del_pedido` | **PASS** |
| **QA-M04** | Entrega: pedido pagado no equivale a entregado | pedido pagado | confirmar entrega | El pago NO entrega; la entrega mueve sólo su estado; es idempotente y reintentable | 5/5 | `test_pedido_snapshot.py::test_el_pago_confirmado_paga_el_pedido_pero_no_lo_entrega` · `test_entrega_pedido.py` (2) · `test_inventario_controller.py::test_no_se_confirma_la_entrega_de_un_pedido_no_pagado` | **PASS** |
| **QA-V01** | Ticket usado dos veces: el segundo consumo se deniega y se audita | ticket canjeado | canjear con otra clave | 409 `TICKET_YA_CONSUMIDO` y acta | 2/2 | `test_validacion_ticket.py::test_el_segundo_uso_con_otra_clave_se_deniega_y_se_audita` · `test_e2e_validacion.py::test_el_segundo_canje_con_otra_clave_responde_409` | **PASS** |
| **QA-V02** | Escaneo simultáneo: sólo se consume la cantidad permitida | 2 escaneos concurrentes | escanear en paralelo | Se consume una sola vez; la cantidad excedente se deniega | 2/2 **sobre SQLite** ⇒ `select_for_update` es un NO-OP (§4.3) | `test_concurrencia_validacion.py::test_dos_escaneos_simultaneos_consumen_una_sola_vez` · `test_validacion_ticket.py::test_la_cantidad_excedente_se_deniega` | **PASS con BLOQUEO de motor** |
| **QA-K01** | Elegibilidad: equipo de edición/disciplina incorrecta no entra a la competencia | ediciones y disciplinas distintas | listar elegibles | El equipo de otra edición, de otra disciplina o con plantilla incompleta NO es elegible | 4/4 | `test_elegibilidad.py` (4) | **PASS** |
| **QA-K02** | Programación: no acepta solapamiento improcedente | horarios que se tocan | programar | Un equipo no se solapa consigo mismo; los intervalos que sólo se tocan NO se solapan; la agenda no cambia al rechazar | 3/3 | `test_solapamiento_horario.py` (3) | **PASS** |
| **QA-K03** | Corregir resultado: preview de impacto y confirmación sin cascada oculta | resultado registrado | previsualizar; corregir | La vista previa NO escribe; un descendiente ya transcurrido BLOQUEA la cascada; el override explícito la permite | 5/5 | `test_correccion.py` (3) · `test_preview_avance.py` (2) | **PASS** |
| **QA-A01** | Pagos admin: estado claro, filtro operativo y diagnóstico avanzado | compras con 4 veredictos | filtrar; abrir detalle | Cada veredicto tiene etiqueta y descripción; el filtro declarado por el resumen es el que el listado acepta | 2/2 backend + `src/features/admin/pagos/__tests__/pagos-admin-estados.test.tsx` (verde en `F1`) | `test_estado_operativo_pago.py::test_cada_veredicto_tiene_etiqueta_y_descripcion` · `test_admin_operacion.py::test_el_filtro_estado_pago_devuelve_las_inscripciones_sin_pagar` | **PASS** |
| **QA-A02** | Equipo admin: la pantalla de detalle explica plantilla y estado | equipo con plantilla incompleta | filtrar por plantilla | El filtro `plantilla=INCOMPLETA` usa el mínimo que publica la disciplina | 1/1 backend + `src/features/admin/equipos/__tests__/equipos-admin-estados.test.tsx` (verde en `F1`) | `test_admin_operacion.py::test_el_filtro_plantilla_devuelve_los_equipos_incompletos` | **PASS** |
| **QA-A03** | Acciones admin: el frontend oculta lo prohibido; el backend rechaza el comando forzado | admin; versión desfasada | forzar comando | El actor sin capacidad NO pasa; el comando sensible SIN motivo es 422; la versión desfasada es 409 | 4/4 backend + `src/features/admin/operaciones/__tests__/operaciones-estados.test.tsx` (verde en `F1`) | `test_admin_operacion.py` (3) · `test_bye_manual.py::test_el_bye_exige_motivo_auditado` | **PASS** |
| **QA-MEDIA01** | Imágenes: N imágenes ordenadas, persistentes sin CDN | multipart con N ficheros | crear; releer | La galería queda en orden; token duplicado, huérfano, firma inválida y tamaño excedido se rechazan; el alta persiste los archivos | 9/9 | `test_producto_multipart.py` (5) · `test_patrocinadores_multipart.py` (2) · `test_producto_media_limpieza.py::test_una_alta_exitosa_persiste_los_archivos` · `test_patrocinadores_multipart.py::test_un_anonimo_recibe_401` | **PASS** |
| **QA-N01** | Email no disponible: no revierte compra ni derecho | SMTP no configurado | notificar | El intento queda registrado; el envío se omite con código explícito; el fallo NO revierte el pago confirmado | 3/3 | `test_notificacion.py` (2) · `test_notificacion_independencia.py::test_el_fallo_de_la_notificacion_no_revierte_el_pago_confirmado` | **PASS** |

**Totales:** **29 / 29** con ejecución real. **27** verdes plenos · **2**
(`QA-I05`, `QA-V02`) verdes **con BLOQUEO DE MOTOR** (§4.3). **0** casos sin
evidencia y **0** casos inventados.

---

## 4. Concurrencia — T-093

### 4.1 Lo que SÍ está probado (motor SQLite)

| Escenario | Caso | Resultado |
|---|---|---|
| Alta de inscripción duplicada | `test_inscripcion_concurrencia.py::test_dos_altas_simultaneas_no_duplican` | **PASS** |
| Carrera perdida reutiliza la ganadora | `test_inscripcion_concurrencia.py::test_la_carrera_perdida_reutiliza_la_inscripcion_ganadora` | **PASS** |
| Dos asignaciones simultáneas | `test_asignacion_participante.py::test_dos_asignaciones_simultaneas_no_sobre_suscriben` | **PASS** |
| Base de datos impide sobre-suscribir el pool | `test_cupo_disponibles.py::test_la_base_de_datos_impide_sobre_suscribir_el_pool` | **PASS** |
| Reintento concurrente de activación | `test_activacion_compra.py::test_un_reintento_concurrente_no_habilita_el_derecho_dos_veces` | **PASS** |
| Doble webhook | `test_pago_activacion.py::test_un_webhook_duplicado_no_habilita_el_derecho_dos_veces` | **PASS** |
| Confirmación tardía | `test_pago_activacion.py::test_la_confirmacion_tardia_no_habilita_el_derecho_dos_veces` | **PASS** |
| Confirmaciones simultáneas de persona | `test_concurrencia_persona.py::test_confirmaciones_simultaneas_no_duplican` | **PASS** |
| Doble escaneo de ticket | `test_concurrencia_validacion.py::test_dos_escaneos_simultaneos_consumen_una_sola_vez` | **PASS** |
| Dos pedidos pendientes no sobrevenden | `test_inventario_reserva.py::test_dos_pedidos_pendientes_no_sobrevenden` | **PASS** |

### 4.2 La reserva es una sentencia atómica condicional

`test_asignacion_participante.py::test_la_reserva_de_cupo_es_una_sentencia_atomica_condicional`
— la garantía está **escrita y probada** en el código; lo que falta es el
**motor** que la haga cumplir.

### 4.3 BLOQUEO: la lane PostgreSQL NO se puede ejecutar (ENTORNO)

**Re-verificado HOY** (no heredado sin comprobar):

| Comprobación | Resultado |
|---|---|
| `Get-NetTCPConnection -LocalPort 5432 -State Listen` | **hay** un `postgres` escuchando en 5432 (PID 6964) |
| Conexión con las credenciales del propio `Aplicacion/docker-compose.yml` (`salesianos_db` / `salesianos_user` / `changeme`) por `127.0.0.1:5432`, `connect_timeout=5` | **FALLO**: `OperationalError` vacío — el servidor cierra durante la autenticación |
| Motor de Docker | **NO corre**: `Get "http://%2F%2F.%2F%2Fpipe%2FdockerDesktopLinuxEngine/v1.47/info": … El sistema no puede encontrar el archivo especificado` ⇒ el servicio `db` del compose (`postgres:16-alpine`) **no se puede levantar** |
| Módulo de settings con PostgreSQL en el objetivo | **ninguno**: `config/settings/` = `base`, `development`, `production`, `test` — y `test` está **fijado** a SQLite `:memory:` |

⇒ **Clasificación: BLOQUEO DE ENTORNO, no de código.** El riesgo de
`XCT-01` §7.1 (`select_for_update` es un NO-OP en SQLite) **sigue ABIERTO**
para `QA-V02` / `QA-I05`. **Debe cerrarse antes del corte de producción.**
Dueño: **A0 + A9**.

---

## 5. UX, accesibilidad y responsive — T-093

### 5.1 La puerta que este packet congela

**Fichero nuevo (VER-02):**
`Aplicacion/frontend/src/lib/__tests__/ver-02-auditoria-a11y-responsive.test.ts`
— **12 casos** que miden la REGLA que el marcado debe obedecer, sobre **las
38 rutas vivas** y **todo** el árbol de producto.

| Contrato | Puerta | Resultado |
|---|---|---|
| §1 · inventario | La aplicación sirve **38** rutas; las 38 están en el mapa `RUTAS` (los parámetros se normalizan: `:token`, `:slug` y `:id` son la misma plantilla) | **PASS** |
| §1 · los cinco anchos | Cada ruta declara puntos de ruptura (`sm:`/`md:`/`lg:`/`xl:`) en la familia de producto que **importa** | **PASS** (38/38) |
| A11Y-02 · foco visible | Ningún control del área de producto quita el contorno sin declarar anillo, borde o fondo de foco | **PASS** |
| A11Y-04 · `scope` | Toda cabecera de columna del área de producto declara `scope` | **PASS** (tras el arreglo §7.2) |
| A11Y-07 · 44 px | Ningún control autónomo del área de producto queda por debajo de 44 px | **PASS** (tras el arreglo §7.3) |
| A11Y-10 · ubicación | La navegación (cabecera, barra lateral, submenú admin) expone `aria-current` | **PASS** |
| A11Y-12 · movimiento | `app/globals.css` declara `prefers-reduced-motion` | **PASS** |
| A11Y-13 · `alt` | Ninguna imagen del árbol queda sin `alt` | **PASS** |
| §1.2 · antipatrones | El zoom **NO** está desactivado; ningún contenedor del área de producto fija un ancho de píxeles | **PASS** |

### 5.2 La deuda declarada que NO crece

Las primitivas `components/ui/**` son **fuente copiada de shadcn**: su dueño es
A7 + A0, no este packet. La puerta **congela la lista exacta** de lo que se
sabe roto, de modo que un hallazgo invisible se convierte en deuda **contada**
y su crecimiento **rompe** la puerta:

| Primitiva | Defecto | Estado |
|---|---|---|
| `components/ui/searchable-select.tsx` | el `<input>` del combobox quita el contorno **sin** indicador de foco | **ABIERTO** — dueño A7 + A0 |

### 5.3 Los 38 caminos vivos (auditados)

`/` · `/administracion` · `/administracion/competencias` ·
`/administracion/competencias/:id` · `/administracion/competencias/:id/cuadro` ·
`/administracion/competencias/agenda` · `/administracion/ediciones` ·
`/administracion/equipos` · `/administracion/equipos/:id` ·
`/administracion/inscripciones` · `/administracion/inscripciones/:id` ·
`/administracion/marketplace` · `/administracion/marketplace/entregas` ·
`/administracion/marketplace/inventario` ·
`/administracion/marketplace/productos/:id` · `/administracion/pagos` ·
`/administracion/participantes` · `/administracion/pases` ·
`/administracion/pases/validar` · `/administracion/patrocinadores` ·
`/administracion/personas` · `/administracion/usuarios` ·
`/administracion/validaciones` · `/informacion` · `/inscripcion` · `/login` ·
`/mi-cuenta` · `/mis-compras` · `/mis-compras/:id` · `/mis-inscripciones` ·
`/mis-inscripciones/:id` · `/pases` · `/pases/gestionar/:token` ·
`/recuperar-compra` · `/registro` · `/tienda` · `/tienda/:slug` ·
`/tienda/pedidos/:token`

El bracket público conceptual `RT-CP-10` (`/competencias/[id]`) **no** existe
como página: es la proposición sin page ID de GOV-02, no una ruta viva.

### 5.4 Los estados (SH-03, diez estados)

La cobertura de estados por superficie está probada por las **52** suites de
estado que ya existen (`*-estados.test.tsx` de `cuenta`, `inscripciones`,
`pases`, `marketplace`, `patrocinadores`, `validaciones`, `competencias`,
`admin/*`, `public`, `pagos`) y las **6** suites de contrato de pago. Todas
verdes en `F1` (2288/2288). El **detalle** de cada estado por ruta **no** se
reproduce aquí: la evidencia ejecutable son esas suites, y su nombre es el
de la superficie.

---

## 6. Seguridad y secretos — T-094

### 6.1 La frontera de permisos, recorrida sobre las 79 operaciones

**Fichero nuevo (VER-02):**
`Aplicacion/backend/modules/administracion/tests/integration/test_ver02_frontera_de_permisos.py`
— **13 casos**.

| # | Puerta | Resultado |
|---:|---|---|
| 1 | El registro vivo declara al menos una ruta por superficie (la puerta no puede pasar en vacío) | **PASS** (79 operaciones) |
| 2 | **Ninguna operación nueva se vuelve pública sin revisión**: el conjunto de operaciones públicas del registro vivo es **exactamente** la lista congelada de **26** | **PASS** — DRIFT de exposición = **0** |
| 3 | **Ninguna** de las **53** operaciones protegidas acepta una petición anónima: **53/53 ⇒ 401** | **PASS** |
| 4 | La denegación anónima usa el código congelado `AUTHENTICATION_REQUIRED` y `data: null` | **PASS** (53/53) |
| 5 | **Ninguna** denegación filtra traza, ruta, SQL, excepción cruda ni identificador interno (16 marcas vigiladas) | **PASS** (53/53) |
| 6 | Una cuenta del grupo `Normal` **no** alcanza ninguna superficie con capacidad: **403**, nunca 2xx (22 superficies de administración + competencias + validaciones + las 2 escrituras con capacidad) | **PASS** |
| 7 | La denegación por capacidad usa `ACTION_NOT_ALLOWED` | **PASS** |
| 8 | **Un token ajeno no abre un lote ni un pedido**: 404 en las 4 rutas con token, con código congelado | **PASS** |
| 9 | La notificación del proveedor **sin firma** se rechaza con 400 `PAGO_NOTIFICACION_NO_VERIFICABLE` | **PASS** |
| 10 | La denegación por titularidad es la **congelada**: 403 `INSCRIPCION_NO_AUTORIZADA` para «no es tuyo», 404 `INSCRIPCION_NO_ENCONTRADA` para «no existe»; ninguna de las dos filtra datos del recurso | **PASS** (ver §6.3, V-02-SEC-01) |

### 6.2 Lo que la sonda midió (respuestas reales, no opinión)

La sonda recorrió **las 79** operaciones con **tres** actores (anónimo, cuenta
`Normal`, cuenta `staff`) y guardó el cuerpo de cada respuesta:

| Actor | Resultado medido |
|---|---|
| Anónimo sobre las **53** rutas con JWT | **53 × 401** — **0** respuestas 2xx, **0** respuestas 5xx |
| `Normal` sobre las superficies con capacidad | **403** en todas; **0** respuestas 2xx |
| `Normal` sobre las rutas de dominio (`inscripciones`, `pagos/ordenes`, `marketplace/pedidos`, `personas`) | 404 / 409 / 422 según el caso — **siempre** sin 2xx y **sin** datos del recurso ajeno |
| Anónimo sobre las **26** rutas públicas | catálogo 404 (sin edición publicada en la sonda), token ajeno 404, webhook sin firma 400, token sin carga 400, fuente externa 503 |

Los **cuerpos** son SIEMPRE la envoltura congelada
(`success`/`data`/`error`/`message`) con `error.code` estable y prosa
pública. **Cero** trazas, **cero** rutas internas, **cero** SQL, **cero**
identificadores internos.

### 6.3 Hallazgos de seguridad abiertos (NO críticos)

| # | Hallazgo | Severidad | Consecuencia | Dueño |
|---|---|---|---|---|
| **V-02-SEC-01** | `GET /api/inscripciones/{id}` (y las rutas de titularidad equivalentes) responden **403** a «existe pero no es tuyo» y **404** a «no existe»: un actor **autenticado** puede distinguir la existencia por el código | **BAJA** | Oráculo de existencia; NO filtra datos ni permite la acción | **Producto + A0** — el código `INSCRIPCION_NO_AUTORIZADA` está **congelado** en `FR-03` §2.1; neutralizarlo exige una **enmienda de contrato**, fuera de las raíces de este packet |
| **V-02-SEC-02** | Las **3** operaciones de `/api/token/**` (`ninja_jwt`) responden con la envoltura **propia de la biblioteca** (`{"detail":…,"code":"invalid"}`) y **no** con la envoltura congelada `success`/`data`/`error`/`message` de `FR-01` §4 | **BAJA** | Inconsistencia de contrato, **no** de seguridad: el frontend (`src/app/api/auth/refresh/route.ts`) consume la forma correcta y el sistema funciona | **A0** — `NinjaJWTDefaultController` es un controller de terceros; sustituirlo es una decisión de arquitectura |
| **V-02-SEC-03** | El conmutador de visibilidad de la contraseña y las pestañas de acceso miden 24 px y 36 px | **BAJA** | Cumplen el mínimo de WCAG 2.5.8 (24×24); no llegan al objetivo de 44 px del proyecto | **A7 / UI-01** — la corrección mueve el icono y necesita una decisión de diseño |

**Ninguno** de los tres es crítico, y **ninguno** permite leer, escribir ni
ejecutar nada fuera del alcance del actor.

### 6.4 Lo que NO se pudo hacer: la pasada de navegador

**BLOQUEO DE ENTORNO.** Comprobado, no supuesto:

- `node_modules/@playwright` — **no existe**;
- `node_modules/playwright` — **no existe**;
- `node_modules/puppeteer` — **no existe**;
- `node_modules/axe-core`, `jest-axe`, `vitest-axe` — **no existen**;
- la instalación de dependencias está **prohibida** por las reglas del packet.

⇒ **NO se ejecutó** ninguna medición en 360 / 390 / 768 / 1024 / 1440 con un
motor de render, **ni** un recorrido de tabulación real, **ni** un barrido de
axe, **ni** una prueba con lector de pantalla.

Lo que **sí** se ejecutó, y es su substitutes honesto:

1. **12/12** de la puerta de contrato (§5.1) sobre **las 38** rutas y todo el
   árbol de producto — la REGLA que el marcado obedece;
2. **53/53** de las rutas vivas con petición real y cuerpo real (§6.2);
3. las **6** suites responsive/portada ya existentes del proyecto
   (`public-responsive`, `portada-viewport`, `cuenta-responsive`,
   `inscripcion-responsive`, `inscripcion-transporte`) — verdes en `F1`;
4. la **deuda declarada y congelada** de las primitivas de shadcn (§5.2).

**Residuos explícitos** (nunca se asumen verdes):

| Residuo | Por qué no se puede cerrar aquí |
|---|---|
| Ancho real de columna, desbordamiento horizontal del `body`, reflow a 200 % de zoom | Requiere motor de layout |
| Orden de tabulación real y trampa/restauración de foco en diálogo | Requiere navegador real |
| Contraste calculado por par de token en claro y oscuro | Requiere axe/Lighthouse |
| Conductor de lector de pantalla (NVDA / VoiceOver) | Requiere dispositivo y navegador |
| Comportamiento de cámara y QR con poca luz | Requiere dispositivo |

### 6.5 El techo de Biome

| Medición | Errores | Avisos | Ficheros |
|---|---:|---:|---:|
| Techo del baseline congelado (`BL-04` §3.3) | 105 | 93 | 566 |
| VER-01, segunda pasada (2026-11-20) | 445 | 110 | 714 |
| **VER-02 (ahora)** | **444** | **110** | **715** |

El recuento de errores **bajó en 1** (el `organizeImports` de
`PreinscribirButton.tsx`, que este packet tocó) y el fichero nuevo de la
puerta de auditoría es **limpio**. La puerta de lint **sigue roja** contra el
techo: es **deuda heredada** de todo el frontend del rebuild, en código de
producción ajeno a este packet. **Dueño: A0 + A7.** **No bloquea VER-03**, pero
**bloquea la firma** de VER-03.

### 6.6 Escanse de secretos

`S1` (§2.3): **0 valores de secreto** en `Aplicacion/`. La única coincidencia
es una **descripción de deuda** en la documentación. Además:

- **backend**: **0** `logger.*` con `password|token|secret|clave|referencia|cvv|tarjeta|dni`; **0** `print`.
- **frontend**: el único `console.log` está en `src/errors/toast-adapter.ts`
  y es el **valor por defecto** de un adaptador que la aplicación **sustituye**
  en `src/providers/ReactQueryProvider.tsx:23` (`configureToast(toast.error,
  toast.success)`) ⇒ **nunca se ejecuta** en la aplicación.
- **respuestas**: los cuerpos de las 79 operaciones fueron inspeccionados
  (§6.2): **0** filtraciones de secretos, referencias del proveedor, importes
  o firmas.

---

## 7. Correcciones aplicadas por este packet

Todas son **mínimas**, en la raíz de su dueño, y con **prueba** que las
sostiene. **Cero** ficheros de `contract/**`, de `Aplicacion/plan/**`, de
`Aplicacion/documentacion/**`, de los **raíces congelados** (`backend/**`,
`frontend/**`, `worker/**`, `proxy/**`) y **cero** `.env*` o bases de datos.

### 7.1 La lane de verificación que no recogía nada

| Fichero | Cambio | Por qué |
|---|---|---|
| `Aplicacion/backend/conftest.py` | `pytest_configure` registra los marcadores `e2e` e `integration`; `pytest_collection_modifyitems` marca cada test según su carpeta | El packet exige `-m "e2e or integration"` y la lane recogía **0** tests (exit 5). Sin esto, **ninguna** evidencia E2E del packet habría existido |

**Prueba:** `B1` (`704 deselected · exit 5`) ⇒ `B2` (`711 passed · exit 0`) ⇒ `B9` (`732 passed · exit 0` en la corrida de cierre).

### 7.2 La cabecera de columna sin `scope` (A11Y-04)

| Fichero | Cambio | Por qué |
|---|---|---|
| `Aplicacion/frontend/src/features/admin/components/AdminDataTable.tsx` | `scope="col"` en el `<TableHead>` | `SH-02` §2.2: «Column header semantics must be `<th scope="col">`». Es la **tabla compartida de TODO** el panel administrativo: el defecto afectaba a las seis superficies de administración |

**Prueba:** la puerta de VER-02 (`A11Y-04`) pasó de **1 fallo** a **0**.

### 7.3 Los objetivos táctiles por debajo de 44 px (A11Y-07)

| Fichero | Cambio | Por qué |
|---|---|---|
| `features/admin/operaciones/components/BarraFiltros.tsx` | `min-h-11` en «Limpiar filtros» y en «Cerrar» | Eran 32 px (`h-8` de shadcn). El gemelo de escritorio ya lo tenía |
| `features/admin/pagos/components/DetalleComercialPago.tsx` | `min-h-11` en «Cerrar» | Ídem |
| `features/cuenta/components/PanelSesion.tsx` | `min-h-11` en «Entrar de nuevo» | Era 28 px (`size="sm"`) |
| `features/portada/components/Gallery.tsx` | `min-h-11 min-w-11` en «Imagen anterior» y «Siguiente imagen» | Eran 32×32 (`size="icon"`) |
| `features/portada/components/PreinscribirButton.tsx` | `min-h-11` garantizado por `cn()` | El tamaño es dinámico: el llamador podía dejar el botón en 32 px |

**Prueba:** la puerta de VER-02 (`A11Y-07`) pasó de **7 fallos** a **0**; las
**2288** pruebas del frontend siguen verdes y `tsc` sigue en **0**.

---

## 8. Ficheros cambiados por este packet

**Backend (2)**

| Fichero | Acción |
|---|---|
| `Aplicacion/backend/conftest.py` | modificado (§7.1) |
| `Aplicacion/backend/modules/administracion/tests/integration/test_ver02_frontera_de_permisos.py` | **creado** (§6.1, 13 casos) |

**Frontend (7)**

| Fichero | Acción |
|---|---|
| `Aplicacion/frontend/src/lib/__tests__/ver-02-auditoria-a11y-responsive.test.ts` | **creado** (§5.1, 12 casos) |
| `Aplicacion/frontend/src/features/admin/components/AdminDataTable.tsx` | modificado (§7.2) |
| `Aplicacion/frontend/src/features/admin/operaciones/components/BarraFiltros.tsx` | modificado (§7.3) |
| `Aplicacion/frontend/src/features/admin/pagos/components/DetalleComercialPago.tsx` | modificado (§7.3) |
| `Aplicacion/frontend/src/features/cuenta/components/PanelSesion.tsx` | modificado (§7.3) |
| `Aplicacion/frontend/src/features/portada/components/Gallery.tsx` | modificado (§7.3) |
| `Aplicacion/frontend/src/features/portada/components/PreinscribirButton.tsx` | modificado (§7.3) |

**Artefactos (2):** este fichero (creado) y
`Aplicacion/task/salesianos-fest-rebuild/STATE.md` (modificado).

**Nota de concurrencia sobre uno de estos ficheros.** `features/admin/pagos/components/DetalleComercialPago.tsx` recibió **dos** cambios durante el packet: el de VER-02 (`min-h-11` en «Cerrar») **y** uno **concurrente** (el bloque «Compra reutilizada» pasa a distinguir `undefined` de `false`, con «-» en lugar de «Sí»/«No»). El cambio concurrente **se preservó intacto**: no se revirtió ni se fusionó. El diff de VER-02 en ese fichero es **una** línea de clase.

**Fuera del repositorio (temporal, nada commiteado):**
`%TEMP%\opencode\ver02\{route_inventory.py, probe_permisos.py,
probe-frontend.ts, qa-matrix-nodeids.txt, nodeids.txt, backend-full-v.txt,
route-inventory.json, probe-permisos.json}`.

---

## 9. Rollback

1. Revertir los **2** ficheros del backend (`conftest.py` y el guardián de
   permisos nuevo).
2. Revertir los **7** ficheros del frontend (§7.2 y §7.3 y el guardián nuevo).
3. Borrar este fichero y revertir la transición de `STATE.md`.
4. En Engram: restaurar `sdd/salesianos-fest-rebuild/state` y
   `…/apply-progress`.
5. Los ficheros de `%TEMP%\opencode\ver02\` se pueden borrar sin efecto.

**Punto de rollback:** **`2c411cdfc062714cfa7ff39765c4357ddf8267e2`**
("betha 6") — el HEAD real, que **ya existía** cuando este packet empezó y que
**no cambió**: VER-02 **no creó ningún commit**. **Nunca** revertir ni
resetear ese commit.

> **Aviso sobre el SHA que heredan los paquetes.** Todas las transiciones
> anteriores apuntan a `f3df5401c56b61c340f257e67d5a306944e9e670` ("betha 4"),
> pero **ese objeto NO existe en este repositorio**. El SHA real es
> `f3df5401c56b41c340f257e67d5a306904a9e670` (con `b41c` y `d5a3`). La petición
> **`A0-VER01-01`** sigue **ABIERTA** (VER-01 §12.6) y este packet **no** la
> cierra porque la evidencia de otros packets queda fuera de sus raíces.

---

## 10. Veredicto

### 10.1 ¿Completa VER-02?

**SÍ, para su alcance ejecutable en este entorno**, con tres bloqueos
**declarados y explícitos**:

| Criterio de aceptación del packet | Estado |
|---|---|
| «Cada QA ID tiene evidencia real o un bloqueador explícito; ningún éxito inventado» | ✅ — **29/29** con ejecución real (**113** pruebas focales verdes); **0** inventado |
| «Ningún hallazgo crítico de accesibilidad, permiso, titularidad, concurrencia o exposición de secretos queda abierto» | ✅ — **0** críticos: los 3 hallazgos de seguridad son de severidad **BAJA** y están asignados (§6.3); los **2** defectos de accesibilidad **probados** están **corregidos** (§7.2, §7.3) |
| «Los huecos residuales de navegador/dispositivo/lector de pantalla quedan listados» | ✅ — §6.4 (5 residuos, con su causa) |
| «Ejercitar la concurrencia de capacidad, stock, callbacks y validación» | ⚠️ — **10 escenarios verdes** (§4.1) **sobre SQLite**; el **motor con bloqueo de filas** es un **BLOQUEO DE ENTORNO** (§4.3) |
| «Probar 401/403/titularidad/comandos forzados/token scope y barrer respuestas y logs» | ✅ — **53/53** rutas con JWT ⇒ 401; **0** fugas; token ajeno ⇒ 404; webhook sin firma ⇒ 400; comando sensible sin motivo ⇒ 422 (§6.1, §6.2) |
| «Auditar las rutas enviadas a cinco anchos, teclado, foco, nombres, errores, live regions, touch, overflow, reduced motion y tablas/diálogos» | ⚠️ — **la puerta de contrato** sobre las **38** rutas está **verde** (§5.1) y el **barrido de 5 anchos con motor de render NO se ejecutó** (§6.4): **BLOQUEO DE ENTORNO** |
| «Registrar los hallazgos primero por severidad; re-ejecutar sólo después de arreglos separados» | ✅ — §6.3 (3 hallazgos BAJA, asignados) y §7 (2 correcciones con puerta RED→GREEN) |

### 10.2 ¿Queda VER-03 desbloqueado?

**SÍ, con dos condiciones de bloqueo explícitas** (las mismas que arrastraba
VER-01 §12.7, más una nueva):

1. **El techo de Biome** (444/110 vs 105/93) debe cerrarse antes de la
   **firma** de VER-03 — dueño **A0 + A7**.
2. **La lane PostgreSQL** debe correrse antes del **corte de producción** —
   dueño **A0 + A9**.
3. **La pasada de navegador a los cinco anchos** (y el barrido de axe y el
   lector de pantalla) debe ejecutarse en un entorno con motor — dueño
   **A9** con **A7**.

Ninguna de las tres es un defecto de producto introducido por el rebuild que
VER-02 pueda corregir: las tres son **de entorno o de deuda heredada**.

### 10.3 Firmas

| Rol | Estado | Nota |
|---|---|---|
| A9 (QA / E2E / seguridad) | **ejecutado** | 29/29 casos, 79/79 operaciones, 13/13 de la puerta de seguridad |
| A7 (UI / accesibilidad) | **parcial** | 2 correcciones aplicadas; 3 hallazgos BAJA y la deuda de `searchable-select` quedan asignados |
| A0 (cableado / lint / entorno) | **parcial** | 3 bloqueos: Biome, PostgreSQL, motor de navegador |
| Producto | **pendiente** | `V-02-SEC-01` (enmienda de `FR-03` §2.1) y `V-02-SEC-02` (envoltura de `ninja_jwt`) |
