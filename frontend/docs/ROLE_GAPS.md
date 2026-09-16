# Gaps — Role-Based Access Control (Salesianos MVP)

> **Origen:** `sdd-explore` ejecutado el 2026-09-13.
> **Cambio:** `salesianos-mvp-foundation`
> **Pregunta del usuario:** "El admin user no debería poder armar equipos — solo el responsable. Solo el responsable debe ver el login y armar su equipo."

---

## 1. Estado actual

La app define **3 roles** en `users.ts`:

```ts
export const userRoles = ['responsable', 'admin_comite', 'admin_finanzas'] as const;
```

El seed crea un admin:

```ts
rol: 'admin_comite'  // el Comité del Salesianos FEST
```

**Pero NO existe control de acceso basado en roles (RBAC) en ningún lado.** Solo se verifica que el usuario esté autenticado (`hasAuth`), no qué rol tiene.

---

## 2. Los 7 Gaps

### Gap 1 — `/login` no redirige admins

**Archivo:** `src/proxy.ts` línea 16

**Comportamiento actual:** Cuando un admin Comité inicia sesión, es redirigido a `/dashboard` (igual que un responsable).

**Esperado:** Admin Comité → redirigido a `/admin/comite/inscripciones`.

**Fix:** Leer el rol del JWT o de la sesión y redirigir según corresponda.

---

### Gap 2 — `/register` accesible para admins

**Archivo:** `src/app/(auth)/register/page.tsx`

**Comportamiento actual:** Cualquier usuario autenticado (incluso admin) puede abrir `/register` y crear una segunda cuenta de responsable.

**Esperado:** Si ya autenticado, redirigir según rol. Si admin, a `/admin/comite/inscripciones`.

---

### Gap 3 — `/inscripcion` accesible para admins

**Archivo:** `src/app/(protected)/inscripcion/page.tsx`

**Comportamiento actual:** El InscripcionWizard se renderiza para CUALQUIER usuario autenticado, sin importar su rol.

**Esperado:** Solo `rol === 'responsable'` puede ver el wizard. Admin debería ser redirigido a su panel.

**Riesgo:** Si un admin abre el wizard y envía el formulario, crea una inscripción a nombre suyo — no tiene sentido administrativo.

---

### Gap 4 — `/dashboard` no diferencia por rol

**Archivo:** `src/app/(protected)/dashboard/page.tsx`

**Comportamiento actual:** Tanto responsable como admin ven la misma pantalla "Bienvenido" con mensaje genérico.

**Esperado:** Responsable → ve su inscripción + estado. Admin → redirigido a `/admin/comite/inscripciones`.

---

### Gap 5 — `/admin/comite/inscripciones` accesible para no-admins

**Archivo:** `src/app/(protected)/admin/comite/inscripciones/page.tsx`

**Comportamiento actual:** Cualquier usuario autenticado (incluido un responsable) podría acceder si conoce la URL.

**Esperado:** Solo `rol === 'admin_comite'` o `rol === 'admin_finanzas'` pueden acceder.

**Riesgo:** Un responsable podría ver la lista de TODAS las inscripciones de la plataforma, incluyendo DNIs y contactos de otros equipos.

---

### Gap 6 — `createInscripcionAction` no valida el caller

**Archivo:** `src/app/actions/inscripcion/create.ts`

**Comportamiento actual:** El Server Action recibe `userId` del cliente. Nunca verifica que ese `userId` corresponda a la sesión actual ni que el usuario sea `responsable`.

**Esperado:**
- Validar que el usuario está autenticado (sesión válida)
- Validar que el `userId` del payload coincide con el de la sesión
- Validar que el rol es `responsable`

**Riesgo crítico de seguridad:** Un atacante podría enviar `userId: '<cualquier-user-id>'` y crear una inscripción a nombre de otro usuario.

---

### Gap 7 — `InscripcionWizard` no valida rol client-side

**Archivo:** `src/features/inscripcion/components/InscripcionWizard.tsx`

**Comportamiento actual:** El wizard se renderiza para cualquier usuario autenticado.

**Esperado:** Si `useAuthUser().rol !== 'responsable'`, mostrar mensaje "Esta sección es solo para responsables" + link al panel admin (si aplica).

**Nota:** Esto es **defense-in-depth** — el guard real es server-side (Gap 6). El guard client-side solo mejora UX.

---

## 3. Cambios propuestos

### Capa 1: Server-side (autoridad)

| Archivo | Cambio |
|---------|--------|
| `src/lib/auth/get-session.ts` (nuevo) | Helper para obtener sesión actual con rol: `getCurrentSession()` |
| `src/proxy.ts` | Después de verificar `hasAuth`, leer cookie, verificar JWT, redirigir según rol |
| `src/app/actions/inscripcion/create.ts` | Validar sesión + rol + que `userId` coincide |
| `src/app/actions/inscripcion/update-status.ts` | Validar sesión + rol = `admin_comite` |

