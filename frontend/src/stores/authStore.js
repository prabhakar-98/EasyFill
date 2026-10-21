import { create } from "zustand";
import { apiFetch } from "../lib/api";

const useAuthStore = create((set, get) => ({
  token: localStorage.getItem("token") || null,
  user: JSON.parse(localStorage.getItem("user") || "null"),
  loading: false,
  error: null,

  register: async (email, password, first_name, last_name) => {
    set({ loading: true, error: null });
    try {
      const res = await apiFetch("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, first_name, last_name }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        set({ loading: false, error: err.detail || "Registration failed" });
        return false;
      }
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      set({ token: data.access_token, user: data.user, loading: false });
      return true;
    } catch (e) {
      set({ loading: false, error: e.message });
      return false;
    }
  },

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const res = await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        set({ loading: false, error: err.detail || "Login failed" });
        return false;
      }
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      set({ token: data.access_token, user: data.user, loading: false });
      return true;
    } catch (e) {
      set({ loading: false, error: e.message });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    set({ token: null, user: null });
  },

  fetchMe: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await apiFetch("/api/auth/me");
      if (!res.ok) {
        get().logout();
        return;
      }
      const data = await res.json();
      localStorage.setItem("user", JSON.stringify(data));
      set({ user: data });
    } catch {
      get().logout();
    }
  },
}));

export default useAuthStore;
