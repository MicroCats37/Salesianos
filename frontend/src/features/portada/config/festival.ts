/**
 * Configuración del festival — fuente única de datos y enlaces.
 *
 * Replica `config.js` del micrositio oficial, tipado para TypeScript.
 * Las fechas llevan el offset explícito de Lima (-05:00): Lima no aplica
 * horario de verano, así que no hace falta ninguna librería de zonas.
 */

export const FESTIVAL = {
  nombre: "Salesianos FEST 2026",
  edicion: "EDICIÓN 2026",
  ciudad: "LIMA, PERÚ",
  claim: "EL REENCUENTRO QUE NOS MUEVE",
  frase: "UN FESTIVAL. TODA LA FAMILIA.",
  descripcion:
    "Vuelve a encontrarte con tu promoción. Salesianos FEST 2026: deporte, familia y fiesta el 21 de noviembre en la Asociación Okinawense del Perú, Ate, Lima.",
  fechaEvento: "21 DE NOVIEMBRE DE 2026",
  inicio: "2026-11-21T08:00:00-05:00",
  fin: "2026-11-22T03:00:00-05:00",
} as const;

/** Ventanas de venta de inscripciones (Lima). */
export const VENTAS = {
  preventaHasta: "2026-10-25T20:00:00-05:00",
  regularDesde: "2026-10-26T00:00:00-05:00",
  regularHasta: "2026-11-08T20:00:00-05:00",
  extemporaneaDesde: "2026-11-09T00:00:00-05:00",
  inscripcionCierra: "2026-11-18T20:00:00-05:00",
} as const;

export const SEDE = {
  nombre: "ASOCIACIÓN OKINAWENSE DEL PERÚ",
  direccion: "Av. Asturias s/n · Ate, Lima",
  bienvenida: "Bienvenida desde las 8:00 a. m.",
  mapaEmbedUrl:
    "https://maps.google.com/maps?q=Asociaci%C3%B3n%20Okinawense%20del%20Per%C3%BA%20Av%20Asturias%20Mz%206%20Lt%201%20Mayorazgo%20Ate%20Lima&t=&z=15&ie=UTF8&iwloc=&output=embed",
  mapaUrl:
    "https://www.google.com/maps/search/?api=1&query=Asociaci%C3%B3n%20Okinawense%20del%20Per%C3%BA%20Av%20Asturias%20Mz%206%20Lt%201%20Mayorazgo%20Ate%20Lima",
} as const;

export const ENLACES = {
  contacto: "https://wa.me/51967951650",
  telefono: "967 951 650",
  facebook:
    "https://www.facebook.com/people/Salesianos-2002-Bodas-de-Plata/61593863260385/?sk=photos",
  instagram: "https://www.instagram.com/salesianos2002bodasdeplata",
  tiktok: "https://www.tiktok.com/@salesianos.2002",
  registro: "/inscripcion",
  calendario: "/salesianos-fest-2026.ics",
} as const;

/** La transmisión en vivo se anuncia cuando la organización publica el enlace. */
export const EN_VIVO = {
  url: "",
  embedUrl: "",
  estado: "proximamente",
} as const;

/** Los auspiciadores se confirman por la organización; hoy la lista es vacía. */
export const AUSPICIADORES: { nombre: string; imagen: string; url: string }[] =
  [];

/** Anclas de las secciones de la portada. */
export const SECCIONES = {
  inicio: "inicio",
  experiencia: "experiencia",
  promociones: "promociones",
  campeonato: "campeonato",
  programa: "programa",
  familia: "familia",
  fiesta: "fiesta",
  paquetes: "paquetes",
  enVivo: "en-vivo",
  lugar: "lugar",
  auspiciadores: "auspiciadores",
  preguntas: "preguntas",
} as const;

/** Enlaces del header de la portada. */
export const NAV_LINKS = [
  { href: `#${SECCIONES.experiencia}`, label: "El festival" },
  { href: `#${SECCIONES.promociones}`, label: "Promociones" },
  { href: `#${SECCIONES.campeonato}`, label: "Campeonato" },
  { href: `#${SECCIONES.familia}`, label: "En familia" },
  { href: `#${SECCIONES.fiesta}`, label: "La fiesta" },
  { href: `#${SECCIONES.paquetes}`, label: "Paquetes" },
  { href: `#${SECCIONES.auspiciadores}`, label: "Auspiciadores" },
] as const;
