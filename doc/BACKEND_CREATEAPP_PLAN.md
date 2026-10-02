# Plan de Creación de Django Apps — Salesianos FEST 2026

> **Versión:** 1.0  
> **Fecha:** 2026-09-18  
> **Proyecto:** `salesianos`  
> **Arquitectura:** Django modular con contrato `contract/django-app-architecture-contract.md`  
> **Objetivo:** Documentar los comandos, pasos y archivos para crear los módulos `usuarios` (extender) e `inscripciones` (nuevo) siguiendo la arquitectura del proyecto.

---

## 1. Comando de Referencia para Todos los Pasos

### Entorno virtual y settings

```bash
# Desde backend/
cd C:\Users\Usuario\Desktop\Aplicaciones\CST\Salesianos\backend

# Windows (PowerShell)
.venv\Scripts\python.exe manage.py <comando> --settings=config.settings.development

# Linux/Mac
source .venv/bin/activate
python manage.py <comando> --settings=config.settings.development
```

> **Nota:** `manage.py` por defecto usa `config.settings.production`. Siempre agregar `--settings=config.settings.development` para desarrollo local.

---

## 2. Estrategia de Creación

### Opción elegida: Copiar estructura de `entidades` como template

**¿Por qué no `startapp`?**

1. `django-admin startapp` o `manage.py startapp` genera una estructura plana que NO coincide con la arquitectura CAM.
2. La estructura correcta requiere crear a mano las carpetas `domain/`, `presentation/`, `infrastructure/`, `tests/`, etc.
3. Copiar `entidades` como base y limpiar/adecuar es más rápido y genera menos errores.

**Procedimiento:**

```bash
# 1. Copiar entidades como base
cd C:\Users\Usuario\Desktop\Aplicaciones\CST\Salesianos\backend\modules
cp -r entidades inscripcion_base   # Linux/Mac
# En Windows PowerShell:
# Copy-Item -Path entidades -Destination inscripcion_base -Recurse

# 2. Renombrar la carpeta
mv inscripcion_base inscripcion_module_delete  # paso intermedio
# En Windows:
# Rename-Item -Path inscripcion_base -NewName inscripcion_module_delete
```

**Alternativa más limpia (recomendada):** Crear la estructura manualmente carpeta por carpeta para tenercontrol total.

---

## 3. Módulo `usuarios` — Extender con `Persona`

### 3.1 Archivos a crear/modificar

| Acción | Archivo | Descripción |
|--------|---------|-------------|
| CREAR | `modules/usuarios/domain/models/persona.py` | Modelo Persona |
| MODIFICAR | `modules/usuarios/domain/models/__init__.py` | Re-exportar Persona |
| CREAR | `modules/usuarios/domain/constants.py` | Choices (TipoDocumento, Genero) |
| CREAR | `modules/usuarios/domain/exceptions.py` | Excepciones de dominio |
| CREAR | `modules/usuarios/domain/schemas/persona_schemas.py` | DTOs internos (CreateData, Result) |
| MODIFICAR | `modules/usuarios/admin.py` | Registrar Persona |
| CREAR | `modules/usuarios/tests/factories.py` | Factory de Persona para tests |

### 3.2 Modelo `Persona` (campos según BACKEND_DOMAIN_PLAN.md)

```python
# modules/usuarios/domain/models/persona.py
from django.db import models
from core.models import BaseModel

class Persona(BaseModel):
    class TipoDocumentoChoices(models.TextChoices):
        DNI = "DNI", "DNI"
        CE = "CE", "Carnet de Extranjería"
        PAS = "PAS", "Pasaporte"

    class GeneroChoices(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO = "F", "Femenino"

    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    tipo_documento = models.CharField(max_length=3, choices=TipoDocumentoChoices.choices)
    numero_documento = models.CharField(max_length=20)
    genero = models.CharField(max_length=1, choices=GeneroChoices.choices)
    telefono = models.CharField(max_length=9, blank=True, null=True)
    whatsapp = models.CharField(max_length=9, blank=True, null=True)
    contacto_emergencia_nombre = models.CharField(max_length=120, blank=True, null=True)
    contacto_emergencia_telefono = models.CharField(max_length=9, blank=True, null=True)
    aseguradora_nombre = models.CharField(max_length=255, blank=True, null=True)
    aseguradora_numero_poliza = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "numero_documento"],
                name="unique_tipo_numero_documento"
            )
        ]
```

### 3.3 Relation con `Usuario`

```python
# En Usuario — agregar a modules/usuarios/domain/models/usuario.py
persona_fk = models.OneToOneField(
    "usuarios.Persona",
    on_delete=models.PROTECT,
    related_name="usuario",
    blank=True,
    null=True,
)
```

---

## 4. Módulo `inscripciones` — Crear desde cero

