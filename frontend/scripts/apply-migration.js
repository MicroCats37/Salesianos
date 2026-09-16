const D = require("better-sqlite3");
const fs = require("fs");
const db = new D("./dev.db");
const sql = fs.readFileSync("./drizzle/0000_tricky_nebula.sql", "utf8");
db.exec(sql);
const tables = db
  .prepare(
    "SELECT name FROM sqlite_master WHERE type='table' AND name != '__drizzle_migrations'",
  )
  .all()
  .map((t) => t.name);
console.log("Tablas creadas:", tables.join(", "));
db.close();
