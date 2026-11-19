# FR-09 — Registro de decisiones abiertas (PD y heredadas)

**Freeze:** parte del registro `GOV-01` · **Propietario:** A0 (registro) + producto (decisión) · **Estado:** OPEN — nada aquí está ratificado
**Trazabilidad:** `Aplicacion/plan/salesianos-fest-rebuild/00-decisiones-y-alcance.md` §4 · `funcional/03` §6 · `contratos/01` §2 · `contratos/02` §2 y §5 · `contratos/03` §4 · apply-progress GOV-00 §11

---

## 1. Regla de este registro

> **Nada en este documento está aprobado.** Una `[PROPUESTO]`, una `[PENDIENTE]` o una pregunta abierta sigue abierta después de GOV-01. Este freeze **no** ratifica propuestas: congela **interfaces** para que el trabajo no dependiente avance, y deja cada decisión de negocio con su dueño y su alcance de bloqueo.

Los identificadores `GOV-01-OPEN-xx` son **nuevos** y solo de registro de gobierno. No inventan tareas del plan.

## 2. Decisiones funcionales abiertas (`PD-*`)

Fuente: `00-decisiones-y-alcance.md` §4. Texto original preservado.

| ID | Pendiente (texto del plan) | Afecta | Bloquea | Owner | Ámbito de bloqueo exacto | Freeze relacionada | Estado |
|---|---|---|---|---|---|---|---|
| `PD-01` | BOX: ¿se asigna a responsable, equipo o grupo definido? ¿cómo se utiliza? | Asignación y canje grupal | Detalle de BOX | A4 + producto | No bloquea `FREEZE-RT`. Bloquea el detalle de BOX en DOM-03 (`T-030`…`T-032`) | `FREEZE-RT` §1 (BOX listado como derecho grupal, titularidad abierta) | OPEN |
| `PD-02` | Pases: ¿revocar antes del uso libera la asignación? ¿se permite reemplazar titular? | Reglas de `PaseBeneficiario` | Flujo de revocación | A4 + producto | No bloquea la interfaz de revocación. Bloquea el comportamiento de negocio en DOM-03 (`T-031`) y las pruebas de XCT-01 | `FREEZE-RT` §2.3 | OPEN |
| `PD-03` | Ticket: ¿1 código por unidad o ticket con cantidad y consumo parcial? | Validación por producto | Consumo parcial | A4 + A8 + producto | No bloquea `FREEZE-RT`: la forma expone `cantidad_total` / `cantidad_disponible` / `cantidad_consumida`. Bloquea el producto entregable y los casos de XCT-01 | `FREEZE-RT` §3.1 | OPEN |
| `PD-04` | Acceso: ¿una entrada válida una vez, por día o con reingresos? | Control de acceso | Reglas finales de escaneo | A8 + producto | No bloquea ninguna interfaz. Bloquea las reglas finales de escaneo en XCT-01 (`T-080`) | — | OPEN |
| `PD-05` | Inventario: ¿stock compartido entre ediciones o separado por edición? | Modelo de stock | Modelo definitivo de existencia | A5 + producto | No bloquea `FREEZE-CM` ni `FREEZE-MD`. Bloquea el modelo de existencias en DOM-04 (`T-040`) | `FREEZE-ED` §2.5 (referencia cruzada) | OPEN |
| `PD-06` | Cancelación/reembolso: cuándo se permiten, efecto sobre cupos, entradas y productos | Pagos y dominios | Reembolsos/cancelaciones avanzadas | A2 + producto | No bloquea `FREEZE-CM`. Bloquea XCT-03 (`T-084`) y cualquier endpoint de reembolso | `FREEZE-CM` §5 | OPEN |
| `PD-07` | Compras anónimas: definir ámbito definitivo de guest checkout (inscripción vs pases/tienda) | UX/autenticación | Inscripción como invitado | A1 + A7 + producto | No bloquea `FREEZE-ID` (el mecanismo de invitado está congelado para los dominios que lo usen). Bloquea el flujo de inscripción como invitado en DOM-01 (`T-021`) | `FREEZE-ID` §4 | OPEN |
| `PD-08` | Correo: proveedor, plantillas, límites, reintentos y entrega | Notificaciones | Envío real, no compras | A0 + producto | No bloquea ningún freeze. Bloquea XCT-03 (`T-086`) | `FREEZE-CM` §4 | OPEN — **diferido** (`DEC-21`) |
| `PD-09` | Beneficios de paquete y ampliación: qué se recalcula por cupo y qué se otorga una sola vez | Beneficios adicionales | Algunos paquetes | A4 + producto | No bloquea `FREEZE-CM` ni `FREEZE-RT`. Bloquea DOM-02 (`T-023`) para los paquetes afectados | `FREEZE-RT` §4 (`RN-P01`) | OPEN |
| `PD-10` | Alcance exacto de modificaciones administrativas, motivos, autorizaciones y devoluciones | Operación admin | Acciones sensibles específicas | A0 + producto | No bloquea ningún freeze. Bloquea XCT-02 (`T-083`) | `FREEZE-ID` §5 | OPEN |

