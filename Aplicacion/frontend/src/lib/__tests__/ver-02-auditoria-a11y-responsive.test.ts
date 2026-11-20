/**
 * VER-02 — Auditoría de accesibilidad y responsive de TODAS las rutas vivas.
 *
 * Packet: `VER-02` · Change: `salesianos-fest-rebuild` · Owner: A9
 * Authority: `evidence/routes/SH-02-responsive-and-accessibility-matrix.md`
 * §2.1 (A11Y-01…A11Y-16) y §1.2 (antipatrones).
 *
 * ## Qué prueba y qué NO prueba
 *
 * Esta puerta congela la REGLA que el marcado debe obedecer. NO sustituye a
 * la pasada de navegador: `jsdom` no tiene motor de layout, así que aquí no
 * se mide ningún píxel, ni el ancho real de una columna, ni el desbordamiento
 * horizontal, ni el orden de tabulación real. La ausencia de motor de
 * navegador en este entorno (y la prohibición de instalar dependencias) es un
 * BLOQUEO declarado en la evidencia de VER-02.
 *
 * Lo que sí es verificable, y es lo que esta puerta mide:
 *
 * - A11Y-02 · quitar el contorno NUNCA deja el foco invisible.
 * - A11Y-04 · la cabecera de columna declara `scope`.
 * - A11Y-07 · el objetivo táctil declara 44 px (`min-h-11` y compañía).
 * - A11Y-10 · la navegación expone la ubicación actual (`aria-current`).
 * - A11Y-12 · el movimiento no esencial respeta `prefers-reduced-motion`.
 * - A11Y-13 · la imagen declara su texto alternativo.
 * - §1.2 · el zoom NO está desactivado y NO hay ancho fijo de píxeles.
 * - §1    · cada ruta viva se declara en el mapa y declara puntos de ruptura.
 */

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

import { RUTAS } from "../routes";

// ── El árbol ────────────────────────────────────────────────────────────────

const RAIZ = join(process.cwd(), "src");

/** El árbol legado, fuera del objetivo: no se audita. */
const EXCLUIDAS = ["components-app"];

function recorrer(dir: string): string[] {
  const salida: string[] = [];

  for (const entrada of readdirSync(dir)) {
    const completo = join(dir, entrada);
    if (statSync(completo).isDirectory()) {
      salida.push(...recorrer(completo));
      continue;
    }
    if (/\.(tsx?|css)$/.test(entrada)) salida.push(completo);
  }

  return salida;
}

function relativo(archivo: string): string {
  return relative(RAIZ, archivo).replace(/\\/g, "/");
}

function esAuditable(archivo: string): boolean {
  const nombre = relativo(archivo);
  if (nombre.includes("__tests__/")) return false;
  if (nombre.endsWith(".test.ts") || nombre.endsWith(".test.tsx")) return false;
  return !EXCLUIDAS.some((excluida) => nombre.startsWith(excluida));
}

const TODOS = recorrer(RAIZ).filter(esAuditable);
const FUENTES = new Map(
  TODOS.map((f) => [relativo(f), readFileSync(f, "utf8")]),
);

/** El área de producto: las vistas y los componentes que el producto usa. */
const PRODUCTO = [...FUENTES.entries()].filter(
  ([nombre]) => nombre.startsWith("features/") || nombre.startsWith("app/"),
);

/** Las primitivas de shadcn que el proyecto copia y parchea. */
const PRIMITIVAS = [...FUENTES.entries()].filter(([nombre]) =>
  nombre.startsWith("components/ui/"),
);

// ── El lector de etiquetas ──────────────────────────────────────────────────
//
// Un `<Button ... />` de shadcn puede ocupar varias líneas y llevar un
// `onClick={() => ...}` con llaves. Una expresión regular que termine en el
// primer `>` corta la etiqueta por la mitad y produce falsos positivos: este
// lector respeta las llaves y las comillas.

function etiqueta(fuente: string, desde: number): string {
  let i = desde;
  let nivel = 0;
  let cita: string | null = null;

  while (i < fuente.length) {
    const ch = fuente[i];

    if (cita) {
      if (ch === "\\") {
        i += 2;
        continue;
      }
      if (ch === cita) cita = null;
    } else if (ch === '"' || ch === "'" || ch === "`") {
      cita = ch;
    } else if (ch === "{") {
      nivel += 1;
    } else if (ch === "}") {
      nivel -= 1;
    } else if (ch === ">" && nivel === 0) {
      return fuente.slice(desde, i + 1);
    }

    i += 1;
  }

  return fuente.slice(desde);
}

