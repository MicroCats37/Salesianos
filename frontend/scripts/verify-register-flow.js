const Database = require("better-sqlite3");
const db = new Database("./dev.db");

// Check tables exist
const tables = [
  "personas",
  "users",
  "sesiones",
  "inscripciones",
  "equipos",
  "deportistas",
  "deportista_equipos",
];
console.log("=== VERIFYING DATABASE ===");
for (const t of tables) {
  try {
    const count = db.prepare(`SELECT count(*) as c FROM ${t}`).get();
    console.log(`  ${t.padEnd(20)} OK (${count.c} rows)`);
  } catch (e) {
    console.log(`  ${t.padEnd(20)} MISSING: ${e.message}`);
  }
}

// Verify the admin user exists
const admin = db
  .prepare("SELECT * FROM users WHERE email = 'admin@salesianosfest.com'")
  .get();
if (admin) {
  console.log(
    `\n  Admin user: ${admin.email} (persona_id: ${admin.persona_id})`,
  );
  try {
    const persona = db
      .prepare("SELECT * FROM personas WHERE id = ?")
      .get(admin.persona_id);
    if (persona) {
      console.log(`  Persona: ${persona.nombres} ${persona.apellidos}`);
    } else {
      console.log(
        `  ⚠️ Persona record not found for persona_id: ${admin.persona_id}`,
      );
    }
  } catch {
    console.log(`  ⚠️ personas table missing — cannot verify persona`);
  }
} else {
  console.log("\n  ⚠️ Admin user not found — need to run seed");
}
db.close();
