"""
Módulo `usuarios` — identidad civil, cuentas, roles y titularidad.

Freeze: `FREEZE-ID-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-03-identity-titularidad.md`

Este módulo es el dueño de la identidad del festival:

- `Persona` — identidad civil. Existe SIN cuenta.
- `Usuario` — credenciales y sesión. La relación con `Persona` es OPCIONAL.
- Grupos Django `Normal` y `Administrador` — los dos roles funcionales.
- Interfaz de titularidad — las cuatro titularidades congeladas.
- Resolver local → fuente externa — persistencia diferida y anti-duplicado.

Nada de este módulo autoriza una operación comercial: la titularidad se
comprueba sobre el recurso que cada módulo dueño aporta
(`FR-03` §2.1 regla 1).
"""
