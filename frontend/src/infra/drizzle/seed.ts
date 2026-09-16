import "dotenv/config";
import { hash } from "bcryptjs";
import { eq } from "drizzle-orm";
import { db, schema } from "@/infra/drizzle/client";

async function seedBases() {
  const version = "BASES-SF26-2026-09-06";
  const existing = await db
    .select()
    .from(schema.bases)
    .where(eq(schema.bases.version, version))
    .limit(1);
  if (existing.length === 0) {
    await db.insert(schema.bases).values({
      version,
      aprobadoEn: new Date("2026-09-05"),
      contenidoUrl: null,
      activo: true,
    });
    console.log(`✓ bases: ${version}`);
  } else {
    console.log(`• bases: ${version} already exists`);
  }
}

async function seedDisciplinas() {
  const disciplinasData = [
    { codigo: "fulbito_var" as const, nombre: "Fulbito Varones", maxJugadores: 12 },
    { codigo: "fulbito_dam" as const, nombre: "Fulbito Mujeres", maxJugadores: 12 },
    { codigo: "voley_mix" as const, nombre: "Voley Mixto", maxJugadores: 12 },
    { codigo: "basket_var" as const, nombre: "Basket Varones", maxJugadores: 10 },
  ];

  for (const data of disciplinasData) {
    const existing = await db
      .select()
      .from(schema.disciplinas)
      .where(eq(schema.disciplinas.codigo, data.codigo))
      .limit(1);
    if (existing.length === 0) {
      await db.insert(schema.disciplinas).values(data).onConflictDoNothing();
      console.log(`✓ disciplina: ${data.codigo}`);
    } else {
      console.log(`• disciplina: ${data.codigo} already exists`);
    }
  }
}

async function seedCategorias() {
  const [fulbitoVar] = await db
    .select()
    .from(schema.disciplinas)
    .where(eq(schema.disciplinas.codigo, "fulbito_var"))
    .limit(1);
  const [fulbitoDam] = await db
    .select()
    .from(schema.disciplinas)
    .where(eq(schema.disciplinas.codigo, "fulbito_dam"))
    .limit(1);
  const [voleyMix] = await db
    .select()
    .from(schema.disciplinas)
    .where(eq(schema.disciplinas.codigo, "voley_mix"))
    .limit(1);
  const [basketVar] = await db
    .select()
    .from(schema.disciplinas)
    .where(eq(schema.disciplinas.codigo, "basket_var"))
    .limit(1);

  if (!fulbitoVar || !fulbitoDam || !voleyMix || !basketVar) {
    throw new Error("Disciplinas not found — run seedDisciplinas first");
  }

  const categoriasData = [
    // Fulbito Varones
    { disciplinaId: fulbitoVar.id, codigo: "junior" as const, nombre: "Junior", anioMin: 2012, anioMax: 2025 },
    { disciplinaId: fulbitoVar.id, codigo: "senior" as const, nombre: "Senior", anioMin: 1998, anioMax: 2011 },
    { disciplinaId: fulbitoVar.id, codigo: "master" as const, nombre: "Master", anioMin: 1987, anioMax: 1997 },
    { disciplinaId: fulbitoVar.id, codigo: "super_master" as const, nombre: "Super Master", anioMin: 1970, anioMax: 1986 },
    // Fulbito Mujeres
    { disciplinaId: fulbitoDam.id, codigo: "junior" as const, nombre: "Junior", anioMin: 2001, anioMax: 2024 },
    { disciplinaId: fulbitoDam.id, codigo: "master" as const, nombre: "Master", anioMin: 1975, anioMax: 2000 },
    // Voley Mixto
    { disciplinaId: voleyMix.id, codigo: "junior" as const, nombre: "Junior", anioMin: 2012, anioMax: 2025 },
    { disciplinaId: voleyMix.id, codigo: "senior" as const, nombre: "Senior", anioMin: 1998, anioMax: 2011 },
    { disciplinaId: voleyMix.id, codigo: "master" as const, nombre: "Master", anioMin: 1975, anioMax: 1986 },
    // Basket Varones
    { disciplinaId: basketVar.id, codigo: "junior" as const, nombre: "Junior", anioMin: 2012, anioMax: 2025 },
    { disciplinaId: basketVar.id, codigo: "senior" as const, nombre: "Senior", anioMin: 1998, anioMax: 2011 },
    { disciplinaId: basketVar.id, codigo: "master" as const, nombre: "Master", anioMin: 1970, anioMax: 1997 },
  ];

  for (const data of categoriasData) {
    const existing = await db
      .select()
      .from(schema.categorias)
      .where(eq(schema.categorias.disciplinaId, data.disciplinaId))
      .limit(1);

    const filtered = existing.filter((c: any) => c.codigo === data.codigo);
    if (filtered.length === 0) {
      await db.insert(schema.categorias).values(data).onConflictDoNothing();
      console.log(`✓ categoria: ${data.codigo} (${data.nombre})`);
    } else {
      console.log(`• categoria: ${data.codigo} (${data.nombre}) already exists`);
    }
  }
}

