const D = require("better-sqlite3");
const db = new D("./dev.db");

// Borrar inscripciones de prueba y sus dependencias
db.prepare("DELETE FROM deportista_equipos").run();
db.prepare("DELETE FROM deportistas").run();
db.prepare("DELETE FROM equipos").run();
db.prepare("DELETE FROM inscripciones").run();
db.prepare("DELETE FROM sesiones").run();

// Borrar personas y users de prueba (conservar admin 00000000)
const adminPersona = db
  .prepare("SELECT id FROM personas WHERE numero_documento = '00000000'")
  .get();
db.prepare("DELETE FROM users WHERE persona_id != ?").run(adminPersona.id);
db.prepare("DELETE FROM personas WHERE numero_documento != '00000000'").run();

console.log("users:", db.prepare("SELECT email, rol FROM users").all());
console.log(
  "personas:",
  db.prepare("SELECT numero_documento, nombres FROM personas").all(),
);
console.log(
  "inscripciones:",
  db.prepare("SELECT count(*) as c FROM inscripciones").get(),
);
db.close();
console.log("\nDB limpia de datos de prueba.");
