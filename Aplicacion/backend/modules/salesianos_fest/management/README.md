# Comandos de gestión — `salesianos_fest`

> Documento operativo de los comandos de gestión de este módulo: qué siembra
> `seed_catalogo`, qué garantiza y qué NO hace. El contrato de arquitectura
> vive en `contract/`; este archivo no lo reemplaza.

---

## 1. `seed_catalogo` — bootstrap del catálogo

Ruta: `modules/salesianos_fest/management/commands/seed_catalogo.py`

Deja el catálogo poblado para que el flujo de inscripción sea **servible** en
un entorno vacío: sin él, el frontend consulta el catálogo y no hay nada que
mostrar.

```
Evento → Edición PUBLICADA → Promociones (GLOBALES)
                                  → Categorías (de la edición)
                                  → Disciplinas → Paquetes
                                                  → Precios → Vínculos
                                                  → Beneficios
```

El catálogo es el **oficial del FEST**: las categorías con su rango de
promociones, las disciplinas y los paquetes con sus precios unitarios y sus
mínimos comerciales.

### 1.1 Uso

```bash
python manage.py seed_catalogo

# Otra edición (la identidad se pide por parámetro, nunca por constante):
python manage.py seed_catalogo \
    --edicion-slug 2027 \
    --edicion-nombre "Salesianos FEST 2027" \
    --anio 2027

# Informa de lo que haría sin dejar ninguna fila escrita:
python manage.py seed_catalogo --dry-run
```

| Parámetro | Por defecto | Para qué |
|---|---|---|
| `--evento-nombre` | `Salesianos FEST` | Nombre del evento raíz. Se ignora si el evento ya existe. |
| `--evento-slug` | `salesianos-fest` | Slug del evento: su clave natural de reutilización. |
| `--edicion-nombre` | `Salesianos FEST 2026` | Nombre de la edición. Se ignora si ya existe. |
| `--edicion-slug` | `2026` | Slug de la edición: su clave natural de reutilización. |
| `--anio` | `2026` | Año de la edición. Se ignora si ya existe. |
| `--modulo` | — | Módulo lógico adicional a habilitar (repetible). `inscripciones` se habilita **siempre**. |
| `--dry-run` | — | Ejecuta la siembra dentro de una transacción que se deshace. |

### 1.2 Qué queda sembrado

| Entidad | Cuántas | Alcance |
|---|---|---|
| Promociones | 56 | **GLOBALES**: una por año de cohorte (1970–2025). No cuelgan de ninguna edición. |
| Categorías | 4 | Por **edición**: `Junior`, `Senior`, `Master`, `Super Master`, cada una con su rango de cohorte. |
| Disciplinas | 4 | Por edición: fútbol 7 masculino, fútbol 7 femenino, vóley mixto, básquet masculino. |
| Paquetes | 8 | Por edición, con su tipo, su modo de disciplinas, su mínimo comercial y sus beneficios. |
| Precios | 16 | Dos por paquete: **preventa** y **regular**. |
| Vínculos | 13 | Disciplina↔paquete. |
| Beneficios | 8 | Declarados por paquete (`FIESTA`, `BOX_BEBIDAS`, `CERVEZA`). |

El precio es **UNITARIO** (`D-CAT-01`): `PaquetePrecio.monto` es el precio de
**una** persona y el total lo deriva el servidor como `cantidad × precio`
(`RN-C02`). `Paquete.minimo_compra_inicial` es el mínimo **comercial** de
participantes en el alta.

Las dos ventanas de precio tienen fechas **FIJAS** (`2020-01-01` →
`2026-10-31` para preventa, `2026-10-31` → abierta para regular). No se
calculan con `date.today()`: una fecha variable crearía una fila de precio
nueva en cada ejecución y rompería la idempotencia.

### 1.3 Garantías

Cada garantía está cubierta por un test de integración en
`modules/salesianos_fest/tests/integration/test_seed_catalogo.py`.

| # | Garantía | Cómo se cumple |
|---|---|---|
| 1 | **IDEMPOTENTE**: reejecutarlo no duplica ni una fila | Cada entidad se crea con `get_or_create` sobre su clave natural; lo que ya existe se REUTILIZA tal cual. |
| 2 | **NUNCA borra ni resetea** | No hay `--clear`, no hay `delete()`, no hay `update_or_create`. Los vínculos disciplina↔paquete que el operador haya añadido se conservan. Las categorías obsoletas que el legacy borraba (Sub-14, Sub-16, Sub-18, Sub-20) NO se borran: se conservan y el operador puede retirarlas con `estado = INACTIVA`. |
| 3 | **NUNCA pisa la configuración del operador** | Si un paquete ya tiene precios, el seed NO crea los precios oficiales NI modifica los existentes. Si una categoría ya existe con otro rango de promoción, el rango se preserva y se avisa. |
| 4 | **NUNCA corre en el arranque del servidor** | Es un comando de gestión explícito. `docker/entrypoint.sh` no lo invoca. |
| 5 | **NUNCA exige que el frontend elija la edición** | La edición sembrada queda `PUBLICADA` y con el módulo `inscripciones` habilitado, que es lo que exige el orden congelado de alcance (`FR-02` §2.2) cuando el cliente no manda `edicion_id`. |
| 6 | **NUNCA reescribe una fila existente** | La reejecución no cambia ni el contenido ni el `updated_at` de ninguna fila: sólo crea lo que falta. |

### 1.4 Fallas esperadas

| Situación | Comportamiento |
|---|---|
| Ya existe **otra** edición `PUBLICADA` | Falla con `CommandError` y **no siembra nada**: el alcance se resuelve por la edición publicada ÚNICA (`FR-02` §2.2, nivel 3). Un catálogo ambiguo no es un catálogo servible. |
| La edición objetivo está `CERRADA` | Falla con `CommandError`: el seed no reabre una edición cerrada. Indique otra con `--edicion-slug`. |
| La edición objetivo está `BORRADOR` | La publica (si no hay otra publicada) y le habilita `inscripciones`. |

### 1.5 Patrón que sigue

Reproduce el patrón de `modules/eventos/management/commands/
crear_edicion_inicial.py`:

- La identidad del evento y de la edición se pide **por parámetro**, nunca por
  constante de settings.
- El alta de la edición se hace por el **camino de escritura** del módulo
  `eventos` (flujo → core service → selector), no con un `objects.create()`
  directo sobre la edición.
- El comando es **idempotente**.

### 1.6 Verificación de la idempotencia

```bash
# 1) Estado inicial
python manage.py seed_catalogo --dry-run   # informa sin escribir

# 2) Siembra
python manage.py seed_catalogo

# 3) Reejecución: no debe cambiar ningún conteo
python manage.py seed_catalogo
```

Los conteos que el propio comando imprime al final deben ser **idénticos**
entre la primera y la segunda ejecución:

```
Promociones: 56 (catálogo global)
Categorías: 4
Disciplinas: 4
Paquetes: 8
Precios: 16
Vínculos: 13
Beneficios: 8
```

Cobertura automatizada:

```bash
python -m pytest modules/salesianos_fest/tests/integration/test_seed_catalogo.py -q
```

---

## 2. `emitir_ticket` — no pertenece a este módulo

`emitir_ticket` vive en `modules/validaciones/management/commands/`. Se
documenta aquí sólo para dejar constancia de que **no** es un comando de
siembra y **no** debe invocarse durante el bootstrap del catálogo.
