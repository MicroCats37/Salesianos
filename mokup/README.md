# Salesianos FEST 2026

Versión estática y compartible de la plataforma web de preinscripción deportiva de Salesianos FEST 2026.

## Vista local

```bash
python3 -m http.server 8080
```

Luego abre `http://localhost:8080`.

## Publicación con GitHub Pages

El repositorio incluye un flujo automático en `.github/workflows/pages.yml`. En GitHub, abre **Settings → Pages** y selecciona **GitHub Actions** como fuente. Cada actualización de la rama `main` publicará el sitio.

## Alcance de esta exportación

- Incluye la interfaz, estilos, imágenes y comportamiento del formulario visibles en la versión publicada.
- Es una exportación estática compilada, adecuada para demostración y GitHub Pages.
- El pago con izipay continúa deshabilitado y esta versión no procesa ni almacena tarjetas.
- Para un sistema productivo con base de datos, validación administrativa y pagos reales se requiere implementar el backend descrito en el documento técnico maestro.

## Sitio original

https://salesianos-fest-2026-registro.ciplimai.chatgpt.site

Todos los derechos reservados. No se concede una licencia de reutilización del logotipo ni de los recursos de marca.
