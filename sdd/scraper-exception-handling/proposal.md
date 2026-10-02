# Proposal: Scraper Exception Handling

## Intent

Definir y estructurar una jerarquía de excepciones en el microservicio `worker/scraper` para preservar el contexto de los errores (red, timeouts, parsing), clasificar su severidad de forma estática (retryable vs non-retryable) y aplicar una política de reintentos en el cliente consumidos (`RealConsultaExternaClient`). Esto evitará la pérdida de información útil al traducir errores y mitigará fallos por caídas transitorias de los portales externos.

## Scope

### In Scope
- Implementar jerarquía de excepciones estructuradas en el `worker/scraper` (`ScraperTimeoutError`, `ScraperUnavailableError`, `ScraperFormatError`, además de la base `ScraperError` y `DocumentNotFoundError`).
- Configurar traducción de estas excepciones en FastAPI (`main.py`) para emitir respuestas JSON estructuradas con metadatos de error (código, mensaje, flag `retryable`).
- Clasificar los errores estáticamente en retryable (timeout, red, 503) y non-retryable (format error, 404, validación).
- Implementar una política de reintentos en el cliente Django `RealConsultaExternaClient` para los errores clasificados como retryable.
- Añadir logging estructurado y contextual en el scraper antes de elevar las excepciones, y en el manejador global.
- Añadir pruebas para escenarios de error en el scraper (tiempos de espera, cambios de formato, fallos de red).

### Out of Scope
- Unificar excepciones de dominio (`SunatNotFoundError`, `ReniecNotFoundError`) entre módulos (evitando abstracciones compartidas prematuras).
- Alterar la lógica interna de extracción y parseo mediante BeautifulSoup más allá de cómo se capturan y envuelven los fallos.
- Agregar un backend de observabilidad (Prometheus/Jaeger); solo se usará logging estándar.

## Capabilities

> This section is the CONTRACT between proposal and specs phases.

### New Capabilities
- `scraper-exceptions`: Jerarquía estructurada para preservar el contexto del fallo original y propagarlo al límite del servicio.
- `scraper-retry-policy`: Política en el cliente HTTP (`RealConsultaExternaClient`) para absorber fallas transitorias de red de forma automática.

### Modified Capabilities
- `consulta-externa-client`: Traducción HTTP-a-Dominio actualizada para mapear los nuevos flags de `retryable` y extraer información detallada del error original enviado por el scraper.

## Approach

1. **Jerarquía (Scraper):** Crear las clases solicitadas heredando de una base `ScraperError`. Cada una admitirá información clave (e.g. tipo de timeout, selector fallido).
2. **FastAPI (Scraper):** Interceptar las excepciones personalizadas en `main.py`. Generar respuestas 502/503/504 según corresponda, devolviendo un JSON que incluya la bandera `retryable` derivada del tipo de excepción.
3. **Logging (Scraper):** Inyectar logs que registren el traceback y los parámetros del documento antes de la interrupción del flujo.
4. **Política de Reintentos (Django):** El cliente `RealConsultaExternaClient` capturará los errores de red (usando `httpx`) y las respuestas HTTP de error. Si la condición (o el payload JSON) indica que es retryable, ejecutará hasta un número limitado de reintentos antes de transformarlo en el `HttpError` de Ninja, respetando el contrato de arquitectura actual de Django.
5. **Pruebas:** Añadir test unitarios para el wrapper HTTP, mockeando las excepciones de la biblioteca subyacente y validando que el cliente de Django reintenta adecuadamente.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `worker/scraper/documento_scraper.py` | Modified | Nuevas clases de excepciones y refactorización de `raise` para usar la jerarquía. |
| `worker/scraper/main.py` | Modified | Nuevos manejadores de error globales de FastAPI para traducción HTTP y logging. |
| `backend/modules/entidades/infrastructure/services.py` | Modified | Adaptación de `RealConsultaExternaClient` con lógica de reintento. |
| `worker/scraper/tests/test_api.py` | Modified | Nuevos test cases comprobando `retryable`, respuestas y timeouts. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cambios en la estructura del error JSON rompan el cliente | Medio | Mantener el campo `detail` clásico en la respuesta HTTP como fallback, y usar propiedades extendidas explícitas como `error_code` y `retryable`. |
| Reintentos bloqueen la ejecución sincrónica | Bajo | El cliente usa `httpx` async; limitar el número de intentos (max 2) y el timeout por intento a un nivel seguro. |

## Rollback Plan

Revertir a la versión anterior de `documento_scraper.py` y `main.py` para anular la nueva jerarquía. Descartar el cliente modificado en Django y volver a la implementación sin reintentos explícitos. 

## Dependencies

- No se agregan nuevas bibliotecas (se usará el sistema estándar de excepciones y reintentos basados en loop/httpx nativo, a menos que se prefiera `tenacity` que se añadiría solo si el proyecto ya lo soporta).

## Success Criteria

- [ ] Los logs del scraper muestran trazas útiles y contexto (documento consultado, tipo de timeout o fallo de red) cuando el scraper falla.
- [ ] Errores de parsing (`ScraperFormatError`) y 404 no causan reintentos automáticos.
- [ ] Caídas de red o timeouts (`ScraperTimeoutError`, `ScraperUnavailableError`) gatillan el reintento configurado en el cliente Django.
- [ ] La batería de pruebas en `worker/scraper/tests/test_api.py` cubre específicamente los caminos de error.