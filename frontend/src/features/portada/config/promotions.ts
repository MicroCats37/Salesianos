/**
 * Promociones confirmadas para Salesianos FEST 2026.
 *
 * Cada una tiene su anuncio oficial (Facebook) y el afiche correspondiente.
 * Los datos vienen del micrositio oficial (`community.js`).
 */

export interface Promocion {
  anio: number;
  imagen: string;
  fuente: string;
}

export const PROMOCIONES: Promocion[] = [
  {
    anio: 1986,
    imagen: "/images/portada/promo-1986.webp",
    fuente:
      "https://www.facebook.com/photo.php?fbid=122122882659462108&set=pb.61593863260385.-2207520000&type=3",
  },
  {
    anio: 1997,
    imagen: "/images/portada/promo-1997.webp",
    fuente:
      "https://www.facebook.com/photo.php?fbid=122122605141462108&set=pb.61593863260385.-2207520000&type=3",
  },
  {
    anio: 1998,
    imagen: "/images/portada/promo-1998.webp",
    fuente:
      "https://www.facebook.com/photo.php?fbid=122122441167462108&set=pb.61593863260385.-2207520000&type=3",
  },
  {
    anio: 2003,
    imagen: "/images/portada/promo-2003.webp",
    fuente:
      "https://www.facebook.com/photo.php?fbid=122122881879462108&set=pb.61593863260385.-2207520000&type=3",
  },
  {
    anio: 2004,
    imagen: "/images/portada/promo-2004.webp",
    fuente:
      "https://www.facebook.com/photo.php?fbid=122122232691462108&set=pb.61593863260385.-2207520000&type=3",
  },
  {
    anio: 2009,
    imagen: "/images/portada/promo-2009.webp",
    fuente:
      "https://www.facebook.com/photo.php?fbid=122122403331462108&set=pb.61593863260385.-2207520000&type=3",
  },
  {
    anio: 2013,
    imagen: "/images/portada/promo-2013.webp",
    fuente:
      "https://www.facebook.com/photo.php?fbid=122122438803462108&set=pb.61593863260385.-2207520000&type=3",
  },
];