### 2.1 Resumen de alcance de bloqueo

| Categoría | PD |
|---|---|
| Bloquean implementación en un paquete concreto | `PD-01`, `PD-02`, `PD-03`, `PD-05`, `PD-06`, `PD-07`, `PD-09`, `PD-10` |
| Bloquean solo reglas finales de prueba | `PD-04` |
| Diferido por decisión explícita del plan | `PD-08` |
| Bloquean un freeze de GOV-01 | **ninguna** |

**Consecuencia:** ningún `PD` bloquea la apertura de FND-01…FND-05 ni de los esqueletos UI-0x. Todos bloquean trabajo **de dominio** posterior, y ninguno se resuelve por inferencia en este freeze.

## 3. Pendientes del plan fuera de la tabla `PD-*`

| ID | Origen | Pendiente | Owner | Ámbito de bloqueo | Estado |
|---|---|---|---|---|---|
| `GOV-01-OPEN-02` | `FL-01` paso 4 `[PROPUESTO]` | Exponer el histórico público de ediciones | A0 + producto | No bloquea nada. **No ratificado** | OPEN |
| `GOV-01-OPEN-03` | sin requisito aprobado | Ciclo de vida de una `Edicion`: fechas, cierre, reapertura | A0 + producto | No bloquea `FREEZE-ED` (las fechas quedan **nullables y sin semántica**). Bloquea las reglas de publicación en FND-02 y ADM-02 | OPEN |
| `GOV-01-OPEN-04` | `contratos/02` §2 | ¿Los operadores de validación usan el grupo `Administrador` o una política interna? «No crear tercer grupo por defecto» | A0 + producto | No bloquea `FREEZE-RT` (la autorización del operador se define por permiso operativo, sin decidir el grupo). Bloquea el modelado de permisos en FND-01 (`T-018`) | OPEN |
| `GOV-01-OPEN-05` | `contratos/02` §5 | Política exacta de expiración, rotación de enlaces y verificación de contacto de la compra invitada | A1 + A0 + producto | No bloquea `FREEZE-ID` §4 (el mecanismo queda congelado con los tres atributos: vencimiento, ámbito, revocabilidad). Bloquea el parámetro concreto de expiración en DOM-03 y XCT-03 | OPEN |
| `GOV-01-OPEN-06` | `PD-06` (derivado) | Política de cancelación/reembolso por dominio | A2 + producto | No bloquea `FREEZE-CM` | OPEN |
| `GOV-01-OPEN-07` | `DEC-21` | Proveedor SMTP, credenciales, cuotas, plantillas y reintentos | A0 + producto | Diferido. No bloquea compras | OPEN — **diferido** |
| `GOV-01-OPEN-08` | `PD-02` (derivado) | Reglas de `PaseBeneficiario` al revocar: liberar asignación, reemplazo de titular | A4 + producto | No bloquea `FREEZE-RT` | OPEN |
| `GOV-01-OPEN-09` | `contratos/03` §5 | Copia de seguridad, permisos del volumen de media y manejo de nombres eliminados | A0 + producto | No bloquea `FREEZE-MD`. Bloquea la parte de despliegue de XCT-03 (`T-085`) | OPEN |
| `GOV-01-OPEN-10` | `FREEZE-MD` | Límites exactos de dimensiones por tipo de imagen | A0 + A5 | No bloquea `FREEZE-MD` (los límites se fijan en FND-01). Bloquea la validación final de imágenes | OPEN |
| `GOV-01-OPEN-11` | `django-app-architecture-contract.md` §16.4 | Versionado de **path** de API (`/v1`) | A0 | No bloquea nada. Este freeze usa versionado de **schema**, no de path | OPEN — pospuesto |
| `GOV-01-OPEN-12` | `FR-07` §3.4 | Rutas de lectura restantes del ledger (catálogos, cuentas, equipos, competencias) | A7 | No bloquea nada. Se amplía en GOV-02 | OPEN |
| `GOV-01-OPEN-13` | `FR-08` | Storybook o equivalente como consumidor formal de fixtures provisionales | A7 | No bloquea nada | OPEN |

