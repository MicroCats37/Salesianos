"use client";

import {
  useCatalogoCategorias,
  useCatalogoDisciplinas,
} from "@/features/inscripciones/hooks/useCatalogo";
import { CrearCompetenciaForm } from "../components/CrearCompetenciaForm";
import { useCompetenciasLista } from "../hooks/useCompetencias";
import type { CategoriaDeEdicion } from "../types/competencia.types";
import { mensajeDeError } from "../utils/competencias.errores.utils";
import { estadoDesdeConsulta } from "../utils/competencias.estado.utils";
import { CompetenciasListaView } from "./CompetenciasListaView";

/**
 * The container of `/administracion/competencias` (`ADM-10`).
 *
 * The page only routes: the CONTAINER is the one that reads the data and
 * hands the state to the view.
 */
export interface CompetenciasListaRutaProps {
  /** The state filter of the URL. */
  filtroEstado?: string;
  /** The band filter of the URL. */
  filtroCategoria?: string;
}

/**
 * The competitions of the edition, with the bands of the catalogue.
 *
 * ## The catalogue of the bands is BORROWED, not owned
 *
 * The OPTIONS of the band filter are the bands that the catalogue of the
 * edition publishes (`GET /catalogo/categorias`, `RT-IN-16`), read with the
 * CANONICAL client of the catalogue (`features/inscripciones`): one
 * endpoint, one client and one key namespace (`salesianos-api-data`,
 * FND-08 regla 1). This route declares NO second client and NO second key
 * for the same answer, and it invents NO band: the browser never deduces
 * which band a cohort belongs to (`RN-C02`, `QA-K01`).
 *
 * ## A failure of the catalogue does NOT hide the list
 *
 * The catalogue is a SECONDARY read: it only feeds the options of the
 * filter. If it fails, the list of competitions is still drawn and the
 * filter of the band says, out loud, that it is not available. The retry
 * action reads BOTH again.
 */
export function CompetenciasListaRuta({
  filtroEstado,
  filtroCategoria,
}: CompetenciasListaRutaProps) {
  const consulta = useCompetenciasLista({
    estado: filtroEstado,
    categoria_id: filtroCategoria,
  });

  const catalogo = useCatalogoCategorias();
  const disciplinasCatalogo = useCatalogoDisciplinas();

  const categorias: CategoriaDeEdicion[] =
    catalogo.data?.categorias.map((categoria) => ({
      id: categoria.id,
      nombre: categoria.nombre,
    })) ?? [];

  const reintentar = () => {
    void consulta.refetch();
    void catalogo.refetch();
  };

  return (
    <>
      <CrearCompetenciaForm
        disciplinas={disciplinasCatalogo.data?.disciplinas ?? []}
        categorias={catalogo.data?.categorias ?? []}
      />
      <CompetenciasListaView
        estado={estadoDesdeConsulta(consulta)}
        competencias={consulta.data ?? []}
        categorias={categorias}
        filtroEstado={filtroEstado}
        filtroCategoria={filtroCategoria}
        reintentar={reintentar}
        mensajeError={
          consulta.isError ? mensajeDeError(consulta.error) : undefined
        }
        avisoCatalogos={
          catalogo.isError
            ? "No se pudo cargar el catálogo de categorías, así que el filtro de categoría no está disponible."
            : undefined
        }
      />
    </>
  );
}