function abreEtiquetas(fuente: string, nombre: string): string[] {
  const salida: string[] = [];
  const patron = new RegExp(`<${nombre}\\b`, "g");

  for (;;) {
    const coincidencia = patron.exec(fuente);
    if (coincidencia === null) break;
    salida.push(etiqueta(fuente, coincidencia.index));
  }

  return salida;
}

// ── Las rutas vivas ─────────────────────────────────────────────────────────

/** La ruta que sirve un `page.tsx`, deducida de su carpeta. */
function rutaDePagina(nombre: string): string {
  const carpeta = nombre.replace(/^app\//, "").replace(/\/page\.tsx$/, "");

  const segmentos = carpeta
    .split("/")
    .filter((s) => s !== "" && !/^\(.*\)$/.test(s))
    .map((s) =>
      s.startsWith("[") && s.endsWith("]") ? `:${s.slice(1, -1)}` : s,
    );

  return `/${segmentos.join("/")}`;
}

const PAGINAS = [...FUENTES.entries()]
  .filter(
    ([nombre]) => nombre.startsWith("app/") && nombre.endsWith("/page.tsx"),
  )
  .map(([nombre, fuente]) => ({ nombre, ruta: rutaDePagina(nombre), fuente }));

/** Todas las rutas que el mapa declara, con los parámetros de las fábricas. */
function rutasDeclaradas(): Set<string> {
  const declaradas = new Set<string>();

  const visitar = (valor: unknown) => {
    if (typeof valor === "string") {
      declaradas.add(valor);
      return;
    }
    if (typeof valor === "function") {
      // Las fábricas de ruta llevan un parámetro: se llaman con un centinela.
      try {
        const ruta = (valor as (v: string) => string)("__PARAM__");
        declaradas.add(ruta.replace("__PARAM__", ":parametro"));
      } catch {
        // Una fábrica que no acepta un string no es una ruta.
      }
      return;
    }
    if (valor && typeof valor === "object") {
      Object.values(valor).forEach(visitar);
    }
  };

  visitar(RUTAS);

  return declaradas;
}

/**
 * La plantilla de una ruta: los parámetros se normalizan a `:parametro` para
 * que el nombre del parámetro (`:token`, `:slug`, `:id`) NO sea una diferencia
 * de estilo sino la misma ruta.
 */
function plantilla(ruta: string): string {
  return ruta.replace(/:[^/]+/g, ":parametro");
}

// ── Los contratos medibles ─────────────────────────────────────────────────

/** A11Y-07 · 44 px son 11 unidades de Tailwind (`--spacing` 0.25 rem). */
const ALTO_MINIMO = /min-h-11\b|\bh-(11|12|13|14|16)\b|\bsize-11\b/;

/**
 * Controles que NO son un objetivo táctil autónomo y por eso no declaran
 * 44 px. Cada excepción lleva su motivo: son excepciones, no permisos.
 */
const EXCEPCIONES_DE_OBJETIVO: Record<string, string> = {
  "features/competencias/components/TarjetaEncuentro.tsx":
    "la ficha entera es el objetivo: su caja la fija el contenido",
  "features/portada/components/LiveSection.tsx":
    "el disparador mide 64 px (`size-16`)",
  "features/portada/components/PromotionsSection.tsx":
    "el bloque completo es el objetivo (`w-full`)",
  "features/portada/components/Reglamento.tsx":
    "la cabecera del acordeón mide 20 px de alto + 40 px de relleno",
  "features/auth/components/AuthVisualPanel.tsx":
    "INDICADOR de carrusel: 10 px. Hallazgo ABIERTO de VER-02 (V-02-A11Y-07-02): " +
    "corregirlo exige una decisión de diseño que ningún packet de verificación puede tomar",
  "features/portada/components/Hero.tsx":
    "INDICADOR de carrusel: 6 px. Hallazgo ABIERTO de VER-02 (V-02-A11Y-07-03): " +
    "corregirlo exige una decisión de diseño que ningún packet de verificación puede tomar",
  "features/auth/components/RegisterForm.tsx":
    "el conmutador de visibilidad de la contraseña mide 24 px: cumple el mínimo " +
    "de WCAG 2.5.8 (24×24) y no llega al objetivo de 44 px del proyecto. " +
    "Hallazgo de VER-02 (V-02-A11Y-07-04), no corregido aquí",
  "features/auth/views/LoginClientShell.tsx":
    "el conmutador de visibilidad de la contraseña y las pestañas de acceso: " +
    "24 px y 36 px. Mínimo de WCAG 2.5.8 cumplido, objetivo de 44 px del " +
    "proyecto no. Hallazgo de VER-02 (V-02-A11Y-07-05), no corregido aquí",
};

/** A11Y-02 · un control que quita el contorno DEBE declarar un foco visible. */
const FOCO_VISIBLE =
  /focus-visible:ring|focus:ring|focus-visible:border-|focus:border-|focus-visible:bg-|focus:bg-|focus-visible:outline-(?!none)|focus:outline-(?!none)/;

/** Los controles que reciben foco: sólo ellos pueden perder la visibilidad. */
const CONTROLES_CON_FOCO = [
  "button",
  "input",
  "select",
  "textarea",
  "Button",
  "Link",
  "TabsTrigger",
  "PaginationLink",
  "PaginationPrevious",
  "PaginationNext",
];

/** A11Y-07 · el objetivo táctil de 44 px. */
function objetivosSin44px(): string[] {
  const fallos: string[] = [];

  for (const [nombre, fuente] of PRODUCTO) {
    if (!nombre.startsWith("features/")) continue;

    for (const etiqueta_ of ["Button", "button"]) {
      for (const tag of abreEtiquetas(fuente, etiqueta_)) {
        if (ALTO_MINIMO.test(tag)) continue;
        if (EXCEPCIONES_DE_OBJETIVO[nombre]) continue;
        fallos.push(`${nombre} :: ${tag.replace(/\s+/g, " ").slice(0, 180)}`);
      }
    }
  }

  return fallos;
}

/** SH-02 §2.2 · la cabecera de columna declara su ámbito. */
function cabecerasSinScope(): string[] {
  const fallos: string[] = [];

  for (const [nombre, fuente] of PRODUCTO) {
    if (!nombre.startsWith("features/")) continue;

    for (const tag of abreEtiquetas(fuente, "TableHead")) {
      if (!/\bscope=/.test(tag))
        fallos.push(`${nombre} :: ${tag.replace(/\s+/g, " ")}`);
    }
  }

  return fallos;
}

/** A11Y-02 · el foco invisible. */
function focoInvisible(ambito: [string, string][]): string[] {
  const fallos: string[] = [];

  for (const [nombre, fuente] of ambito) {
    for (const control of CONTROLES_CON_FOCO) {
      for (const tag of abreEtiquetas(fuente, control)) {
        if (!/outline-none/.test(tag)) continue;
        if (FOCO_VISIBLE.test(tag)) continue;
        fallos.push(`${nombre} :: ${tag.replace(/\s+/g, " ").slice(0, 180)}`);
      }
    }
  }

  return fallos;
}

// ── La auditoría ────────────────────────────────────────────────────────────

describe("VER-02 — inventario de rutas", () => {
  it("la aplicación sirve las rutas que el rebuild declaró", () => {
    expect(PAGINAS.length).toBeGreaterThanOrEqual(35);
    expect(PAGINAS.some((p) => p.ruta === "/")).toBe(true);
    expect(PAGINAS.some((p) => p.ruta === "/administracion/pagos")).toBe(true);
    expect(PAGINAS.some((p) => p.ruta === "/pases/gestionar/:token")).toBe(
      true,
    );
  });

  it("ninguna ruta viva escapa del mapa de rutas", () => {
    const declaradas = new Set([...rutasDeclaradas()].map(plantilla));
    const huerfanas = PAGINAS.filter(
      (p) => !declaradas.has(plantilla(p.ruta)),
    ).map((p) => p.ruta);

    expect(huerfanas).toEqual([]);
  });

  it("cada ruta declara puntos de ruptura: se adapta a los cinco anchos", () => {
    // La ruta no es "responsive" porque funciona en uno de ellos (SH-02 §1).
    // La familia de la ruta se deduce de lo que la página IMPORTA: el grupo
    // de rutas `(auth)` no aparece en la URL, así que la URL no lo cuenta.
    const sinRupturas: string[] = [];

    for (const pagina of PAGINAS) {
      const areas = new Set<string>();

      for (const coincidencia of pagina.fuente.matchAll(
        /from\s+"@\/features\/([^"]+)"/g,
      )) {
        areas.add(coincidencia[1].split("/")[0]);
      }

      const familia = [...FUENTES.entries()].filter(([nombre]) =>
        [...areas].some((area) => nombre.startsWith(`features/${area}/`)),
      );

      const fuente = [pagina.fuente, ...familia.map(([, texto]) => texto)].join(
        "\n",
      );

      if (!/\b(sm|md|lg|xl):/.test(fuente)) sinRupturas.push(pagina.ruta);
    }

    expect(sinRupturas).toEqual([]);
  });
});

