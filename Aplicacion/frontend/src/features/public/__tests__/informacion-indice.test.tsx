// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InformacionView } from "../views/InformacionView";

/**
 * The anchor navigation of the information page.
 *
 * The rule of the brief is simple and absolute: EVERY anchor of the index
 * lands on a section that exists. An anchor that points nowhere is a broken
 * promise, and it is the defect this suite freezes.
 */
describe("PUB-02 - el índice de anclas", () => {
  it("el índice es una navegación con nombre accesible", () => {
    render(<InformacionView />);

    expect(
      screen.getByRole("navigation", { name: "Contenido de esta página" }),
    ).toBeDefined();
  });

  it("cada ancla del índice resuelve a una sección que existe", () => {
    const { container } = render(<InformacionView />);

    const enlaces = Array.from(
      container.querySelectorAll('nav a[href^="#"]'),
    );

    expect(enlaces.length).toBeGreaterThan(0);

    for (const enlace of enlaces) {
      const destino = enlace.getAttribute("href") ?? "";
      expect(destino.startsWith("#")).toBe(true);
      expect(container.querySelector(destino)).not.toBeNull();
    }
  });

  it("la página ofrece el camino a la inscripción", () => {
    render(<InformacionView />);

    expect(
      screen.getByRole("link", { name: "Crear una inscripción" }),
    ).toBeDefined();
  });
});
