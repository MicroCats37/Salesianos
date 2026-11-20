/**
 * The single source of truth for the route map.
 *
 * The plan proposes the routes (`frontend/01` §2 and §3); they are "provisional"
 * there, so every route lives in ONE constant: renaming a route is a change
 * in this file, never a search-and-replace across the markup.
 *
 * Route groups do not alter the URL, so the path of `(cuenta)/mi-cuenta` is
 * `/mi-cuenta`.
 */

export const RUTAS = {
  publico: {
    inicio: "/",
    informacion: "/informacion",
    pases: "/pases",
    paseGestionar: (token: string) => `/pases/gestionar/${token}`,
    tienda: "/tienda",
    tiendaProducto: (slug: string) => `/tienda/${slug}`,
    tiendaPedido: (token: string) => `/tienda/pedidos/${token}`,
    recuperarCompra: "/recuperar-compra",
    videos: "/videos",
    videoDetalle: (id: string) => `/videos/${id}`,
  },
  auth: {
    login: "/login",
    registro: "/registro",
  },
  cuenta: {
    miCuenta: "/mi-cuenta",
    misInscripciones: "/mis-inscripciones",
    misInscripcionesDetalle: (id: string) => `/mis-inscripciones/${id}`,
    misCompras: "/mis-compras",
    misComprasDetalle: (id: string) => `/mis-compras/${id}`,
    inscripcion: "/inscripcion",
  },
  administracion: {
    resumen: "/administracion",
    personas: "/administracion/personas",
    usuarios: "/administracion/usuarios",
    inscripciones: "/administracion/inscripciones",
    inscripcionesDetalle: (id: string) => `/administracion/inscripciones/${id}`,
    equipos: "/administracion/equipos",
    equiposDetalle: (id: string) => `/administracion/equipos/${id}`,
    participantes: "/administracion/participantes",
    competencias: "/administracion/competencias",
    competenciaDetalle: (id: string) => `/administracion/competencias/${id}`,
    competenciaCuadro: (id: string) =>
      `/administracion/competencias/${id}/cuadro`,
    competenciaAgenda: "/administracion/competencias/agenda",
    pagos: "/administracion/pagos",
    pases: "/administracion/pases",
    pasesValidar: "/administracion/pases/validar",
    marketplace: "/administracion/marketplace",
    marketplaceProducto: (id: string) =>
      `/administracion/marketplace/productos/${id}`,
    marketplaceInventario: "/administracion/marketplace/inventario",
    marketplaceEntregas: "/administracion/marketplace/entregas",
    patrocinadores: "/administracion/patrocinadores",
    validaciones: "/administracion/validaciones",
    videos: "/administracion/videos",
  },
} as const;

/**
 * The public destinations offered by the site header.
 *
 * They are filtered by the edition scope the backend publishes: the shell
 * never invents an enabled module.
 */
export interface DestinoPublico {
  href: string;
  label: string;
}

export const DESTINOS_PUBLICOS: DestinoPublico[] = [
  { href: RUTAS.publico.informacion, label: "Información" },
  { href: RUTAS.publico.pases, label: "Pases" },
  { href: RUTAS.publico.tienda, label: "Tienda" },
  { href: RUTAS.publico.videos, label: "En vivo" },
];

/**
 * The public destination a visitor can reach without a session.
 */
export const RUTAS_PUBLICAS: string[] = [
  RUTAS.publico.inicio,
  RUTAS.publico.informacion,
  RUTAS.publico.pases,
  RUTAS.publico.tienda,
  RUTAS.publico.recuperarCompra,
  RUTAS.publico.videos,
  RUTAS.auth.login,
  RUTAS.auth.registro,
];

/**
 * Whether a path is reachable without a session.
 *
 * The guest link routes carry a token in the path and are public by nature:
 * the token is the credential and its expiry is the server's business.
 */
export function esRutaPublica(pathname: string): boolean {
  if (RUTAS_PUBLICAS.includes(pathname)) return true;
  return (
    pathname.startsWith(`${RUTAS.publico.pases}/gestionar/`) ||
    pathname.startsWith(`${RUTAS.publico.tienda}/`) ||
    pathname.startsWith(`${RUTAS.publico.videos}/`)
  );
}
