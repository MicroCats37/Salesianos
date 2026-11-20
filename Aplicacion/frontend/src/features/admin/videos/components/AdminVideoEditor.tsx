"use client";

import { AlignLeft, Link, Type } from "lucide-react";
import { useId, useMemo } from "react";
import { FormField } from "@/components/forms/FormField";
import { FormFooter } from "@/components/forms/FormFooter";
import { FormGrid } from "@/components/forms/FormGrid";
import { GenericForm } from "@/components/genericForm/GenericForm";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { VideoListItem } from "@/features/videos/schemas/video.schema";
import {
  type CrearVideoFormData,
  CrearVideoFormSchema,
} from "../schemas/admin.video.schema";

export interface AdminVideoEditorProps {
  /** Whether the editor is open. */
  abierto: boolean;
  /** Called when the editor opens or closes. */
  onAbiertoChange: (abierto: boolean) => void;
  /** The video that is being edited, when the editor edits one. */
  video?: VideoListItem;
  /** Whether the editor is waiting for the server. */
  ocupado?: boolean;
  /**
   * The publication.
   *
   * It REJECTS when the server refuses, so the form receives the field errors
   * of the answer and puts each one next to the control that owns it.
   */
  onGuardar: (datos: CrearVideoFormData) => Promise<void>;
}

/**
 * AdminVideoEditor - the publication and the edition of a video.
 *
 * The form is the Mode 1 (`children`) of `GenericForm`: the label and the
 * error of every field are drawn ONCE, by `FormField`, and the validation
 * lives in Zod and the payload is built by the hook of the mutation, never
 * here.
 *
 * The edition is a `PATCH`: the fields that the operator did not touch do not
 * travel, because `GenericForm` diffs the values against the ones that the
 * video already had.
 */
export function AdminVideoEditor({
  abierto,
  onAbiertoChange,
  video,
  ocupado = false,
  onGuardar,
}: AdminVideoEditorProps) {
  const idBase = useId();

  const editando = Boolean(video);

  const valoresIniciales = useMemo<CrearVideoFormData>(
    () =>
      video
        ? {
            titulo: video.titulo,
            descripcion: video.descripcion,
            url: video.url,
          }
        : { titulo: "", descripcion: "", url: "" },
    [video],
  );

  return (
    <Dialog open={abierto} onOpenChange={onAbiertoChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {editando ? "Editar el video" : "Publicar un video"}
          </DialogTitle>
          <DialogDescription>
            {editando
              ? "Solo viajan al servidor los campos que cambies."
              : "El video aparece en la sala de proyección en cuanto el servidor lo acepta."}
          </DialogDescription>
        </DialogHeader>

        <GenericForm<CrearVideoFormData>
          schema={CrearVideoFormSchema}
          submitMode={editando ? "update" : "create"}
          initialData={valoresIniciales}
          onSubmit={onGuardar}
          isLoading={ocupado}
          formClassName="flex flex-col gap-4"
        >
          {({ methods, isSubmitting, submissionMessage }) => {
            const {
              formState: { errors },
            } = methods;

            return (
              <>
                <FormGrid>
                  <FormField
                    id={`${idBase}-titulo`}
                    label="Título"
                    required
                    icon={Type}
                    span={12}
                    error={errors.titulo?.message}
                  >
                    {(control) => (
                      <Input {...control} {...methods.register("titulo")} />
                    )}
                  </FormField>

                  <FormField
                    id={`${idBase}-descripcion`}
                    label="Descripción (opcional)"
                    icon={AlignLeft}
                    span={12}
                    error={errors.descripcion?.message}
                  >
                    {(control) => (
                      <Textarea
                        {...control}
                        {...methods.register("descripcion")}
                        rows={3}
                      />
                    )}
                  </FormField>

                  <FormField
                    id={`${idBase}-url`}
                    label="Dirección del video (http o https)"
                    required
                    icon={Link}
                    span={12}
                    error={errors.url?.message}
                  >
                    {(control) => (
                      <Input
                        {...control}
                        type="url"
                        inputMode="url"
                        {...methods.register("url")}
                      />
                    )}
                  </FormField>

                  <FormFooter
                    submitLabel={
                      editando ? "Guardar los cambios" : "Publicar el video"
                    }
                    pendingLabel="Guardando…"
                    onCancel={() => onAbiertoChange(false)}
                    isSubmitting={isSubmitting}
                  />
                </FormGrid>

                {submissionMessage?.type === "error" ? (
                  <p role="alert" className="text-caption text-destructive">
                    {submissionMessage.message}
                  </p>
                ) : null}
              </>
            );
          }}
        </GenericForm>
      </DialogContent>
    </Dialog>
  );
}