describe("VER-02 — A11Y-04 · la cabecera de columna declara su ámbito", () => {
  it("ninguna cabecera de tabla del área de producto carece de `scope`", () => {
    expect(cabecerasSinScope()).toEqual([]);
  });
});

describe("VER-02 — A11Y-07 · el objetivo táctil mide 44 px", () => {
  it("ningún control autónomo del área de producto queda por debajo de 44 px", () => {
    expect(objetivosSin44px()).toEqual([]);
  });
});

describe("VER-02 — A11Y-13 · la imagen declara su texto alternativo", () => {
  it("ninguna imagen del árbol queda sin `alt`", () => {
    const fallos: string[] = [];

    for (const [nombre, fuente] of FUENTES) {
      for (const tag of abreEtiquetas(fuente, "img")) {
        if (!/\balt=/.test(tag))
          fallos.push(`${nombre} :: ${tag.replace(/\s+/g, " ")}`);
      }
    }

    expect(fallos).toEqual([]);
  });
});

describe("VER-02 — A11Y-02 · el foco nunca queda invisible", () => {
  it("ningún control del área de producto pierde su indicador de foco", () => {
    expect(focoInvisible(PRODUCTO)).toEqual([]);
  });

  it("la deuda declarada en las primitivas de shadcn NO crece", () => {
    // Las primitivas `components/ui/**` son fuente copiada de shadcn: su
    // dueño es A7 + A0, no este packet. La lista congelada convierte un
    // hallazgo invisible en una deuda CONTADA: si crece, esta puerta falla.
    const declarada = ["components/ui/searchable-select.tsx"];

    const hallados = focoInvisible(PRIMITIVAS).map(
      (linea) => linea.split(" :: ")[0],
    );
    const unicos = [...new Set(hallados)].sort();

    expect(unicos).toEqual(declarada);
  });
});

