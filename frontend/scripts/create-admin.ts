#!/usr/bin/env tsx
/**
 * CLI script to create or update an admin/superuser.
 *
 * Usage:
 *   npm run admin:create -- --dni 12345678 --password "secret" --nombre "John" --apellido "Doe"
 *   npm run admin:create -- --dni 12345678 --password "secret" --email "admin@example.com" --role admin_finanzas
 *
 * Environment variables (alternative to CLI args):
 *   ADMIN_DNI       - Required: DNI number
 *   ADMIN_PASSWORD  - Required: password
 *   ADMIN_EMAIL     - Optional: email (defaults to admin@local)
 *   ADMIN_NOMBRE    - Optional: first name
 *   ADMIN_APELLIDO  - Optional: last name
 *   ADMIN_ROLE      - Optional: admin_comite | admin_finanzas (default: admin_comite)
 *
 * Security: No public route. CLI-only. Passwords are hashed with bcrypt.
 */

import "dotenv/config";
import { hash } from "bcryptjs";
import { eq } from "drizzle-orm";
import { db, schema } from "@/infra/drizzle/client";
import type { UserRole } from "@/infra/drizzle/schema";

const VALID_ROLES: UserRole[] = ["admin_comite", "admin_finanzas"];

interface Args {
  dni?: string;
  password?: string;
  email?: string;
  nombre?: string;
  apellido?: string;
  role?: UserRole;
}

function parseArgs(): Args {
  const args: Args = {};
  const cliArgs = process.argv.slice(2);

  for (let i = 0; i < cliArgs.length; i++) {
    const arg = cliArgs[i];
    if (arg === "--dni" && i + 1 < cliArgs.length) args.dni = cliArgs[++i];
    else if (arg === "--password" && i + 1 < cliArgs.length)
      args.password = cliArgs[++i];
    else if (arg === "--email" && i + 1 < cliArgs.length)
      args.email = cliArgs[++i];
    else if (arg === "--nombre" && i + 1 < cliArgs.length)
      args.nombre = cliArgs[++i];
    else if (arg === "--apellido" && i + 1 < cliArgs.length)
      args.apellido = cliArgs[++i];
    else if (arg === "--role" && i + 1 < cliArgs.length)
      args.role = cliArgs[++i] as UserRole;
    else if (arg === "--help" || arg === "-h") {
      console.log(`Usage: npm run admin:create -- [options]
Options:
  --dni <value>       DNI number (required)
  --password <value>  Password (required)
  --email <value>     Email (optional, default: admin@local)
  --nombre <value>    First name (optional)
  --apellido <value>  Last name (optional)
  --role <value>      Role: admin_comite | admin_finanzas (optional, default: admin_comite)
Environment variables also supported: ADMIN_DNI, ADMIN_PASSWORD, ADMIN_EMAIL, ADMIN_NOMBRE, ADMIN_APELLIDO, ADMIN_ROLE
`);
      process.exit(0);
    }
  }

  // Override with env vars if not provided via CLI
  args.dni = args.dni ?? process.env.ADMIN_DNI;
  args.password = args.password ?? process.env.ADMIN_PASSWORD;
  args.email = args.email ?? process.env.ADMIN_EMAIL ?? "admin@local";
  args.nombre = args.nombre ?? process.env.ADMIN_NOMBRE ?? "Admin";
  args.apellido = args.apellido ?? process.env.ADMIN_APELLIDO ?? "Local";
  args.role =
    args.role ?? (process.env.ADMIN_ROLE as UserRole) ?? "admin_comite";

  return args;
}

function validateArgs(args: Args): string | null {
  if (!args.dni?.trim()) return "DNI is required (--dni or ADMIN_DNI)";
  if (!args.password?.trim())
    return "Password is required (--password or ADMIN_PASSWORD)";
  if (args.password.length < 8) return "Password must be at least 8 characters";
  if (args.role && !VALID_ROLES.includes(args.role)) {
    return `Invalid role: ${args.role}. Must be one of: ${VALID_ROLES.join(", ")}`;
  }
  return null;
}

async function createOrUpdateAdmin(args: Args) {
  const dni = args.dni?.trim() ?? "";
  const password = args.password?.trim() ?? "";
  const email = args.email?.toLowerCase().trim() ?? "admin@local";
  const nombre = args.nombre?.trim() ?? "Admin";
  const apellido = args.apellido?.trim() ?? "Local";
  const role: UserRole = args.role ?? "admin_comite";

  console.log(`Creating/updating admin user:`);
  console.log(`  DNI: ${dni}`);
  console.log(`  Email: ${email}`);
  console.log(`  Nombre: ${nombre} ${apellido}`);
  console.log(`  Role: ${role}`);

  // Find existing persona by DNI
  const existingPersonaByDNI = await db
    .select()
    .from(schema.personas)
    .where(eq(schema.personas.numeroDocumento, dni))
    .limit(1);

  // Find existing user by email or DNI
  const existingByEmail = await db
    .select()
    .from(schema.users)
    .where(eq(schema.users.email, email))
    .limit(1);

  const existingByDNI = existingPersonaByDNI[0]
    ? await db
        .select()
        .from(schema.users)
        .where(eq(schema.users.personaId, existingPersonaByDNI[0].id))
        .limit(1)
    : [];

  const existingUser = existingByDNI[0] ?? existingByEmail[0];

  const passwordHash = await hash(password, 12);

  if (!existingUser) {
    // Create new persona and user
    const persona =
      existingPersonaByDNI[0] ??
      (
        await db
          .insert(schema.personas)
          .values({
            tipoDocumento: "DNI",
            numeroDocumento: dni,
            nombres: nombre,
            apellidos: apellido,
          })
          .returning()
      )[0];

    await db.insert(schema.users).values({
      personaId: persona.id,
      email,
      passwordHash,
      rol: role,
    });

    console.log(`✓ Admin user created with ID: ${persona.id}`);
  } else {
    // Update existing user
    await db
      .update(schema.users)
      .set({
        passwordHash,
        rol: role,
        email,
        updatedAt: new Date(),
      })
      .where(eq(schema.users.id, existingUser.id));

    // Update persona if exists
    if (existingPersonaByDNI[0]) {
      await db
        .update(schema.personas)
        .set({
          tipoDocumento: "DNI",
          numeroDocumento: dni,
          nombres: nombre,
          apellidos: apellido,
          updatedAt: new Date(),
        })
        .where(eq(schema.personas.id, existingPersonaByDNI[0].id));
    }

    console.log(`✓ Admin user updated: ${existingUser.id}`);
  }

  console.log(`\nAdmin creation complete.`);
  console.log(`IMPORTANT: Save these credentials securely:`);
  console.log(`  DNI: ${dni}`);
  console.log(`  Password: ${password}`);
  console.log(`  Role: ${role}`);
}

async function main() {
  const args = parseArgs();
  const error = validateArgs(args);

  if (error) {
    console.error(`Error: ${error}`);
    console.error(`Run with --help for usage information.`);
    process.exit(1);
  }

  try {
    await createOrUpdateAdmin(args);
    process.exit(0);
  } catch (err) {
    console.error("Failed to create admin:", err);
    process.exit(1);
  }
}

main();
