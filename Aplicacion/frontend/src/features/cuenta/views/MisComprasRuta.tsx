"use client";

import { useComprasCuenta } from "../hooks/useComprasCuenta";
import { MisComprasView } from "./MisComprasView";

export function MisComprasRuta({
  filtros,
}: {
  filtros: Record<string, string | undefined>;
}) {
  const consulta = useComprasCuenta();

  if (consulta.isPending) {
    return <MisComprasView estado="cargando" filtros={filtros} />;
  }

  if (consulta.isError) {
    return <MisComprasView estado="error" filtros={filtros} />;
  }

  return (
    <MisComprasView estado="listo" compras={consulta.data} filtros={filtros} />
  );
}
