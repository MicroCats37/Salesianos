import "dotenv/config";
import { eq } from "drizzle-orm";
import { createInscripcion } from "../src/core/use-cases/inscripcion";
import { db } from "../src/infra/drizzle/client";
import {
  DrizzleBaseRepository,
  DrizzleCategoriaRepository,
  DrizzleDisciplinaRepository,
  DrizzleInscripcionRepository,
  DrizzlePromocionRepository,
} from "../src/infra/drizzle/repositories";
import {
  bases,
  disciplinas,
  promociones,
  users,
} from "../src/infra/drizzle/schema";

async function main() {
  console.log("=== TEST REAL: createInscripcion use-case ===\n");

  const promo = db
    .select()
    .from(promociones)
    .where(eq(promociones.activa, true))
    .all()[0];
  const base = db.select().from(bases).where(eq(bases.activo, true)).all()[0];
  const disc = db
    .select()
    .from(disciplinas)
    .where(eq(disciplinas.codigo, "fulbito_var"))
    .all()[0];
  const user = db
    .select()
    .from(users)
    .where(eq(users.email, "cap2@test.com"))
    .all()[0];

  if (!promo || !base || !disc || !user) {
    console.error("Faltan datos base. Corré el seed.");
    process.exit(1);
  }

  console.log(
    "promo:",
    promo.anio,
    "| base:",
    base.version,
    "| disc:",
    disc.codigo,
    "| user:",
    user.email,
  );

  const deps = {
    inscripcionRepository: new DrizzleInscripcionRepository(),
    promocionRepository: new DrizzlePromocionRepository(),
    disciplinaRepository: new DrizzleDisciplinaRepository(),
    categoriaRepository: new DrizzleCategoriaRepository(),
    baseRepository: new DrizzleBaseRepository(),
  };

  // Limpiar inscripción previa del user si existe
  const existing = await deps.inscripcionRepository.findByUserId(user.id);
  if (existing) {
    console.log(
      "\n⚠️ El user YA tiene una inscripción — borrando para el test...",
    );
    const { inscripciones } = await import("../src/infra/drizzle/schema");
    db.delete(inscripciones).where(eq(inscripciones.userId, user.id)).run();
    console.log("   borrada.");
  }

  try {
    const result = await createInscripcion(deps, {
      userId: user.id,
      promocionId: promo.id,
      basesId: base.id,
      paqueteMonto: 1350,
      teamName: "Los Invictos 2002",
      acceptedBases: true,
      fitnessDeclaration: true,
      imageConsent: true,
      deportistas: [
        {
          tipoDocumento: "DNI",
          numeroDocumento: "80111222",
          nombres: "Pedro",
          apellidos: "Ramirez",
          genero: "V",
          rolDisciplina: "Capitán",
          acreditacion: "Verificación en padrón",
          disciplinaIds: [disc.id],
          shirtSize: "L",
        },
        {
          tipoDocumento: "DNI",
          numeroDocumento: "80111223",
          nombres: "Luis",
          apellidos: "Torres",
          genero: "V",
          rolDisciplina: "Jugador",
          acreditacion: "Verificación en padrón",
          disciplinaIds: [disc.id],
          shirtSize: "M",
        },
      ],
    });

    console.log("\n✅ INSCRIPCIÓN CREADA:", result.inscripcion.id);
    console.log("   status:", result.inscripcion.status);
    console.log("   teamName:", result.inscripcion.teamName);
    console.log("   equipos:", result.equipos.length);
    console.log("   deportistas:", result.deportistas.length);
    console.log(
      "   primer deportista:",
      result.deportistas[0].persona.nombres,
      result.deportistas[0].persona.apellidos,
      "| talla:",
      result.deportistas[0].shirtSize,
    );

    // Cleanup
    const { inscripciones, deportistas, equipos, DeportistaEquipos, personas } =
      await import("../src/infra/drizzle/schema");
    db.delete(DeportistaEquipos).run();
    db.delete(deportistas)
      .where(eq(deportistas.inscripcionId, result.inscripcion.id))
      .run();
    db.delete(equipos)
      .where(eq(equipos.inscripcionId, result.inscripcion.id))
      .run();
    db.delete(inscripciones)
      .where(eq(inscripciones.id, result.inscripcion.id))
      .run();
    db.delete(personas).where(eq(personas.numeroDocumento, "80111222")).run();
    db.delete(personas).where(eq(personas.numeroDocumento, "80111223")).run();
    console.log("\n✓ Cleanup hecho. FLUJO COMPLETO FUNCIONA.");
  } catch (e: any) {
    console.error("\n❌ ERROR:", e.constructor?.name, "-", e.message);
    if (e.fieldErrors)
      console.error("   fieldErrors:", JSON.stringify(e.fieldErrors, null, 2));
  }

  process.exit(0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
