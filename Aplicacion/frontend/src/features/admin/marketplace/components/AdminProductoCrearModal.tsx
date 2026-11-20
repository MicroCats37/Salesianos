"use client";

import {
  AlignLeft,
  BadgeDollarSign,
  Boxes,
  CalendarClock,
  Hash,
  ImagePlus,
  Layers,
  Package,
  Tag,
  Trash2,
  Type,
} from "lucide-react";
import type { UseFormReturn } from "react-hook-form";
import { useController, useWatch } from "react-hook-form";
import { FormField } from "@/components/forms/FormField";
import { FormGrid } from "@/components/forms/FormGrid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AppFormModal } from "@/components-app/forms/AppFormModal";
import {
  type CategoriaLista,
  type ProductoCrearFormData,
  productoCrearFormSchema,
} from "@/features/marketplace/schemas/producto.schema";

export interface AdminProductoCrearModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  categorias: CategoriaLista[];
  categoriasCargando: boolean;
  creando: boolean;
  onCrear: (datos: ProductoCrearFormData) => Promise<unknown>;
}

const valoresIniciales: ProductoCrearFormData = {
  nombre: "",
  slug: "",
  descripcion: "",
  categoria_id: null,
  precio: 0,
  precio_oferta: null,
  oferta_inicia: null,
  oferta_termina: null,
  estado: "ACTIVO",
  stock_inicial: 0,
  imagenes: [],
};

export function AdminProductoCrearModal({
  open,
  onOpenChange,
  categorias,
  categoriasCargando,
  creando,
  onCrear,
}: AdminProductoCrearModalProps) {
  return (
    <AppFormModal<ProductoCrearFormData>
      open={open}
      onOpenChange={onOpenChange}
      title="Nuevo producto"
      description="Define la ficha comercial y su galería. La primera imagen cargada queda como principal hasta que elijas otra."
      eyebrow="Tienda"
      icon={<Package className="size-5" aria-hidden="true" />}
      primaryLabel="Crear producto"
      primaryLoadingLabel="Creando..."
      primaryLoading={creando}
      primaryDisabled={categoriasCargando}
      onPrimary={() => undefined}
      schema={productoCrearFormSchema}
      initialData={valoresIniciales}
      onSubmit={onCrear}
      showErrorsAsToasts
      size="xl"
      bodyClassName="max-h-[70vh] overflow-y-auto"
      formClassName="flex flex-col gap-4"
    >
      {({ methods, isSubmitting, submissionMessage }) => (
        <>
          {submissionMessage?.type === "error" ? (
            <p
              role="alert"
              className="rounded-[var(--radius-md)] border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive"
            >
              {submissionMessage.message}
            </p>
          ) : null}
          <CamposProducto
            methods={methods}
            categorias={categorias}
            categoriasCargando={categoriasCargando}
            bloqueado={isSubmitting}
          />
        </>
      )}
    </AppFormModal>
  );
}

/**
 * Los campos de la ficha comercial.
 *
 * El formulario es el Modo 1 (`children`): la etiqueta, el icono y el error de
 * cada campo los dibuja UNA vez `FormField`. Los valores que el formulario
 * tiene que observar (`categoria_id`, `estado` e `imagenes`) se leen con
 * `useController` y `useWatch` ACOTADOS a su campo: el formulario no se
 * vuelve a dibujar con cada tecla.
 */