### 4.1 Estructura de carpetas a crear

```
modules/inscripciones/
├── __init__.py                      # Re-exporta desde domain/models/
├── apps.py                          # AppConfig con label="inscripciones"
├── models.py                        # Re-export desde domain/models/
├── admin.py                         # Registro de ModelAdmins
├── di.py                            # Wiring injector
│
├── domain/
│   ├── __init__.py
│   ├── constants.py                 # Choices (EstadoInscripcion, etc.)
│   ├── exceptions.py                # ConflictError, NotFoundError, BusinessError
│   │
│   ├── models/
│   │   ├── __init__.py             # Re-exporta todos los modelos
│   │   ├── disciplina.py           # Disciplina, Categoria
│   │   ├── paquete.py              # Paquete, PaqueteDisciplina
│   │   ├── evento.py               # Evento
│   │   ├── inscripcion.py         # Inscripcion, InscripcionDelegado, PersonaAceptacion
│   │   └── equipo.py               # EquipoInscrito, ParticipacionDisciplina, ParticipanteInscripcion
│   │
│   ├── schemas/                    # DTOs internos (Pydantic)
│   │   ├── __init__.py
│   │   ├── disciplina_schemas.py
│   │   ├── paquete_schemas.py
│   │   ├── inscripcion_schemas.py
│   │   └── equipo_schemas.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── core/                  # Sync services
│   │   │   ├── __init__.py
│   │   │   ├── disciplina_service.py
│   │   │   ├── paquete_service.py
│   │   │   ├── evento_service.py
│   │   │   ├── inscripcion_service.py
│   │   │   └── equipo_service.py
│   │   │
│   │   ├── flujos/                # Async flows (CON transaction.atomic)
│   │   │   ├── __init__.py
│   │   │   └── crear_inscripcion_flujo.py
│   │   │
│   │   └── orchestrators/        # Async facades (delgadas)
│   │       ├── __init__.py
│   │       └── inscripcion_orchestrator.py
│   │
│   └── selectors/                 # Complex queries
│       ├── __init__.py
│       └── inscripcion_selector.py
│
├── presentation/
│   ├── __init__.py
│   ├── schemas/                  # Ninja HTTP schemas (*In, *Out)
│   │   ├── __init__.py
│   │   ├── disciplina_schemas.py
│   │   └── inscripcion_schemas.py
│   │
│   ├── controllers/              # Thin controllers (async)
│   │   ├── __init__.py
│   │   ├── disciplina_controller.py
│   │   └── inscripcion_controller.py
│   │
│   └── presenters/              # Transform result → HTTP schema
│       ├── __init__.py
│       └── inscripcion_presenter.py
│
├── infrastructure/
│   ├── __init__.py
│   └── selectors/               # Concrete selector implementations
│       └── __init__.py
│
├── tests/
│   ├── __init__.py
│   ├── factories.py             # Factory functions (NOT factory_boy)
│   ├── integration/
│   │   └── test_crear_inscripcion_flujo.py
│   └── e2e/
│       └── test_inscripcion_e2e.py
│
└── migrations/
    └── __init__.py
```

### 4.2 Archivos esenciales mínimos para el primer apply

Para la **Fase 1 del apply** (modelos base), crear en orden:

1. `apps.py`
2. `domain/models/disciplina.py` + `domain/models/__init__.py`
3. `domain/models/evento.py`
4. `domain/models/paquete.py`
5. `domain/models/inscripcion.py`
6. `domain/models/equipo.py`
7. `domain/constants.py`
8. `domain/exceptions.py`
9. `di.py`
10. `admin.py`
11. `models.py` (re-export)
12. `migrations/`

### 4.3 Archivo `apps.py`

```python
# modules/inscripciones/apps.py
from django.apps import AppConfig

class InscripcionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.inscripciones"
    label = "inscripciones"
    verbose_name = "Inscripciones"

    def ready(self):
        from . import admin  # noqa: F401
```

### 4.4 Archivo `di.py` (initial vacío)

```python
# modules/inscripciones/di.py
from injector import Module, singleton, Binder

class InscripcionesModule(Module):
    def configure(self, binder: Binder) -> None:
        # Se irán agregando bindings conforme se creen servicios
        pass
```

---

## 5. Registro de Módulos en Settings y API

### 5.1 `config/settings/base.py` — Agregar a `LOCAL_APPS`

```python
LOCAL_APPS = [
    # ... existentes ...
    "modules.inscripciones",  # AGREGAR
]
```

### 5.2 `config/settings/base.py` — Agregar a `NINJA_EXTRA.INJECTOR_MODULES`

```python
NINJA_EXTRA = {
    "INJECTOR_MODULES": [
        # ... existentes ...
        "modules.inscripciones.di.InscripcionesModule",  # AGREGAR
    ]
}
```

