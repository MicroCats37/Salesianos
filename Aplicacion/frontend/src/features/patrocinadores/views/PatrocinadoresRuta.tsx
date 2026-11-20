"use client";

import { useState } from "react";
import { ConfirmacionIrreversible } from "@/features/admin/operaciones/components/ConfirmacionIrreversible";
import { ApiQueryError } from "@/hooks";
import {
  usePatrocinadoresAdmin,
  usePatrocinadorMutaciones,
} from "../hooks/usePatrocinadores";
import type { FormularioPatrocinadorDatos } from "../schemas/patrocinador.schema";
import type {
  EstadoVistaPatrocinadores,
  Patrocinador,
} from "../types/patrocinador.types";
import { PatrocinadoresAdminView } from "./PatrocinadoresAdminView";

export function PatrocinadoresRuta() {
  const consulta = usePatrocinadoresAdmin();
  const mutaciones = usePatrocinadorMutaciones();

  const [seleccionado, setSeleccionado] = useState<Patrocinador | null>(null);
  const [porEliminar, setPorEliminar] = useState<Patrocinador | null>(null);

  const patrocinadores = consulta.data ?? [];

  const estado: EstadoVistaPatrocinadores = consulta.isPending
    ? "cargando"
    : consulta.isError
      ? consulta.error instanceof ApiQueryError && consulta.error.status === 403
        ? "sin-permiso"
        : "error"
      : "listo";

  const ocupado =
    mutaciones.crear.isPending ||
    mutaciones.actualizar.isPending ||
    mutaciones.eliminar.isPending ||
    mutaciones.reordenar.isPending;

  const crear = async (datos: FormularioPatrocinadorDatos) => {
    await mutaciones.crear.mutateAsync({
      nombre: datos.nombre,
      slug: datos.slug,
      descripcion: datos.descripcion,
      sitio_web: datos.sitio_web,
      visible: datos.visible,
      logo: datos.logo ?? null,
      imagenes: datos.imagenes.map((archivo) => ({
        token: archivo,
        texto_alternativo: archivo.name,
      })),
    });
  };

  const actualizar = async (
    datos: FormularioPatrocinadorDatos,
    patrocinador: Patrocinador,
  ) => {
    await mutaciones.actualizar.mutateAsync({
      id: patrocinador.id,
      data: {
        nombre: datos.nombre,
        descripcion: datos.descripcion,
        sitio_web: datos.sitio_web,
        visible: datos.visible,
      },
    });
    setSeleccionado(null);
  };

  const mover = (patrocinador: Patrocinador, direccion: -1 | 1) => {
    const ordenados = [...patrocinadores];
    const indice = ordenados.findIndex((item) => item.id === patrocinador.id);
    const destino = indice + direccion;
    if (indice < 0 || destino < 0 || destino >= ordenados.length) return;

    [ordenados[indice], ordenados[destino]] = [
      ordenados[destino],
      ordenados[indice],
    ];

    void mutaciones.reordenar.mutateAsync({
      patrocinador_ids: ordenados.map((item) => item.id),
    });
  };

  return (
    <>
      <PatrocinadoresAdminView
        estado={estado}
        patrocinadores={patrocinadores}
        seleccionado={seleccionado ?? undefined}
        onSeleccionar={setSeleccionado}
        onCrear={crear}
        onActualizar={actualizar}
        onEliminar={setPorEliminar}
        onSubir={(patrocinador) => mover(patrocinador, -1)}
        onBajar={(patrocinador) => mover(patrocinador, 1)}
        ocupado={ocupado}
      />

      <ConfirmacionIrreversible
        abierto={Boolean(porEliminar)}
        onAbiertoChange={(abierto) => {
          if (!abierto) setPorEliminar(null);
        }}
        titulo={`Eliminar ${porEliminar?.nombre ?? "el patrocinador"}`}
        efecto="El patrocinador se borra de la edición y con él se van su logo y su galería. La acción no se puede deshacer."
        motivo={{
          etiqueta: "Motivo de la eliminación",
          placeholder: "Por qué se elimina este patrocinador",
        }}
        confirmar={{
          etiqueta: "Eliminar el patrocinador",
          enCurso: mutaciones.eliminar.isPending,
        }}
        onConfirmar={() => {
          if (!porEliminar) return;
          void mutaciones.eliminar.mutateAsync(porEliminar.id);
          setPorEliminar(null);
          setSeleccionado(null);
        }}
      />
    </>
  );
}
