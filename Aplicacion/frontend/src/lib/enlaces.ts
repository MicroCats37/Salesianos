/**
 * The external links of the event.
 *
 * They are static public addresses, not endpoints: nothing here is consumed
 * by a service and nothing here answers with an envelope. Their values come
 * from the frozen tree, which is the only evidence of the school's public
 * presence.
 */
export const ENLACES = {
  facebook:
    "https://www.facebook.com/people/Salesianos-2002-Bodas-de-Plata/61593863260385/?sk=photos",
  instagram: "https://www.instagram.com/salesianos2002bodasdeplata",
  tiktok: "https://www.tiktok.com/@salesianos.2002",
  whatsapp: "https://wa.me/51967951650",
  telefono: "967 951 650",
  calendario: "/salesianos-fest-2026.ics",
} as const;
