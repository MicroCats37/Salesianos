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

/**
 * User data returned directly from POST /auth/register.
 */
export interface RegisterUser {
  id: string;
  username: string;
  email: string;
  is_staff: boolean;
  is_superuser: boolean;
  persona_id: string | null;
}

export interface AuthSlice {
  user: AuthUser | null;
  isAuthenticated: boolean;
  setAuth: (user: AuthUser) => void;
  logout: () => void;
}

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