function CamposProducto({
  methods,
  categorias,
  categoriasCargando,
  bloqueado,
}: {
  methods: UseFormReturn<ProductoCrearFormData>;
  categorias: CategoriaLista[];
  categoriasCargando: boolean;
  bloqueado: boolean;
}) {
  const {
    register,
    setValue,
    control: controlFormulario,
    formState: { errors },
  } = methods;

  const { field: categoria } = useController({
    control: controlFormulario,
    name: "categoria_id",
  });
  const { field: estado } = useController({
    control: controlFormulario,
    name: "estado",
  });
  const imagenes =
    useWatch({ control: controlFormulario, name: "imagenes" }) ?? [];

  return (
    <fieldset disabled={bloqueado} className="contents">
      <FormGrid>
        <FormField
          id="producto-nombre"
          label="Nombre"
          required
          icon={Type}
          span={6}
          error={errors.nombre?.message}
        >
          {(control) => (
            <Input {...control} {...register("nombre")} autoFocus />
          )}
        </FormField>

        <FormField
          id="producto-slug"
          label="Slug"
          required
          icon={Hash}
          span={6}
          helper="El identificador con el que se publica el producto."
          error={errors.slug?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("slug")}
              placeholder="camiseta-festival"
            />
          )}
        </FormField>

        <FormField
          id="producto-categoria"
          label="Categoría"
          icon={Layers}
          span={6}
          error={errors.categoria_id?.message}
        >
          {(control) => (
            <Select
              value={categoria.value ?? "sin-categoria"}
              onValueChange={(valor) =>
                categoria.onChange(valor === "sin-categoria" ? null : valor)
              }
              disabled={categoriasCargando}
            >
              <SelectTrigger
                {...control}
                onBlur={categoria.onBlur}
                className="w-full"
              >
                <SelectValue placeholder="Elige la categoría" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sin-categoria">Sin categoría</SelectItem>
                {categorias.map((categoriaActual) => (
                  <SelectItem
                    key={categoriaActual.id}
                    value={categoriaActual.id}
                  >
                    {categoriaActual.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </FormField>

        <FormField
          id="producto-estado"
          label="Estado"
          required
          icon={Tag}
          span={6}
          error={errors.estado?.message}
        >
          {(control) => (
            <Select
              value={estado.value}
              onValueChange={(valor) =>
                estado.onChange(valor as "ACTIVO" | "INACTIVO")
              }
            >
              <SelectTrigger
                {...control}
                onBlur={estado.onBlur}
                className="w-full"
              >
                <SelectValue placeholder="Elige el estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ACTIVO">Activo</SelectItem>
                <SelectItem value="INACTIVO">Inactivo</SelectItem>
              </SelectContent>
            </Select>
          )}
        </FormField>

        <FormField
          id="producto-descripcion"
          label="Descripción"
          icon={AlignLeft}
          span={12}
          error={errors.descripcion?.message}
        >
          {(control) => (
            <Textarea {...control} {...register("descripcion")} rows={4} />
          )}
        </FormField>

        <FormField
          id="producto-precio"
          label="Precio"
          required
          icon={BadgeDollarSign}
          span={4}
          error={errors.precio?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("precio")}
              type="number"
              min="0"
              step="0.01"
              inputMode="decimal"
            />
          )}
        </FormField>

        <FormField
          id="producto-precio-oferta"
          label="Precio de oferta"
          icon={BadgeDollarSign}
          span={4}
          helper="Déjalo vacío si el producto no tiene oferta."
          error={errors.precio_oferta?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("precio_oferta")}
              type="number"
              min="0"
              step="0.01"
              inputMode="decimal"
            />
          )}
        </FormField>

        <FormField
          id="producto-stock"
          label="Stock inicial"
          required
          icon={Boxes}
          span={4}
          error={errors.stock_inicial?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("stock_inicial")}
              type="number"
              min="0"
              step="1"
              inputMode="numeric"
            />
          )}
        </FormField>

        <FormField
          id="producto-oferta-inicia"
          label="Inicio de oferta"
          icon={CalendarClock}
          span={6}
          error={errors.oferta_inicia?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("oferta_inicia")}
              type="datetime-local"
            />
          )}
        </FormField>

        <FormField
          id="producto-oferta-termina"
          label="Fin de oferta"
          icon={CalendarClock}
          span={6}
          error={errors.oferta_termina?.message}
        >
          {(control) => (
            <Input
              {...control}
              {...register("oferta_termina")}
              type="datetime-local"
            />
          )}
        </FormField>
      </FormGrid>

      <section
        aria-labelledby="galeria-titulo"
        className="flex flex-col gap-4 border-t border-border pt-5"
      >
        <div className="flex flex-col gap-1">
          <h3
            id="galeria-titulo"
            className="text-sm font-semibold text-foreground"
          >
            Galería
          </h3>
          <p className="text-caption text-muted-foreground">
            Carga varias imágenes, elige una principal y escribe un texto
            alternativo para cada una.
          </p>
        </div>

        <FormField
          id="producto-imagenes"
          label="Imágenes del producto"
          span={12}
          error={errors.imagenes?.message}
        >
          {(control) => (
            <Input
              {...control}
              type="file"
              accept="image/*"
              multiple
              onChange={(evento) => {
                const archivos = Array.from(evento.target.files ?? []);
                if (archivos.length === 0) return;
                const siguientes = archivos.map((archivo, indice) => ({
                  archivo,
                  texto_alternativo: archivo.name,
                  es_principal: imagenes.length === 0 && indice === 0,
                }));
                setValue("imagenes", [...imagenes, ...siguientes], {
                  shouldDirty: true,
                  shouldValidate: true,
                });
                evento.target.value = "";
              }}
            />
          )}
        </FormField>

        {imagenes.length > 0 ? (
          <ul className="flex flex-col gap-3">
            {imagenes.map((imagen, indice) => (
              <li
                key={`${imagen.archivo.name}-${indice}`}
                className="grid gap-2 rounded-[var(--radius-md)] border border-border p-3 sm:grid-cols-[auto_1fr_auto_auto] sm:items-center"
              >
                <ImagePlus
                  className="size-4 text-muted-foreground"
                  aria-hidden="true"
                />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">
                    {imagen.archivo.name}
                  </p>
                  <Input
                    value={imagen.texto_alternativo}
                    onChange={(evento) => {
                      const siguientes = [...imagenes];
                      siguientes[indice] = {
                        ...imagen,
                        texto_alternativo: evento.target.value,
                      };
                      setValue("imagenes", siguientes, { shouldDirty: true });
                    }}
                    aria-label={`Texto alternativo de ${imagen.archivo.name}`}
                    placeholder="Texto alternativo"
                    className="mt-2 min-h-11"
                  />
                </div>
                <label className="flex min-h-11 items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="imagen-principal"
                    checked={imagen.es_principal}
                    onChange={() =>
                      setValue(
                        "imagenes",
                        imagenes.map((actual, posicion) => ({
                          ...actual,
                          es_principal: posicion === indice,
                        })),
                        { shouldDirty: true, shouldValidate: true },
                      )
                    }
                  />
                  Principal
                </label>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label={`Quitar ${imagen.archivo.name}`}
                  onClick={() => {
                    const restantes = imagenes.filter(
                      (_, posicion) => posicion !== indice,
                    );
                    if (
                      restantes.length > 0 &&
                      !restantes.some((actual) => actual.es_principal)
                    ) {
                      restantes[0] = { ...restantes[0], es_principal: true };
                    }
                    setValue("imagenes", restantes, {
                      shouldDirty: true,
                      shouldValidate: true,
                    });
                  }}
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </Button>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </fieldset>
  );
}
