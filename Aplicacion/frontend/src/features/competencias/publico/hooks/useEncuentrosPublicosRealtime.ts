"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { backendPublicUrl } from "@/lib/server/backend-url";
import { encuentroActualizadoEventSchema } from "../schemas/encuentro-realtime.schema";
import { claveEncuentrosPublicos } from "../utils/encuentro-publico.claves.utils";

function websocketUrl() {
  if (typeof window === "undefined") return null;
  const apiBase = backendPublicUrl();
  const backend = /^https?:\/\//i.test(apiBase)
    ? new URL(apiBase)
    : new URL(window.location.origin);
  backend.protocol = backend.protocol === "https:" ? "wss:" : "ws:";
  backend.pathname = "/ws/encuentros/";
  backend.search = "";
  backend.hash = "";
  return backend.toString();
}

export type EstadoRealtime = "conectando" | "conectado" | "reconectando";

/** Revalidates the HTTP snapshot when the server commits a public change. */
export function useEncuentrosPublicosRealtime() {
  const queryClient = useQueryClient();
  const [estado, setEstado] = useState<EstadoRealtime>("conectando");
  const [actualizadoEn, setActualizadoEn] = useState<Date | null>(null);

  useEffect(() => {
    const url = websocketUrl();
    if (!url) return;

    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let stopped = false;
    let attempt = 0;

    const connect = () => {
      if (stopped || document.visibilityState === "hidden") return;
      socket = new WebSocket(url);
      socket.onopen = () => {
        attempt = 0;
        setEstado("conectado");
        void queryClient.invalidateQueries({
          queryKey: claveEncuentrosPublicos,
        });
      };
      socket.onmessage = async (message) => {
        try {
          const event = encuentroActualizadoEventSchema.parse(
            JSON.parse(message.data),
          );
          if (event.type === "encuentro.actualizado") {
            await queryClient.refetchQueries({
              queryKey: claveEncuentrosPublicos,
              type: "active",
            });
            setActualizadoEn(new Date(event.occurred_at));
          }
        } catch {
          // Unknown events are ignored; HTTP remains the source of truth.
        }
      };
      socket.onclose = () => {
        if (stopped) return;
        setEstado("reconectando");
        const delay = Math.min(30_000, 1_000 * 2 ** attempt++);
        retryTimer = setTimeout(connect, delay);
      };
    };

    const visibility = () => {
      if (
        document.visibilityState === "visible" &&
        socket?.readyState !== WebSocket.OPEN
      ) {
        connect();
      }
    };

    connect();
    document.addEventListener("visibilitychange", visibility);
    return () => {
      stopped = true;
      document.removeEventListener("visibilitychange", visibility);
      if (retryTimer) clearTimeout(retryTimer);
      socket?.close();
    };
  }, [queryClient]);

  return { estado, actualizadoEn };
}
