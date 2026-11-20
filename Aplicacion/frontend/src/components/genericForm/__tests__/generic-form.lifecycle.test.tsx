// genericForm/__tests__/generic-form.lifecycle.test.tsx
//
// The lifecycle of the GenericForm: re-hydration, the exact wire shape of the
// submit, the coercion of Zod, the file hand-off and the field errors of the
// backend.
//
// The suites of this packet are WRITTEN but NOT EXECUTED: the runtime
// verification of FND-07 is deferred (the only command allowed in this packet
// is `npx tsc --noEmit`).

// @vitest-environment jsdom

import { zodResolver } from "@hookform/resolvers/zod";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRef } from "react";
import { type Resolver, useForm } from "react-hook-form";
import { describe, expect, it, vi } from "vitest";
import { z } from "zod";

import { GenericForm } from "@/components/genericForm/GenericForm";
import { imageField } from "@/lib/forms/imageField";

/**
 * The schema of the harness.
 *
 * `titulo` is OPTIONAL on purpose: the cases of this suite submit a form that
 * does NOT carry the title (they exercise the coercion, the hand-off of the
 * file and the 422 of the server), and Zod — which owns the validation
 * (`contract/smart.md` §1.A and §5.1) — blocks a submit of a form that does
 * not comply. A required title would stop those submits BEFORE the behaviour
 * under test ever runs.
 */
const schema = z.object({
  titulo: z.string().optional(),
  cantidad: z.coerce.number().optional(),
  descripcion: z.string().nullable().optional(),
  imagen: imageField().schema,
});

type FormValues = z.infer<typeof schema>;

const file = new File(["contenido"], "logo.png", { type: "image/png" });

function serverError(field: string, message: string) {
  return {
    response: {
      status: 422,
      data: {
        success: false,
        data: null,
        error: {
          code: "INVALID_REQUEST",
          message: "La solicitud no es válida.",
          details: null,
          field_errors: [{ field, code: "REQUIRED", message }],
        },
        message: null,
      },
    },
    request: {},
    isAxiosError: true,
  };
}

describe("GenericForm — the create mapping", () => {
  it("sends the validated values and omits the ones that were never filled", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <GenericForm<FormValues> schema={schema} onSubmit={onSubmit}>
        {({ methods }) => (
          <>
            <input aria-label="titulo" {...methods.register("titulo")} />
            <button type="submit">Enviar</button>
          </>
        )}
      </GenericForm>,
    );

    await user.type(screen.getByLabelText("titulo"), "Inscripción");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toEqual({ titulo: "Inscripción" });
  });

  it("lets Zod own the coercion: a number travels as a number", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <GenericForm<FormValues> schema={schema} onSubmit={onSubmit}>
        {({ methods }) => (
          <>
            <input aria-label="cantidad" {...methods.register("cantidad")} />
            <button type="submit">Enviar</button>
          </>
        )}
      </GenericForm>,
    );

    await user.type(screen.getByLabelText("cantidad"), "3");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0].cantidad).toBe(3);
    expect(typeof onSubmit.mock.calls[0][0].cantidad).toBe("number");
  });

  it("hands the File over untouched", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <GenericForm<FormValues> schema={schema} onSubmit={onSubmit}>
        {({ methods }) => (
          <>
            <button
              type="button"
              onClick={() => methods.setValue("imagen", file)}
            >
              Elegir archivo
            </button>
            <button type="submit">Enviar</button>
          </>
        )}
      </GenericForm>,
    );

    await user.click(screen.getByRole("button", { name: "Elegir archivo" }));
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0].imagen).toBe(file);
  });
});