### 5.3 `config/api.py` — Registrar controllers

```python
# Agregar import:
from modules.inscripciones.presentation.controllers.disciplina_controller import (
    DisciplinaController,
)
from modules.inscripciones.presentation.controllers.inscripcion_controller import (
    InscripcionController,
)

# En api.register_controllers(...) al final:
api.register_controllers(DisciplinaController)
api.register_controllers(InscripcionController)
```

---

## 6. Orden de Migraciones

### Fase 1 — `usuarios` (extensión)

```bash
.venv\Scripts\python.exe manage.py makemigrations usuarios --settings=config.settings.development
.venv\Scripts\python.exe manage.py migrate --settings=config.settings.development
```

### Fase 2 — `inscripciones`

```bash
.venv\Scripts\python.exe manage.py makemigrations inscripciones --settings=config.settings.development
.venv\Scripts\python.exe manage.py migrate --settings=config.settings.development
```

> **Importante:** `ParticipacionDisciplina` tiene `UniqueConstraint(evento, disciplina, persona)`. La migration debe incluir esta constraint.

---

## 7. Verificación Post-Creación

```bash
# 1. Verificar que Django cargue sin errores
.venv\Scripts\python.exe manage.py check --settings=config.settings.development

# 2. Verificar que las apps estén instaladas
.venv\Scripts\python.exe manage.py check --deploy --settings=config.settings.development

# 3. Verificar migrations (dry-run)
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.settings.development

# 4. Listar rutas registradas
.venv\Scripts\python.exe manage.py show_urls --settings=config.settings.development 2>$null || echo "Instalar django-extensions para show_urls"

# 5. Listar modelos registrados en admin
.venv\Scripts\python.exe manage.py shell -c "from django.apps import apps; [(print(m.label)) for m in apps.get_models() if 'inscripcion' in m.label or 'persona' in m.label]" --settings=config.settings.development
```

---

## 8. Resumen de Comandos para Apply

```bash
# === ENTORNO ===
$ cd C:\Users\Usuario\Desktop\Aplicaciones\CST\Salesianos\backend
$ PYTHON=.venv\Scripts\python.exe

# === FASES DE USUARIOS ===
# 1. Agregar Persona al módulo existente
$ PYTHON manage.py makemigrations usuarios --settings=config.settings.development
$ PYTHON manage.py migrate --settings=config.settings.development

# === CREAR INSCRIPCIONES ===
# 1. Crear estructura de carpetas (manual)
# 2. Registrar en settings/base.py
# 3. Registrar di.py en NINJA_EXTRA
# 4. Registrar controllers en config/api.py
# 5. Crear modelos (por orden de dependencia)
$ PYTHON manage.py makemigrations inscripciones --settings=config.settings.development
$ PYTHON manage.py migrate --settings=config.settings.development

# === VERIFICACIÓN ===
$ PYTHON manage.py check --settings=config.settings.development
$ PYTHON manage.py show_urls --settings=config.settings.development
```

---

## 9. Riesgos y Gotchas

| # | Riesgo | Mitigación |
|---|--------|------------|
| G1 | `manage.py startapp` genera estructura incompatible con la arquitectura CAM | Usar copia de `entidades` como base o crear estructura manualmente |
| G2 | Olvidar `--settings=config.settings.development` y ejecutar contra producción | Crear alias o script wrapper; el default de `manage.py` es `production` |
| G3 | Migration order wrong — `inscripciones` referencing `usuarios.Persona` before it exists | Ejecutar `makemigrations` de `usuarios` primero, luego `inscripciones` |
| G4 | UniqueConstraint en `ParticipacionDisciplina` requiere que `evento` y `disciplina` existan como campos directos | Crear tabla con campos explícitos (no derivarlos de la cadena transitiva) |
| G5 | `OneToOneField` entre `Usuario` y `Persona` puede crear ciclos de importación | Usar string reference `"usuarios.Persona"` en el FK |
| G6 | SQLite no soporta `ExclusionConstraint` — no implementar en MVP | Usar validación en servicio + UniqueConstraint simple |

---

## 10. Próximo Paso: `sdd-apply`

Una vez completado este plan de exploración, el flujo para el próximo paso es:

1. **Extender `usuarios` con `Persona`** (modelo + constants + exceptions + admin + tests factory)
2. **Crear estructura base de `inscripciones`** (carpetas + apps.py + di.py + models.py re-export)
3. **Crear modelos de `inscripciones`** en orden: Disciplina → Evento → Paquete → Inscripcion → Equipo
4. **Ejecutar migrations** en orden
5. **Registrar en settings, di, api**
6. **Verificar** con `check` y `show_urls`

---

*Documento generado como resultado de SDD explore phase.*