async function seedPromociones() {
  const currentYear = new Date().getFullYear();
  const promocionesData = Array.from({ length: currentYear - 1970 + 1 }, (_, index) => {
    const anio = 1970 + index;
    return { anio, colegio: "ma" as const, nombre: `Promoción ${anio}`, activa: true };
  });

  for (const data of promocionesData) {
    const existing = await db
      .select()
      .from(schema.promociones)
      .where(eq(schema.promociones.anio, data.anio))
      .limit(1);
    if (existing.length === 0) {
      await db.insert(schema.promociones).values(data).onConflictDoNothing();
      console.log(`✓ promocion: ${data.anio}`);
    } else {
      console.log(`• promocion: ${data.anio} already exists`);
    }
  }
}

async function seedAdmin() {
  const adminEmail = "admin@salesianosfest.com";
  const passwordHash = await hash("admin123", 10);
  const existingByEmail = await db
    .select()
    .from(schema.users)
    .where(eq(schema.users.email, adminEmail))
    .limit(1);
  const existingPersonaByDocument = await db
    .select()
    .from(schema.personas)
    .where(eq(schema.personas.numeroDocumento, "00000000"))
    .limit(1);
  const existingByDocument = existingPersonaByDocument[0]
    ? await db
        .select()
        .from(schema.users)
        .where(eq(schema.users.personaId, existingPersonaByDocument[0].id))
        .limit(1)
    : [];
  const admin = existingByDocument[0] ?? existingByEmail[0];

  if (!admin) {
    const persona =
      existingPersonaByDocument[0] ??
      (
        await db
          .insert(schema.personas)
          .values({
            tipoDocumento: "DNI",
            numeroDocumento: "00000000",
            nombres: "Comité",
            apellidos: "Salesianos",
            telefono: "999999999",
          })
          .returning()
      )[0];

    await db.insert(schema.users).values({
      personaId: persona.id,
      email: adminEmail,
      passwordHash,
      rol: "admin_comite",
    });
    console.log("✓ admin user created");
  } else {
    const adminPersonaId = existingByDocument[0]
      ? admin.personaId
      : existingPersonaByDocument[0]?.id ?? admin.personaId;
    await db
      .update(schema.users)
      .set({
        passwordHash,
        rol: "admin_comite",
        updatedAt: new Date(),
        ...(adminPersonaId !== admin.personaId ? { personaId: adminPersonaId } : {}),
        ...(existingByEmail.length === 0 || existingByEmail[0].id === admin.id ? { email: adminEmail } : {}),
      })
      .where(eq(schema.users.id, admin.id));

    const documentBelongsToAdmin = existingPersonaByDocument[0]?.id === adminPersonaId;
    if (!existingPersonaByDocument[0] || documentBelongsToAdmin) {
      await db
        .update(schema.personas)
        .set({
          tipoDocumento: "DNI",
          numeroDocumento: "00000000",
          nombres: "Comité",
          apellidos: "Salesianos",
          telefono: "999999999",
          updatedAt: new Date(),
        })
        .where(eq(schema.personas.id, adminPersonaId));
    }
    console.log("• admin user updated");
  }
}

async function main() {
  console.log(`[DB_DIALECT=${process.env.DB_DIALECT ?? "sqlite"}] Starting seed...`);
  await seedBases();
  await seedDisciplinas();
  await seedCategorias();
  await seedPromociones();
  await seedAdmin();
  console.log("Seed complete.");
}

main()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
