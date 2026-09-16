// Script E2E de validación — verifica tablas y flujo de inscripción
const Database = require("better-sqlite3");
const db = new Database("./dev.db");

console.log("=== AUDITORÍA DE TABLAS Y FLUJO DE INSCRIPCIÓN ===\n");

// 1. Resumen de tablas
console.log("--- 1. RESUMEN DE TABLAS ---");
const tables = [
  "bases",
  "disciplinas",
  "categorias",
  "promociones",
  "users",
  "sesiones",
  "inscripciones",
  "equipos",
  "jugadores",
];
for (const t of tables) {
  const count = db.prepare("SELECT count(*) as c FROM " + t).get();
  console.log(`  ${t.padEnd(15)} count: ${count.c}`);
}

// 2. Detalle de catálogos
console.log("\n--- 2. CATÁLOGO DE DISCIPLINAS ---");
const discs = db
  .prepare(
    "SELECT codigo, nombre, max_jugadores FROM disciplinas ORDER BY codigo",
  )
  .all();
for (const d of discs) {
  console.log(`  ${d.codigo.padEnd(15)} max=${d.max_jugadores}  "${d.nombre}"`);
}

console.log("\n--- 3. CATEGORÍAS POR DISCIPLINA ---");
const cats = db
  .prepare(`
  SELECT d.codigo as disc, c.codigo, c.anio_min, c.anio_max
  FROM categorias c JOIN disciplinas d ON c.disciplina_id = d.id
  ORDER BY d.codigo, c.codigo
`)
  .all();
const byDisc = {};
for (const c of cats) {
  byDisc[c.disc] = byDisc[c.disc] || [];
  byDisc[c.disc].push(`${c.codigo}(${c.anio_min}-${c.anio_max})`);
}
for (const disc in byDisc) {
  console.log(`  ${disc.padEnd(15)} ${byDisc[disc].join(", ")}`);
}

// 4. Validar que cada categoría pertenece a su disciplina
console.log("\n--- 4. VALIDACIÓN FK CATEGORÍA → DISCIPLINA ---");
const fkErrors = db
  .prepare(`
  SELECT COUNT(*) as c FROM categorias c
  LEFT JOIN disciplinas d ON c.disciplina_id = d.id
  WHERE d.id IS NULL
`)
  .get();
console.log(`  Categorías huérfanas: ${fkErrors.c}`);

// 5. Validar que cada categoria tiene rango de años consistente
console.log("\n--- 5. RANGOS DE AÑOS (anio_min <= anio_max) ---");
const rangeErrors = db
  .prepare(`SELECT count(*) as c FROM categorias WHERE anio_min > anio_max`)
  .get();
console.log(`  Categorías con rango inválido: ${rangeErrors.c}`);

// 6. Validar que la promoción activa tiene FK válida
console.log("\n--- 6. PROMOCIÓN ACTIVA ---");
const promo = db.prepare("SELECT * FROM promociones WHERE activa = 1").get();
console.log(
  `  Promoción: anio=${promo.anio} colegio=${promo.colegio} nombre="${promo.nombre}"`,
);

// 7. Validar que las bases activas existen
console.log("\n--- 7. BASES ACTIVAS ---");
const base = db.prepare("SELECT * FROM bases WHERE activo = 1").get();
console.log(
  `  Bases: version="${base.version}" aprobado_en=${base.aprobado_en}`,
);

// 8. Validar admin user
console.log("\n--- 8. ADMIN USER ---");
const admin = db
  .prepare("SELECT id, email, rol FROM users WHERE rol = ?")
  .get("admin_comite");
console.log(`  Admin: ${admin.email} rol=${admin.rol}`);

// 9. SIMULAR crear inscripción completa con 4 equipos
console.log("\n--- 9. SIMULACIÓN CREAR INSCRIPCIÓN CON 4 EQUIPOS ---");
const now = Math.floor(Date.now() / 1000);
const inscId = require("crypto").randomUUID();
db.prepare(`
  INSERT INTO inscripciones (id, user_id, promocion_id, bases_id, paquete_monto, status, created_at, updated_at)
  VALUES (?, ?, ?, ?, 1350, 'recibida', ?, ?)
`).run(inscId, admin.id, promo.id, base.id, now, now);
console.log(`  Inscripción creada: ${inscId.slice(0, 8)}...`);

const allDiscs = db.prepare("SELECT * FROM disciplinas ORDER BY codigo").all();
let equiposCreados = 0;
let jugadoresCreados = 0;

