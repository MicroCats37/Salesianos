import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { useShallow } from "zustand/react/shallow";
import type { User } from "../schemas";

export interface AuthSlice {
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (user: User) => void;
  setUser: (user: User | null) => void;
  clearUser: () => void;
}

export const useAuthStore = create<AuthSlice>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setAuth: (user) => set({ user, isAuthenticated: true }),
      setUser: (user) => set({ user, isAuthenticated: Boolean(user) }),
      clearUser: () => set({ user: null, isAuthenticated: false }),
    }),
    {
      name: "salesianos-auth-user",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ user: state.user }),
    },
  ),
);

export const useAuthUser = () => useAuthStore((s) => s.user);

export const useAuthState = () =>
  useAuthStore(
    useShallow((s) => ({
      user: s.user,
      isAuthenticated: s.isAuthenticated,
      setAuth: s.setAuth,
      setUser: s.setUser,
      clearUser: s.clearUser,
    })),
  );
