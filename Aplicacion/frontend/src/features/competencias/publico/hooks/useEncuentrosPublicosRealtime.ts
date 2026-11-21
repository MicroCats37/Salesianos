"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { encuentroActualizadoEventSchema } from "../schemas/encuentro-realtime.schema";
import { claveEncuentrosPublicos } from "../utils/encuentro-publico.claves.utils";

function websocketUrl() {
  if (typeof window === "undefined") return null;
  const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${scheme}//${window.location.host}/ws/encuentros/`;
}

/** Revalidates the HTTP snapshot when the server commits a public change. */
export function useEncuentrosPublicosRealtime() {
  const queryClient = useQueryClient();

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
        void queryClient.invalidateQueries({
          queryKey: claveEncuentrosPublicos,
        });
      };
      socket.onmessage = (message) => {
        try {
          const event = encuentroActualizadoEventSchema.parse(
            JSON.parse(message.data),
          );
          if (event.type === "encuentro.actualizado") {
            void queryClient.invalidateQueries({
              queryKey: claveEncuentrosPublicos,
            });
          }
        } catch {
          // Unknown events are ignored; HTTP remains the source of truth.
        }
      };
      socket.onclose = () => {
        if (stopped) return;
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
}
