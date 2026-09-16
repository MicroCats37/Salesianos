// Verifica el flujo completo de creación de inscripción usando los repos reales
const { drizzle } = require("drizzle-orm/better-sqlite3");
const Database = require("better-sqlite3");
const path = require("path");

// Cargar schema via tsx no es trivial en node plano, así que usamos el SQL directo
// Mejor: verificar la lógica del use-case con un test manual de los repos

const db = new Database("./dev.db");

// IDs reales de la DB
const userId = "0308b59a-423d-4e34-95f7-11775c489f04";
const promoId = "624dd402-a208-434d-abf7-ec87908490a9";
const baseId = "4d04e9f7-0d8b-4d20-8609-120450993192";
const discFulbito = "c3e26344-4ae4-40a3-9bd7-6254703f3089";

// Simular lo que haría el Server Action:
// 1. Validar que baseId existe y es activa
const base = db
  .prepare("SELECT * FROM bases WHERE id = ? AND activo = 1")
  .get(baseId);
console.log("1) Base activa:", base ? base.version : "NO ENCONTRADA");

// 2. Validar promocion existe
const promo = db.prepare("SELECT * FROM promociones WHERE id = ?").get(promoId);
console.log("2) Promocion:", promo ? `anio=${promo.anio}` : "NO ENCONTRADA");

// 3. Validar disciplina
const disc = db
  .prepare("SELECT * FROM disciplinas WHERE id = ?")
  .get(discFulbito);
console.log(
  "3) Disciplina:",
  disc ? `${disc.codigo} (max ${disc.max_jugadores})` : "NO ENCONTRADA",
);

// 4. Validar que la categoría se calcula para promo 2002 en fulbito_var
const cats = db
  .prepare("SELECT * FROM categorias WHERE disciplina_id = ?")
  .all(discFulbito);
const catMatch = cats.find(
  (c) => promo.anio >= c.anio_min && promo.anio <= c.anio_max,
);
console.log(
  "4) Categoría para promo 2002 en fulbito_var:",
  catMatch ? catMatch.nombre : "SIN CATEGORIA",
);
console.log(
  "   Categorías disponibles:",
  cats.map((c) => `${c.nombre}(${c.anio_min}-${c.anio_max})`).join(", "),
);

// 5. Validar max_jugadores
const jugadoresCount = 1;
console.log(
  "5) Jugadores (1) <= max (12):",
  jugadoresCount <= disc.max_jugadores ? "OK" : "EXCEDE",
);

// 6. Simular la transacción de inserción
console.log("\n--- Simulando INSERT (transacción) ---");
try {
  const now = Math.floor(Date.now() / 1000);
  const inscId = require("crypto").randomUUID();

  db.prepare(`
    INSERT INTO inscripciones (id, user_id, promocion_id, bases_id, paquete_monto, team_name, status, accepted_bases, declaracion_jurada, fitness_declaration, image_consent, created_at, updated_at)
    VALUES (?, ?, ?, ?, 1350, 'Los Invictos', 'recibida', 1, 1, 1, 1, ?, ?)
  `).run(inscId, userId, promoId, baseId, now, now);
  console.log("✓ Inscripción insertada:", inscId.slice(0, 8));

  const equipoId = require("crypto").randomUUID();
  db.prepare(`
    INSERT INTO equipos (id, inscripcion_id, disciplina_id, categoria_id, created_at)
    VALUES (?, ?, ?, ?, ?)
  `).run(equipoId, inscId, discFulbito, catMatch.id, now);
  console.log("✓ Equipo insertado");

  const personaId = require("crypto").randomUUID();
  db.prepare(`
    INSERT INTO personas (id, tipo_documento, numero_documento, nombres, apellidos, created_at, updated_at)
    VALUES (?, 'DNI', '70123461', 'Ana', 'Lopez', ?, ?)
  `).run(personaId, now, now);
  console.log("✓ Persona insertada");

  const deportistaId = require("crypto").randomUUID();
  db.prepare(`
    INSERT INTO deportistas (id, inscripcion_id, persona_id, rol_disciplina, acreditacion, shirt_size, created_at)
    VALUES (?, ?, ?, 'Delegado', 'Verificación en padrón', 'M', ?)
  `).run(deportistaId, inscId, personaId, now);
  console.log("✓ Deportista insertado");

  db.prepare(`
    INSERT INTO deportista_equipos (deportista_id, equipo_id, created_at)
    VALUES (?, ?, ?)
  `).run(deportistaId, equipoId, now);
  console.log("✓ Deportista→Equipo vinculado");

  // Verificar
  const count = db
    .prepare("SELECT count(*) as c FROM inscripciones WHERE id = ?")
    .get(inscId);
  console.log("\n✓ Inscripción existe en DB: count =", count.c);

  // Cleanup
  db.prepare("DELETE FROM deportista_equipos WHERE deportista_id = ?").run(
    deportistaId,
  );
  db.prepare("DELETE FROM deportistas WHERE id = ?").run(deportistaId);
  db.prepare("DELETE FROM personas WHERE id = ?").run(personaId);
  db.prepare("DELETE FROM equipos WHERE id = ?").run(equipoId);
  db.prepare("DELETE FROM inscripciones WHERE id = ?").run(inscId);
  console.log("✓ Cleanup hecho. El flujo de inserción funciona.");
} catch (e) {
  console.error("✗ ERROR EN LA SIMULACIÓN:", e.message);
}

db.close();
console.log("\n=== FIN DEL TEST ===");
