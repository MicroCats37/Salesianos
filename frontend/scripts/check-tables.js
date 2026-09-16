const D = require("better-sqlite3");
const db = new D("./dev.db");
const tables = db
  .prepare("SELECT name FROM sqlite_master WHERE type='table'")
  .all();
console.log("Tablas en DB:", tables.map((t) => t.name).join(", "));
db.close();
