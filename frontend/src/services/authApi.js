import { apiGet, apiPost, setAuthToken } from "./api";

export async function registerUser(payload) {
  const backendPayload = {
    username: payload.name || payload.username || "",
    email: payload.email,
    password: payload.password,
    role: payload.role || "operator"
  };
  return apiPost("/api/auth/register", backendPayload, { token: null });
}

export async function login(payload) {
  const result = await apiPost("/api/auth/login", payload, {
    token: null,
  });

  setAuthToken(result.access_token);
  return result;
}

// Only keep this if backend has GET /api/auth/me
export async function getCurrentUser() {
  return apiGet("/api/auth/me");
}

export function logout() {
  setAuthToken(null);
}