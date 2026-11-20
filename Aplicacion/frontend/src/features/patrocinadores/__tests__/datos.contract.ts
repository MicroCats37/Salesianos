import { patrocinadorSchema } from "../schemas/patrocinador.schema";

/**
 * The data of the sponsors suite, built THROUGH the Zod mirror.
 *
 * ## WHY THE DATA LIVES HERE AND NOT IN A PRODUCTION FIXTURE
 *
 * The provisional fixture of `UI-05` was a file of PRODUCTION code that
 * carried a copy of the wire of the backend. `API-05` removes it, because the
 * wire of the backend is now written down ONCE, in the mirror
 * (`schemas/patrocinador.schema.ts`), and the suite reads that same mirror.
 *
 * The consequence is the point of the file: a shape that the mirror rejects
 * breaks the suite **BEFORE** a single pixel is drawn.
 *
 * These are EXAMPLES of the wire, not a transport: no module of production
 * imports this file and it is not exported from any barrel.
 */

/** A sponsor of the edition, with its logo and its ordered gallery. */
export const PATROCINADOR = patrocinadorSchema.parse({
  id: "5c9d0e1f-2a3b-4c5d-8e7f-8091a2b3c4d5",
  created_at: "2026-11-10T08:00:00+00:00",
  updated_at: "2026-11-10T08:00:00+00:00",
  edicion_id: "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  edicion_nombre: "Salesianos FEST 2026",
  nombre: "Colegio Norte",
  slug: "colegio-norte",
  descripcion: "Acompaña el torneo de fútbol 7 del festival.",
  sitio_web: "https://colegio-norte.example",
  visible: true,
  logo: {
    url: "/media/patrocinadores/4b8c9d0e/1f2a3b4c.png",
    disponible: true,
  },
  imagenes: [
    {
      id: "2f6a7b8c-9d0e-4f2a-8b4c-5d6e7f8091a2",
      orden: 0,
      url: "/media/patrocinadores/2f6a7b8c/9d0e1f2a.webp",
      texto_alternativo:
        "Fotografía del stand del patrocinador en el patio del colegio",
      disponible: true,
      created_at: "2026-11-10T09:00:00+00:00",
    },
    {
      id: "3a7b8c9d-0e1f-4a3b-9c5d-6e7f8091a2b3",
      orden: 1,
      url: "/media/patrocinadores/3a7b8c9d/0e1f2a3b.webp",
      texto_alternativo:
        "Fotografía del equipo del patrocinador con la camiseta del festival",
      disponible: false,
      created_at: "2026-11-10T09:05:00+00:00",
    },
  ],
});

/** A sponsor without a logo and without a gallery. */
export const PATROCINADOR_SIN_PIEZAS = patrocinadorSchema.parse({
  id: "6d0e1f2a-3b4c-5d6e-8f80-91a2b3c4d5e6",
  created_at: "2026-11-11T10:00:00+00:00",
  updated_at: "2026-11-11T10:00:00+00:00",
  edicion_id: "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  edicion_nombre: "Salesianos FEST 2026",
  nombre: "Comercio del barrio",
  slug: "comercio-del-barrio",
  descripcion: "",
  sitio_web: "",
  visible: false,
  logo: null,
  imagenes: [],
});