describe("GenericForm — the update mapping", () => {
  it("omits the values the user did not touch", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <GenericForm<FormValues>
        schema={schema}
        submitMode="update"
        initialData={{ titulo: "Inscripción", descripcion: "La inscripción" }}
        onSubmit={onSubmit}
      >
        {({ methods }) => (
          <>
            <input aria-label="titulo" {...methods.register("titulo")} />
            <button type="submit">Enviar</button>
          </>
        )}
      </GenericForm>,
    );

    await user.click(screen.getByRole("button", { name: "Enviar" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    // The title did not change and the description was never touched.
    expect(onSubmit.mock.calls[0][0]).toEqual({});
  });
});

describe("GenericForm — the re-hydration", () => {
  function EditForm({ initialData }: { initialData: { titulo: string } }) {
    return (
      <GenericForm<FormValues>
        schema={schema}
        initialData={initialData}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      >
        {({ methods }) => (
          <>
            <input aria-label="titulo" {...methods.register("titulo")} />
            <button type="submit">Enviar</button>
          </>
        )}
      </GenericForm>
    );
  }

  it("re-hydrates the form when the record changes", async () => {
    const { rerender } = render(<EditForm initialData={{ titulo: "A" }} />);

    expect(screen.getByLabelText("titulo")).toHaveValue("A");

    rerender(<EditForm initialData={{ titulo: "B" }} />);

    await waitFor(() =>
      expect(screen.getByLabelText("titulo")).toHaveValue("B"),
    );
  });

  it("does NOT reset when the parent rebuilds the SAME initial data", async () => {
    const user = userEvent.setup();
    const { rerender } = render(<EditForm initialData={{ titulo: "A" }} />);

    const input = screen.getByLabelText("titulo");
    await user.clear(input);
    await user.type(input, "editado");

    // The parent rebuilds the object: the CONTENT did not change.
    rerender(<EditForm initialData={{ titulo: "A" }} />);

    await waitFor(() =>
      expect(screen.getByLabelText("titulo")).toHaveValue("editado"),
    );
  });
});

describe("GenericForm — the field errors of the backend", () => {
  it("reaches the control it belongs to", async () => {
    const user = userEvent.setup();
    const onSubmit = vi
      .fn()
      .mockRejectedValue(serverError("titulo", "El título es obligatorio."));

    render(
      <GenericForm<FormValues>
        schema={schema}
        fields={[{ name: "titulo", label: "Título", type: "text" }]}
        onSubmit={onSubmit}
        submitButtonText="Enviar"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Enviar" }));

    const error = await screen.findByText("El título es obligatorio.");
    expect(error).toBeInTheDocument();
    expect(error.id).toBe("titulo-error");
  });

  it("calls setError EXACTLY ONCE per field", async () => {
    const user = userEvent.setup();
    const onSubmit = vi
      .fn()
      .mockRejectedValue(serverError("titulo", "El título es obligatorio."));

    // The calls are observed OUTSIDE the component, so the assertion can see
    // how many times `setError` was called and for which field.
    const setErrorCalls: string[] = [];

    function Harness() {
      const methods = useForm<FormValues>({
        resolver: zodResolver(schema) as unknown as Resolver<FormValues>,
      });
      // The spy is installed ONCE. Installing it on every render would wrap the
      // spy of the previous render, and the SAME call would be counted once
      // per render instead of once per field.
      const originalSetError = useRef(methods.setError);
      const spied = useRef(false);

      if (!spied.current) {
        spied.current = true;
        const original = originalSetError.current;

        (
          methods as unknown as { setError: (...args: unknown[]) => void }
        ).setError = (...args: unknown[]) => {
          setErrorCalls.push(String(args[0]));
          return (original as unknown as (...inner: unknown[]) => void)(
            ...args,
          );
        };
      }

      return (
        <GenericForm<FormValues>
          schema={schema}
          formMethods={methods}
          onSubmit={onSubmit}
        >
          {() => <button type="submit">Enviar</button>}
        </GenericForm>
      );
    }

    render(<Harness />);

    await user.click(screen.getByRole("button", { name: "Enviar" }));

    await waitFor(() => expect(setErrorCalls.length).toBeGreaterThan(0));
    expect(setErrorCalls).toEqual(["titulo"]);
  });
});
