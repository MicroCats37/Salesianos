// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import type { AnchorHTMLAttributes, ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { AuditoriaValidacionesView } from "../views/AuditoriaValidacionesView";
import { ValidarEntregaView } from "../views/ValidarEntregaView";
import { ValidarPaseView } from "../views/ValidarPaseView";
import {
  ENTREGA_PENDIENTE,
  REGISTRO_ENTRADA,
  REGISTRO_ENTREGA,
  RESULTADO_CONFIRMACION,
  VISTA_PREVIA_PERMITIDA,
} from "./datos.contract";

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
  usePathname: () => "/administracion/validaciones",
}));

/**
 * The states of the validation area.
 *
 * **The suites of this packet have NEVER RUN.** They are written and the
 * execution is deferred to the verification phase. Nothing here may be read
 * as a green result.
 */
describe("validaciones - entrada, recogida y auditoría", () => {
  it("ADM-16 dice que el servicio no existe en vez de simular una lectura", () => {
    render(<ValidarPaseView />);

    expect(
      screen.getByText(/El servicio de validación todavía no está conectado/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Comprobar no consume/i)[0]).toBeInTheDocument();
  });

  it("ADM-16 ofrece el camino de teclado con una etiqueta real", () => {
    render(<ValidarPaseView />);

    const campo = screen.getByLabelText(/código de la entrada/i);
    expect(campo).toBeInTheDocument();
    expect(campo).toHaveAttribute("id", "codigo-credencial");
  });

  it("ADM-16 no ofrece la confirmación sin una vista previa", () => {
    render(<ValidarPaseView />);

    expect(
      screen.getByText(/Todavía no hay una vista previa/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /confirmar el ingreso/i }),
    ).not.toBeInTheDocument();
  });

  it("ADM-16 ofrece la confirmación solo cuando la vista previa la admite", () => {
    render(
      <ValidarPaseView estado="listo" vistaPrevia={VISTA_PREVIA_PERMITIDA} />,
    );

    expect(
      screen.getByRole("button", { name: /confirmar el ingreso/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Esta vista previa no consume nada/),
    ).toBeInTheDocument();
  });

  it("ADM-16 no ofrece la confirmación cuando el servidor la rechaza", () => {
    render(
      <ValidarPaseView
        estado="listo"
        vistaPrevia={{
          ...VISTA_PREVIA_PERMITIDA,
          puede_validar: false,
        }}
      />,
    );

    expect(
      screen.queryByRole("button", { name: /confirmar el ingreso/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/No se puede validar/)).toBeInTheDocument();
  });

  it("una credencial ya usada muestra el consumo anterior", () => {
    render(
      <ValidarPaseView
        estado="listo"
        vistaPrevia={{
          ...VISTA_PREVIA_PERMITIDA,
          puede_validar: false,
          consumo_previo: {
            instante: "2026-11-21T18:42:00+00:00",
            punto: "Puerta principal",
            operador: "Operador de turno",
          },
        }}
      />,
    );

    expect(
      screen.getByText(/Esta credencial ya se había consumido/),
    ).toBeInTheDocument();
  });

  it("la confirmación registrada dice qué pasó y no promete nada más", () => {
    render(
      <ValidarPaseView
        estado="listo"
        vistaPrevia={VISTA_PREVIA_PERMITIDA}
        resultado={RESULTADO_CONFIRMACION}
      />,
    );

    expect(
      screen.getByText(/La validación quedó registrada/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Unidades consumidas: 1/)).toBeInTheDocument();
  });

  it("una repetición se declara repetición y no un segundo consumo", () => {
    render(
      <ValidarPaseView
        estado="listo"
        vistaPrevia={VISTA_PREVIA_PERMITIDA}
        resultado={{ ...RESULTADO_CONFIRMACION, repetida: true }}
      />,
    );

    expect(
      screen.getByText(/no se consumió una segunda vez/i),
    ).toBeInTheDocument();
  });

  it("ADM-20 es una operación distinta de ADM-16 y lo dice", () => {
    render(
      <ValidarEntregaView
        estado="listo"
        pendientes={[ENTREGA_PENDIENTE]}
        vistaPrevia={VISTA_PREVIA_PERMITIDA}
      />,
    );

    expect(
      screen.getByText(/Pagado y entregado son dos hechos/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /confirmar la entrega/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Camiseta del festival")).toBeInTheDocument();
  });

  it("ADM-22 audita el ingreso y la recogida sin mezclarlos", () => {
    render(
      <AuditoriaValidacionesView
        estado="listo"
        registros={[REGISTRO_ENTRADA, REGISTRO_ENTREGA]}
      />,
    );

    expect(screen.getAllByText("Ingreso").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Recogida").length).toBeGreaterThan(0);
  });

  it("ADM-22 expone el resultado, el punto y el responsable como texto", () => {
    render(
      <AuditoriaValidacionesView
        estado="listo"
        registros={[REGISTRO_ENTRADA]}
      />,
    );

    expect(screen.getAllByText("Validación permitida")[0]).toBeInTheDocument();
    expect(screen.getByText("Puerta principal")).toBeInTheDocument();
    expect(screen.getByText("Operador de turno")).toBeInTheDocument();
  });

  it("ADM-22 con un filtro que no deja resultados ofrece quitarlo", () => {
    render(
      <AuditoriaValidacionesView
        estado="listo"
        registros={[]}
        filtroVeredicto="TICKET_YA_CONSUMIDO"
      />,
    );

    expect(
      screen.getByText(/No hay validaciones con ese resultado/),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: /quitar el filtro/i })[0],
    ).toBeInTheDocument();
  });

  it("la auditoría no dibuja asientos cuando el servicio no existe", () => {
    render(<AuditoriaValidacionesView />);

    expect(
      screen.getByText(/Todavía no hay asientos en la bitácora/),
    ).toBeInTheDocument();
  });

  it("la comprobación no consume: el botón de comprobar no confirma", () => {
    render(<ValidarPaseView estado="listo" />);

    const comprobar = screen.getByRole("button", { name: /comprobar/i });
    expect(comprobar).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /confirmar el ingreso/i }),
    ).not.toBeInTheDocument();
  });

  it("la consola bloquea el campo mientras la comprobación está en vuelo", () => {
    render(<ValidarPaseView estado="listo" ocupado />);

    expect(screen.getByRole("button", { name: /comprobando/i })).toBeDisabled();
    expect(screen.getByLabelText(/código de la entrada/i)).toBeDisabled();
  });

  it("ninguna presentación usa un color literal ni un tono de paleta", () => {
    const { container } = render(
      <AuditoriaValidacionesView
        estado="listo"
        registros={[REGISTRO_ENTRADA]}
      />,
    );

    const html = container.innerHTML;
    expect(html).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(html).not.toMatch(
      /\b(bg|text|border)-(red|blue|green|yellow|slate|gray|zinc|neutral|stone)-\d{2,3}\b/,
    );
  });

  it("el botón de comprobar dispara la comprobación con el código escrito", () => {
    const comprobar = vi.fn();
    render(<ValidarPaseView estado="listo" onComprobar={comprobar} />);

    fireEvent.change(screen.getByLabelText(/código de la entrada/i), {
      target: { value: "  ABC-123  " },
    });
    fireEvent.click(screen.getByRole("button", { name: /comprobar/i }));

    expect(comprobar).toHaveBeenCalledWith("ABC-123");
  });
});
