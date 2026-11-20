import { ArrowRight, ShoppingBag } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemHeader,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableHeader as Thead,
} from "@/components/ui/table";
import { RUTAS } from "@/lib/routes";
import type { CompraResumen, OrigenCompra } from "../types/cuenta.types";
import { VeredictoEstado } from "./VeredictoEstado";

export interface ListaComprasProps {
  /** The purchases to list. */
  compras: CompraResumen[];
  className?: string;
}

/**
 * The three origins of a purchase, in the order the reader expects them.
 *
 * The groups are NOT a business rule: the backend groups by origin and the
 * client only names the three the plan declares (frontend/03).
 */
export const ORIGENES: { valor: OrigenCompra; etiqueta: string }[] = [
  { valor: "INSCRIPCION", etiqueta: "Inscripción" },
  { valor: "PASE", etiqueta: "Pase" },
  { valor: "MARKETPLACE", etiqueta: "Tienda" },
];

/** The name of an origin, without a dictionary of business codes. */
export function etiquetaOrigen(origen: OrigenCompra) {
  return ORIGENES.find((item) => item.valor === origen)?.etiqueta ?? "Compra";
}

/**
 * The amount, as the backend sends it.
 *
 * The amount is a STRING and it is never converted into a number: the
 * decimals belong to the server. The tabular numerals keep the column from
 * reflowing when the amount changes (RB-01 ACCOUNT-04).
 */
function formatearMonto(monto: string, moneda: string) {
  return `${moneda} ${monto}`;
}

/**
 * ListaCompras - the purchases of the responsible, grouped by origin.
 *
 * A purchase and its payment are two different things: a purchase may be
 * paid, pending or cancelled, and only the backend knows which one is
 * which. The list shows the verdict, never a recomputation.
 */
export function ListaCompras({ compras, className }: ListaComprasProps) {
  return (
    <div className={className}>
      {/* Cards below 1024: the origin is the header of the card. */}
      <ItemGroup className="gap-3 lg:hidden">
        {compras.map((compra) => (
          // biome-ignore lint/a11y/useSemanticElements: el `Item` del proyecto renderiza un `div`, así que la lista se construye con el rol ARIA y no con `<li>`; cambiar el elemento del componente compartido está fuera de esta zona.
          <Item
            key={compra.id}
            variant="outline"
            role="listitem"
            className="flex-col items-stretch gap-3"
          >
            <ItemHeader>
              <ItemMedia variant="icon">
                <ShoppingBag
                  className="size-4 text-primary"
                  aria-hidden="true"
                />
              </ItemMedia>
              <ItemContent>
                <ItemTitle className="text-foreground">
                  {etiquetaOrigen(compra.origen)}
                </ItemTitle>
                <ItemDescription>{compra.concepto}</ItemDescription>
              </ItemContent>
              <ItemActions>
                <VeredictoEstado veredicto={compra.veredicto} />
              </ItemActions>
            </ItemHeader>

            <dl className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-0.5">
                <dt className="text-caption text-muted-foreground">Importe</dt>
                <dd className="text-sm font-semibold tabular-nums text-foreground">
                  {formatearMonto(compra.monto, compra.moneda)}
                </dd>
              </div>
              <div className="flex flex-col gap-0.5">
                <dt className="text-caption text-muted-foreground">Fecha</dt>
                <dd className="text-sm font-semibold text-foreground">
                  {compra.fecha}
                </dd>
              </div>
            </dl>

            <Button asChild variant="outline" className="min-h-11 w-full">
              <Link href={RUTAS.cuenta.misComprasDetalle(compra.id)}>
                Ver la compra
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
          </Item>
        ))}
      </ItemGroup>

      {/* Table from 1024: the origin is its own column. */}
      <div className="hidden lg:block">
        <Table>
          <Thead>
            <TableRow>
              <TableHead scope="col">Origen</TableHead>
              <TableHead scope="col">Concepto</TableHead>
              <TableHead scope="col">Fecha</TableHead>
              <TableHead scope="col">Importe</TableHead>
              <TableHead scope="col">Estado</TableHead>
              <TableHead scope="col">Detalle</TableHead>
            </TableRow>
          </Thead>
          <TableBody>
            {compras.map((compra) => (
              <TableRow key={compra.id}>
                <TableCell className="font-semibold text-foreground">
                  {etiquetaOrigen(compra.origen)}
                </TableCell>
                <TableCell>{compra.concepto}</TableCell>
                <TableCell className="text-muted-foreground">
                  {compra.fecha}
                </TableCell>
                <TableCell className="font-semibold tabular-nums text-foreground">
                  {formatearMonto(compra.monto, compra.moneda)}
                </TableCell>
                <TableCell>
                  <VeredictoEstado veredicto={compra.veredicto} />
                </TableCell>
                <TableCell>
                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="min-h-11"
                  >
                    <Link href={RUTAS.cuenta.misComprasDetalle(compra.id)}>
                      Ver la compra
                      <ArrowRight className="size-4" aria-hidden="true" />
                    </Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
