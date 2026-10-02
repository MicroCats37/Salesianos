# Backend - Salesianos FEST 2026

Este es el backend del proyecto, construido con **Django**, **Django Ninja Extra** y empaquetado con **uv**.

El proyecto completo corre con Docker Compose (`salesianos_backend`).

## Inicialización y Seeds (Datos base)

Para inicializar el sistema desde cero (por ejemplo, después de montar la base de datos por primera vez), es necesario cargar los datos base (seeds).

Todos los comandos se ejecutan **dentro del contenedor** usando `docker exec`.

### 1. Crear el Administrador

Crea el usuario superadmin (`username: admin`, `password: admin`, vinculado a un DNI de sistema `00000000`).

```bash
docker exec -it salesianos_backend uv run python manage.py create_admin
```

> **Nota:** Si la contraseña fue cambiada y querés resetearla al valor por defecto, podés usar el flag `--force`:
> `docker exec -it salesianos_backend uv run python manage.py create_admin --force`

### 2. Cargar Promociones y Paquetes (Precios)

Este comando carga automáticamente toda la estructura base para que las inscripciones funcionen:
- **Promociones** (Años de egreso: 1970 a 2026).
- **Disciplinas** y **Categorías** (Fulbito, Vóley, Básquet, Súper Máster, etc.).
- **Paquetes y Precios** (Deportistas, Delegados, con sus respectivos precios regulares y promocionales).
- **El Evento Principal** ("Salesianos FEST 2026").

```bash
docker exec -it salesianos_backend uv run python manage.py seed_inscripciones
```

> **Nota:** Ambos comandos son **idempotentes**. Esto significa que si los ejecutás más de una vez, no van a duplicar datos, solo van a actualizar los existentes si algo cambió.

## Migraciones

Si hacés cambios en los modelos y necesitás correr las migraciones en Docker:

```bash
# Para aplicar las migraciones
docker exec -it salesianos_backend uv run python manage.py migrate

# Para crear nuevas migraciones (si desarrollás)
docker exec -it salesianos_backend uv run python manage.py makemigrations
```