## 4. Contradicción documental heredada

| ID | Asunto | Estado |
|---|---|---|
| `GOV-01-OPEN-01` | `TEST_ARCHITECTURE_CONTRACT.md` §2 y §10.5 manda `ninja.testing.TestClient` y prohíbe `django.test.Client`; `django-app-architecture-contract.md` §2.1 prohíbe `ninja.testing.TestClient` para controllers async y permite `django.test.Client`. **Ambos contratos son normativos y del mismo nivel.** | **RESUELTO OPERATIVAMENTE** por `FREEZE-TC-1.0.0` (`FR-01` §7). **ABIERTO DOCUMENTALMENTE**: hace falta una enmienda explícita a `TEST_ARCHITECTURE_CONTRACT.md` §2 y §10.5 que reconozca `NinjaExtraAPI` y `TestAsyncClient`. `contract/**` está en raíz **prohibida** para GOV-01, así que no se modifica aquí. Owner: A0 + producto (GAP-2) |

## 5. Decisiones de gobierno heredadas de GOV-00

No son competencia de GOV-01, pero **siguen abiertas** y se registran aquí para que ningún paquete las trate como resueltas.

| ID | Asunto | Owner | Efecto sobre GOV-01 |
|---|---|---|---|
| `GAP-1` | Destino final de `Aplicacion/**` (borrar y recrear / terminar la copia / abandonar como raíz de código) | A0 + producto | La raiz de destino de este freeze es la ya existente; GAP-1 sigue sin decidir |
| `GAP-2` | Enmiendas a `contract/**` (incluye `GOV-01-OPEN-01`) | A0 + producto | GOV-01 **no** modifica contratos; la enmienda queda en GAP-2 |
| `GAP-3` | Dónde vive la aplicación nueva y la puerta de cutover | A0 + producto | No bloquea el freeze: las interfaces son independientes de la raíz física |
| `GAP-4` | Clasificación de las 5 divergencias de construcción y de los defectos de caché | A0 | No bloquea el freeze; el envelope y la política de caché quedan fijados aquí |
| `D-A` | 26 rutas en cuarentena | A7 + A0 | No bloquea |
| `D-B` | 375 rutas de `frontend/src` no copiadas al destino | A7 + A0 | No bloquea el freeze; sí el trabajo de UI real |
| `D-C` | `Aplicacion/backend/modules/` con solo `__init__.py` | A0 | Confirma que el destino está vacío: los freezes no tienen contraparte de código que ajustar |
| `D-D` | Rotación de 3 conjuntos de secretos | A0 + responsable de credenciales | No bloquea |
| `D-E` | `backend/db.sqlite3` versionado en `f3df540` | responsable de datos | No bloquea |
| `D-1`…`D-6` | Divergencias de la exploración ya **verificadas y corregidas** por GOV-00 | — | No son decisiones: son hechos. Este freeze los consume como hechos |

## 6. Criterios de aceptación de este registro

- [x] Los 10 `PD-*` del plan con owner, ámbito de bloqueo y freeze relacionada.
- [x] Ningún `PD` se convierte en aprobación.
- [x] Los 13 `GOV-01-OPEN-xx` con origen, owner y estado.
- [x] La contradicción del cliente de prueba con estado **operativo** y **documental** diferenciados.
- [x] Las decisiones de gobierno heredadas de GOV-00 registradas como abiertas.