describe("VER-02 — A11Y-10 · la navegación expone la ubicación actual", () => {
  it("la navegación del producto declara `aria-current`", () => {
    const navegaciones = [
      "components/shell/SiteHeader.tsx",
      "components/shell/AppSidebar.tsx",
      "features/admin/components/AdminSubnav.tsx",
    ];

    for (const nombre of navegaciones) {
      expect(FUENTES.get(nombre) ?? "").toContain("aria-current");
    }
  });
});

describe("VER-02 — A11Y-12 · el movimiento respeta la preferencia del sistema", () => {
  it("la hoja global apaga el movimiento no esencial", () => {
    const globals = FUENTES.get("app/globals.css") ?? "";

    expect(globals).toContain("prefers-reduced-motion");
  });
});

describe("VER-02 — SH-02 §1.2 · antipatrones de responsive", () => {
  it("el zoom NO está desactivado", () => {
    for (const [nombre, fuente] of PRODUCTO) {
      if (!nombre.startsWith("app/")) continue;

      expect(fuente).not.toMatch(/userScalable:\s*false/);
      expect(fuente).not.toMatch(/maximumScale:\s*1\b/);
    }
  });

  it("ningún contenedor del área de producto fija un ancho de píxeles", () => {
    const anchosFijos: string[] = [];

    for (const [nombre, fuente] of PRODUCTO) {
      if (!nombre.startsWith("features/")) continue;

      // `max-w-[Npx]` y `w-[calc(100%-…)]` NO son anchos fijos: se adaptan.
      for (const coincidencia of fuente.matchAll(
        /(?<!max-)(?<!min-)\bw-\[(\d+)px\]/g,
      )) {
        anchosFijos.push(`${nombre} :: w-[${coincidencia[1]}px]`);
      }
    }

    expect(anchosFijos).toEqual([]);
  });
});
