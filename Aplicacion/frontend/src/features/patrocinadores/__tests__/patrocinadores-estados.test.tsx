// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import type { AnchorHTMLAttributes, ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { PATROCINADOR, PATROCINADOR_SIN_PIEZAS } from "./datos.contract";
import { PatrocinadoresAdminView } from "../views/PatrocinadoresAdminView";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} {...props}>
      {children as ReactNode}
    </a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/administracion/patrocinadores",
}));

/**
 * The states of the sponsors area.
 *
 * **The suites of this packet have NEVER RUN.** They are written and the
 * execution is deferred to the verification phase. Nothing here may be read
 * as a green result.
 */
describe("patrocinadores - ficha, piezas y galería", () => {
  it("la ruta dice que el servicio no existe en vez de inventar aliados", () => {
    render(<PatrocinadoresAdminView />);

    expect(
      screen.getByText(/Todavía no hay patrocinadores que mostrar/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/todavía no está disponible en el backend/i),
    ).toBeInTheDocument();
  });

  it("la ficha del patrocinador no tiene ninguna cifra", () => {
    render(<PatrocinadoresAdminView estado="listo" />);

    expect(
      screen.getByText(/Un patrocinador no tiene cifras/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/aportaci/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/comisi/i)).not.toBeInTheDocument();
  });

  it("la galería anuncia la posición de la pieza", () => {
    render(
      <PatrocinadoresAdminView
        estado="listo"
        patrocinadores={[PATROCINADOR]}
        seleccionado={PATROCINADOR}
      />,
    );

    expect(screen.getByText("Pieza 1 de 2")).toBeInTheDocument();
  });

  it("la galería se recorre con el teclado y con nombres en español", () => {
    render(
      <PatrocinadoresAdminView
        estado="listo"
        patrocinadores={[PATROCINADOR]}
        seleccionado={PATROCINADOR}
      />,
    );

    const anterior = screen.getByRole("button", { name: "Pieza anterior" });
    const siguiente = screen.getByRole("button", { name: "Pieza siguiente" });
    expect(anterior).toBeDisabled();
    expect(siguiente).toBeEnabled();

    fireEvent.click(siguiente);
    expect(screen.getByText("Pieza 2 de 2")).toBeInTheDocument();
  });

  it("una pieza sin archivo legible muestra el hueco y no una imagen rota", () => {
    render(
      <PatrocinadoresAdminView
        estado="listo"
        patrocinadores={[PATROCINADOR]}
        seleccionado={PATROCINADOR}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Pieza siguiente" }));

    expect(screen.getByText(/no está disponible en el servidor/i)).toBeInTheDocument();
    expect(screen.queryByRole("img", { name: /logo de/i })).toBeInTheDocument();
  });

  it("el logo se describe con el nombre del patrocinador", () => {
    render(
      <PatrocinadoresAdminView
        estado="listo"
        patrocinadores={[PATROCINADOR]}
        seleccionado={PATROCINADOR}
      />,
    );

    expect(
      screen.getAllByRole("img", { name: "Logo de Colegio Norte" }).length,
    ).toBeGreaterThan(0);
  });

  it("un patrocinador sin piezas dice que no tiene piezas", () => {
    render(
      <PatrocinadoresAdminView
        estado="listo"
        patrocinadores={[PATROCINADOR_SIN_PIEZAS]}
        seleccionado={PATROCINADOR_SIN_PIEZAS}
      />,
    );

    expect(
      screen.getByText(/Este patrocinador todavía no tiene piezas/),
    ).toBeInTheDocument();
  });

  it("el formulario anuncia los tipos y el tamaño que acepta el servidor", () => {
    render(<PatrocinadoresAdminView estado="listo" />);

    const logo = screen.getByLabelText(/logo de identidad/i);
    expect(logo).toHaveAttribute("accept", "image/jpeg, image/png, image/webp");
    expect(screen.getByText(/hasta 5 MiB/)).toBeInTheDocument();
  });

  it("el formulario de visibilidad tiene una etiqueta real", () => {
    render(<PatrocinadoresAdminView estado="listo" />);

    expect(
      screen.getByLabelText(/visible en la página pública/i),
    ).toBeInTheDocument();
  });

  it("el error de media explica la causa y el arreglo", () => {
    render(
      <PatrocinadoresAdminView
        estado="listo"
        errorMedio="MEDIA_TAMANO_EXCEDIDO"
      />,
    );

    expect(
      screen.getByText(/supera el tamaño máximo de 5 MiB/i),
    ).toBeInTheDocument();
  });

  it("sin servicio conectado el guardado no sale del dispositivo", () => {
    render(<PatrocinadoresAdminView estado="listo" />);

    expect(
      screen.getByRole("button", { name: /guardar el patrocinador/i }),
    ).toBeDisabled();
    expect(
      screen.getByText(/el guardado no sale de este dispositivo/i),
    ).toBeInTheDocument();
  });

  it("ninguna presentación usa un color literal ni un tono de paleta", () => {
    const { container } = render(
      <PatrocinadoresAdminView
        estado="listo"
        patrocinadores={[PATROCINADOR]}
        seleccionado={PATROCINADOR}
      />,
    );

    const html = container.innerHTML;
    expect(html).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(html).not.toMatch(/\b(bg|text|border)-(red|blue|green|yellow|slate|gray|zinc|neutral|stone)-\d{2,3}\b/);
  });
});