### Capa 2: Server Components (guards de página)

| Archivo | Cambio |
|---------|--------|
| `src/lib/auth/require-role.ts` (nuevo) | `await requireRole('responsable' \| 'admin_comite' \| 'admin_finanzas')` que redirige si no coincide |
| `src/app/(protected)/inscripcion/page.tsx` | `await requireRole('responsable')` |
| `src/app/(protected)/dashboard/page.tsx` | Redirect según rol (responsable → ver inscripción; admin → /admin/comite/inscripciones) |
| `src/app/(protected)/admin/comite/inscripciones/page.tsx` | `await requireRole('admin_comite', 'admin_finanzas')` |

### Capa 3: Client-side (UX)

| Archivo | Cambio |
|---------|--------|
| `src/features/inscripcion/components/InscripcionWizard.tsx` | Si `useAuthUser().rol !== 'responsable'`, render mensaje + link |
| `src/app/(auth)/login/page.tsx` | Después del login, redirigir según rol (responsable → /dashboard; admin → /admin/comite/inscripciones) |
| `src/app/(auth)/register/page.tsx` | Si ya autenticado, redirigir según rol |

---

## 4. Helpers a crear

### `src/lib/auth/get-session.ts`

```ts
import { cookies } from 'next/headers';
import { AUTH_COOKIE_NAME } from '@/infra/auth/cookies';
import { hashToken, verifyAccessToken } from '@/infra/auth/jwt';
import { DrizzleSesionRepository, DrizzleUserRepository } from '@/infra/drizzle/repositories';
import { PermissionDeniedError } from '@/core/errors';

export interface Session {
  userId: string;
  email: string;
  rol: 'responsable' | 'admin_comite' | 'admin_finanzas';
}

export async function getCurrentSession(): Promise<Session | null> {
  const token = (await cookies()).get(AUTH_COOKIE_NAME)?.value;
  if (!token) return null;
  const payload = await verifyAccessToken(token);
  if (!payload) return null;
  const tokenHash = await hashToken(token);
  const sesion = await new DrizzleSesionRepository().findByTokenHash(tokenHash);
  if (!sesion || sesion.revokedAt || sesion.expiresAt < new Date()) return null;
  const user = await new DrizzleUserRepository().findById(payload.sub);
  if (!user) return null;
  return { userId: user.id, email: user.email, rol: user.rol };
}
```

### `src/lib/auth/require-role.ts`

```ts
import { redirect } from 'next/navigation';
import { getCurrentSession } from './get-session';

export async function requireRole(...allowed: Array<'responsable' | 'admin_comite' | 'admin_finanzas'>) {
  const session = await getCurrentSession();
  if (!session) redirect('/login');
  if (!allowed.includes(session.rol)) {
    // Redirect to the right panel based on rol
    if (session.rol === 'admin_comite' || session.rol === 'admin_finanzas') {
      redirect('/admin/comite/inscripciones');
    } else {
      redirect('/dashboard');
    }
  }
  return session;
}
```

---

## 5. Riesgos

| # | Riesgo | Mitigación |
|---|--------|------------|
| 1 | El rol se almacena en el JWT. Si el admin cambia de rol, el token sigue siendo válido hasta que expire | El servidor SIEMPRE valida contra DB en cada Server Action. JWT es solo para identidad. |
| 2 | `getCurrentSession` hace 2 queries a DB por request | Aceptable para MVP. Optimizar con Redis después si hay volumen. |
| 3 | Si el admin user NO se siembra correctamente, no hay forma de hacer login admin | El seed actual crea 1 admin (`admin@salesianosfest.com` / `Admin2026!`) — verificar |

---

## 6. Tests de aceptación

1. Responsable hace login → redirige a `/dashboard` → ve InscripcionWizard
2. Admin Comité hace login → redirige a `/admin/comite/inscripciones` → ve panel admin
3. Responsable intenta acceder a `/admin/comite/inscripciones` → redirige a `/dashboard`
4. Admin intenta acceder a `/inscripcion` → redirige a `/admin/comite/inscripciones`
5. Responsable intenta enviar `userId: '<otro-user-id>'` en `createInscripcionAction` → Server Action rechaza con 403
6. Admin intenta enviar `createInscripcionAction` → rechaza con 403
7. Admin intenta actualizar estado de inscripción → funciona (rol permitido)
8. Responsable intenta actualizar estado de inscripción → rechaza con 403

---

## Próximo paso del SDD

`sdd-propose` para redactar propuesta formal del cambio.
