// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RecuperarCompraForm } from "../components/RecuperarCompraForm";

/**
 * The states of the recovery form.
 *
 * The form is the only form of the public area, and it carries three of the
 * ten states: the validation, the request in progress and the neutral
 * answer. The suite also freezes the rule that matters most here: while the
 * mail provider is not configured the form NEVER fakes a sent message.
 */

describe("REC-01 - el formulario de recuperación", () => {
  it("un envío inválido resume los errores y los asocia a su campo", async () => {
    render(<RecuperarCompraForm />);

    fireEvent.click(screen.getByRole("button", { name: "Solicitar el enlace" }));

    const resumen = await screen.findByRole("alert");
    expect(resumen.textContent).toContain("Revisa");

    // El error está ASOCIADO al campo, no sólo resumido.
    expect(document.getElementById("correo-error")).not.toBeNull();
    expect(
      screen.getByLabelText("Correo de la compra").getAttribute("aria-invalid"),
    ).toBe("true");
  });

  it("un correo con formato inválido no pasa la validación", async () => {
    render(<RecuperarCompraForm />);

    fireEvent.change(screen.getByLabelText("Correo de la compra"), {
      target: { value: "no-es-un-correo" },
    });
    fireEvent.change(screen.getByLabelText("Número de orden"), {
      target: { value: "1234" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Solicitar el enlace" }));

    await waitFor(() => {
      expect(
        screen.getByText("Ese correo no tiene un formato válido."),
      ).toBeDefined();
    });
  });

  it("sin servicio de correo NO finge un envío", async () => {
    render(<RecuperarCompraForm />);

    fireEvent.change(screen.getByLabelText("Correo de la compra"), {
      target: { value: "ana@ejemplo.com" },
    });
    fireEvent.change(screen.getByLabelText("Número de orden"), {
      target: { value: "1234" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Solicitar el enlace" }));

    await waitFor(() => {
      expect(
        screen.getByText("El envío de correos está desactivado por ahora"),
      ).toBeDefined();
    });

    // La respuesta neutra NO se muestra: no se envió nada.
    expect(screen.queryByText("Solicitud registrada")).toBeNull();
  });

  it("con servicio, la respuesta es neutra y no revela la compra", async () => {
    const enviar = vi.fn(async () => ({ tipo: "neutro" as const }));

    render(<RecuperarCompraForm enviar={enviar} />);

    fireEvent.change(screen.getByLabelText("Correo de la compra"), {
      target: { value: "ana@ejemplo.com" },
    });
    fireEvent.change(screen.getByLabelText("Número de orden"), {
      target: { value: "1234" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Solicitar el enlace" }));

    await waitFor(() => {
      expect(screen.getByText("Solicitud registrada")).toBeDefined();
    });

    expect(enviar).toHaveBeenCalledTimes(1);
    // La respuesta no dice que haya una compra.
    expect(screen.queryByText(/encontramos tu compra/i)).toBeNull();
  });

  it("el campo de correo expone el nombre accesible y el tipo correcto", () => {
    render(<RecuperarCompraForm />);

    const correo = screen.getByLabelText("Correo de la compra");
    expect(correo.getAttribute("type")).toBe("email");
    expect(correo.getAttribute("autocomplete")).toBe("email");
  });
});
