"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchPaquetes } from "../paquetes.service";

export function useLandingPaquetes() {
  return useQuery({
    queryKey: ["landing", "paquetes"],
    queryFn: fetchPaquetes,
  });
}
