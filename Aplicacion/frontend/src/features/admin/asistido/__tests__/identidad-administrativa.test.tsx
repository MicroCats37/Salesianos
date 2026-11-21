// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { FormProvider, useForm } from "react-hook-form";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { BloqueIdentidadAdministrativa } from "../components/BloqueIdentidadAdministrativa";

/**
 * The ADMINISTRATIVE identity block.
 *
 * The block owns the UX of resolving an EXACT document: it searches the
 * padrón, it shows the canonical names of the person that already exists and
 * it reveals the name, the surname and the gender of the one that does not.
 *
 * The suite freezes the three states and the ERROR state: the block never
 * asks for the data of a person that is already registered, and it never
 * hides the data of the one that has to be.
 */

const { mutar } = vi.hoisted(() => ({ mutar: vi.fn() }));

vi.mock("@/features/auth/hooks", () => ({
  useResolverPersona: () => ({
    mutateAsync: mutar,
    isPending: false,
  }),
}));

/** The answer of the resolver when the padrón already has the person. */
const ENCONTRADA = {
  origen: "LOCAL",
  persona_id: "8f5f2a2e-0f2f-4a0e-9f4a-6b2a9d0a1c11",
  persistida: true,
  tipo_documento: "DNI",
  numero_documento: "33333333",
  nombres: "María",
  apellidos: "Quispe",
};

/** The answer of the resolver when the padrón does NOT have the person. */
const NO_ENCONTRADA = {
  origen: "EXTERNO",
  persona_id: null,
  persistida: false,
  tipo_documento: "DNI",
  numero_documento: "55555555",
  nombres: "Elena",
  apellidos: "Vega",
};

function Formulario({
  children,
  tipoDocumento = "DNI",
}: {
  children: ReactNode;
  tipoDocumento?: "DNI" | "CE" | "PAS";
}) {
  const methods = useForm({
    defaultValues: {
      tipo_documento: tipoDocumento,
      numero_documento: "",
      nombres: "",
      apellidos: "",
      genero: "",
      estado_identidad: "SIN_CONSULTAR",
    },
  });

  return <FormProvider {...methods}>{children}</FormProvider>;
}

function renderBloque(tipoDocumento: "DNI" | "CE" | "PAS" = "DNI") {
  return render(
    <Formulario tipoDocumento={tipoDocumento}>
      <BloqueIdentidadAdministrativa idPrefijo="participante" />
    </Formulario>,
  );
}

async function buscar(documento: string) {
  fireEvent.change(screen.getByLabelText(/Número de documento/), {
    target: { value: documento },
  });

  fireEvent.click(
    screen.getByRole("button", { name: "Buscar la identidad del documento" }),
  );
}

beforeEach(() => {
  mutar.mockReset();
});

describe("ACP — el bloque de identidad administrativa", () => {
  it("SIN consultar, el bloque NO pide los nombres: primero hay que resolver", () => {
    renderBloque();

    expect(screen.getByLabelText(/Tipo de documento/)).toBeDefined();
    expect(screen.getByLabelText(/Número de documento/)).toBeDefined();
    expect(screen.queryByLabelText(/Nombres/)).toBeNull();
    expect(screen.queryByLabelText(/Apellidos/)).toBeNull();
    expect(screen.queryByLabelText(/Género/)).toBeNull();
  });

  it("CE y pasaporte muestran los datos civiles sin exigir una búsqueda DNI", async () => {
    renderBloque("CE");

    await waitFor(() => {
      expect(screen.getByLabelText(/Nombres/)).toBeDefined();
    });

    expect(screen.getByLabelText(/Apellidos/)).toBeDefined();
    expect(screen.getByLabelText(/Género/)).toBeDefined();
    expect(
      screen.queryByRole("button", {
        name: "Buscar la identidad del documento",
      }),
    ).toBeNull();
  });

  it("normaliza el número según el tipo de documento", async () => {
    const vistaCe = renderBloque("CE");
    const numeroCe = screen.getByLabelText(
      /Número de documento/,
    ) as HTMLInputElement;

    fireEvent.change(numeroCe, { target: { value: "12A34567890" } });
    expect(numeroCe.value).toBe("123456789");

    vistaCe.unmount();
    renderBloque("PAS");
    const pasaporte = screen.getByLabelText(
      /Número de documento/,
    ) as HTMLInputElement;

    fireEvent.change(pasaporte, { target: { value: "ab-12" } });
    expect(pasaporte.value).toBe("AB12");
  });

  it("una identidad ENCONTRADA muestra los nombres canónicos y NO pide los datos", async () => {
    mutar.mockResolvedValue(ENCONTRADA);
    renderBloque();

    await buscar("33333333");

    await waitFor(() => {
      expect(screen.getByText("María Quispe")).toBeDefined();
    });

    // El padrón manda: no se piden los datos de una persona ya registrada.
    expect(screen.queryByLabelText(/Nombres/)).toBeNull();
    expect(screen.queryByLabelText(/Apellidos/)).toBeNull();
    expect(screen.queryByLabelText(/Género/)).toBeNull();
  });

  it("una identidad NO ENCONTRADA revela los nombres, los apellidos y el género", async () => {
    mutar.mockResolvedValue(NO_ENCONTRADA);
    renderBloque();

    await buscar("55555555");

    await waitFor(() => {
      expect(screen.getByLabelText(/Nombres/)).toBeDefined();
    });

    expect(screen.getByLabelText(/Apellidos/)).toBeDefined();
    expect(screen.getByLabelText(/Género/)).toBeDefined();

    // La fuente externa conoce sus nombres: el bloque los precarga.
    expect((screen.getByLabelText(/Nombres/) as HTMLInputElement).value).toBe(
      "Elena",
    );
  });

  it("el género NO se precarga: lo declara el administrador", async () => {
    mutar.mockResolvedValue(NO_ENCONTRADA);
    renderBloque();

    await buscar("55555555");

    await waitFor(() => {
      expect(screen.getByLabelText(/Género/)).toBeDefined();
    });
  });

  it("un fallo de la resolución se ANUNCIA y no deja la identidad resuelta", async () => {
    mutar.mockRejectedValue(new Error("El servicio de identidad no responde."));
    renderBloque();

    await buscar("55555555");

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeDefined();
    });

    expect(
      screen.getByText("El servicio de identidad no responde."),
    ).toBeDefined();
    // El fallo NO revela los campos de una persona que no se ha resuelto.
    expect(screen.queryByLabelText(/Nombres/)).toBeNull();
  });

  it("cada control del bloque se dibuja UNA vez: no hay etiquetas repetidas", () => {
    renderBloque();

    expect(screen.getAllByLabelText(/Tipo de documento/)).toHaveLength(1);
    expect(screen.getAllByLabelText(/Número de documento/)).toHaveLength(1);
  });

  it("cambiar el documento INVALIDA la resolución anterior", async () => {
    mutar.mockResolvedValue(ENCONTRADA);
    renderBloque();

    await buscar("33333333");

    await waitFor(() => {
      expect(screen.getByText("María Quispe")).toBeDefined();
    });

    // El administrador se equivoca de documento: la identidad anterior ya
    // no vale y sus nombres tampoco.
    fireEvent.change(screen.getByLabelText(/Número de documento/), {
      target: { value: "55555555" },
    });

    await waitFor(() => {
      expect(screen.queryByText("María Quispe")).toBeNull();
    });

    // Hay que resolver la identidad otra vez antes de continuar.
    expect(screen.queryByLabelText(/Nombres/)).toBeNull();
  });
});
