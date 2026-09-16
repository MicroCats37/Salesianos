const D = require("better-sqlite3");
const fs = require("fs");

const dbPath = "./dev.db";
const journalPath = "./dev.db-journal";
if (fs.existsSync(dbPath)) {
  fs.unlinkSync(dbPath);
  console.log("dev.db eliminada");
}
if (fs.existsSync(journalPath)) {
  fs.unlinkSync(journalPath);
}

const sqlFiles = fs.readdirSync("./drizzle").filter((f) => f.endsWith(".sql"));
console.log("Migraciones a aplicar:", sqlFiles);

const db = new D(dbPath);
for (const file of sqlFiles) {
  const sql = fs.readFileSync(`./drizzle/${file}`, "utf8");
  const statements = sql
    .split("--> statement-breakpoint")
    .map((s) => s.trim())
    .filter(Boolean);
  for (const stmt of statements) {
    try {
      db.exec(stmt);
    } catch (e) {
      console.error("Error en:", stmt.slice(0, 80));
      throw e;
    }
  }
}

const tables = db
  .prepare(
    "SELECT name FROM sqlite_master WHERE type='table' AND name != '__drizzle_migrations'",
  )
  .all()
  .map((t) => t.name);
console.log("Tablas:", tables.join(", "));

const insCols = db
  .prepare("PRAGMA table_info(inscripciones)")
  .all()
  .map((c) => c.name);
console.log("\nColumnas inscripciones:", insCols.join(", "));
const depCols = db
  .prepare("PRAGMA table_info(deportistas)")
  .all()
  .map((c) => c.name);
console.log("Columnas deportistas:", depCols.join(", "));

db.close();
console.log("\nOK — DB recreada con columnas del mockup.");