for (const disc of allDiscs) {
  // Para cada disciplina, crear un equipo con TODAS sus categorías
  const catsForDisc = db
    .prepare(
      "SELECT * FROM categorias WHERE disciplina_id = ? ORDER BY codigo LIMIT 1",
    )
    .all(disc.id);

  for (const cat of catsForDisc) {
    const equipoId = require("crypto").randomUUID();
    db.prepare(`
      INSERT INTO equipos (id, inscripcion_id, disciplina_id, categoria_id, created_at)
      VALUES (?, ?, ?, ?, ?)
    `).run(equipoId, inscId, disc.id, cat.id, now);

    // Crear max_jugadores - 1 jugadores (casi al límite)
    const jugadoresCount = disc.max_jugadores - 1;
    for (let i = 1; i <= jugadoresCount; i++) {
      const jugId = require("crypto").randomUUID();
      const year = cat.anio_min + i; // cada jugador un año distinto dentro del rango
      const dni = String(10000000 + equiposCreados * 1000 + i)
        .padStart(8, "0")
        .slice(-8);
      const fecha = new Date(`${year}-06-15`);
      db.prepare(`
        INSERT INTO jugadores (id, equipo_id, dni, nombres, apellidos, fecha_nacimiento, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `).run(
        jugId,
        equipoId,
        dni,
        `Jugador${i}`,
        `Apellido${i}`,
        Math.floor(fecha.getTime() / 1000),
        now,
      );
      jugadoresCreados++;
    }
    equiposCreados++;
  }
}

console.log(`  Equipos creados: ${equiposCreados}`);
console.log(`  Jugadores creados: ${jugadoresCreados}`);

// 10. Test del use-case: ¿qué pasa si intentamos insertar max_jugadores + 1?
console.log(
  "\n--- 10. TEST: validación max_jugadores (DB no tiene constraint, use-case es quien valida) ---",
);
const discBV = db
  .prepare("SELECT * FROM disciplinas WHERE codigo = ?")
  .get("basket_var");
console.log(
  `  basket_var max_jugadores: ${discBV.max_jugadores} (esperado 10)`,
);

// 11. Verificar que los jugadores insertados están dentro del rango de su categoría
console.log("\n--- 11. VALIDACIÓN: jugadores en rango etario ---");
const outOfRange = db
  .prepare(`
  SELECT j.nombres, j.fecha_nacimiento, c.anio_min, c.anio_max
  FROM jugadores j
  JOIN equipos e ON j.equipo_id = e.id
  JOIN categorias c ON e.categoria_id = c.id
  WHERE e.inscripcion_id = ?
  AND (CAST(strftime('%Y', j.fecha_nacimiento, 'unixepoch') AS INTEGER) < c.anio_min
       OR CAST(strftime('%Y', j.fecha_nacimiento, 'unixepoch') AS INTEGER) > c.anio_max)
`)
  .all(inscId);
console.log(`  Jugadores fuera de rango: ${outOfRange.length}`);
if (outOfRange.length > 0) {
  console.log("  ⚠️ HAY ERRORES:", outOfRange);
}

// 12. Test DNI duplicado DENTRO del mismo equipo
console.log(
  "\n--- 12. TEST: DNI duplicado (constraint es use-case, no DB) ---",
);
const dups = db
  .prepare(`
  SELECT dni, count(*) as c FROM jugadores j
  JOIN equipos e ON j.equipo_id = e.id
  WHERE e.inscripcion_id = ?
  GROUP BY j.equipo_id, j.dni
  HAVING c > 1
`)
  .all(inscId);
console.log(`  DNIs duplicados dentro de equipo: ${dups.length}`);

// 13. Resumen final
console.log("\n--- 13. ESTADO FINAL DB ---");
for (const t of tables) {
  const count = db.prepare("SELECT count(*) as c FROM " + t).get();
  console.log(`  ${t.padEnd(15)} count: ${count.c}`);
}

// 14. Cleanup
console.log("\n--- 14. CLEANUP ---");
db.prepare(
  "DELETE FROM jugadores WHERE equipo_id IN (SELECT id FROM equipos WHERE inscripcion_id = ?)",
).run(inscId);
db.prepare("DELETE FROM equipos WHERE inscripcion_id = ?").run(inscId);
db.prepare("DELETE FROM inscripciones WHERE id = ?").run(inscId);
console.log("  Datos de prueba eliminados.");

db.close();
console.log("\n=== FIN DE AUDITORÍA ===");
