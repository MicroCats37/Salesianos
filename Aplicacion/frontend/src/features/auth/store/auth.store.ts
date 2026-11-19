import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export interface AuthUser {
  id: string;
  email: string;
  username?: string;
  nombres?: string;
  apellidos?: string;
  rol?: string;
  /** ID de la persona asociada al usuario (null si el usuario no tiene persona vinculada). */
  persona_id?: string | null;
}

export interface AuthSlice {
  user: AuthUser | null;
  isAuthenticated: boolean;
  setAuth: (user: AuthUser) => void;
  logout: () => void;
}

/**
 * Client-side mirror of the session, used ONLY to paint the shell.
 *
 * It is a convenience, never an authority: the cookie session read on the
 * server decides access, and the backend re-evaluates every capability on
 * every request. The store exists so the shell can render a name and a
 * logout button without a round trip.
 */
export const useAuthStore = create<AuthSlice>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setAuth: (user) => set({ user, isAuthenticated: true }),
      logout: () => set({ user: null, isAuthenticated: false }),
    }),
    {
      name: "salesianos-auth-user",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ user: state.user }),
    },
  ),
);

export const useAuthUser = () => useAuthStore((state) => state.user);
