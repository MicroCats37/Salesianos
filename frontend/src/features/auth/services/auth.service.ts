import { api } from "@/lib/api";
import type { ApiResponse } from "@/shared/types/api.types";
import type {
  LoginDniFormData,
  LoginEmailFormData,
  LoginFormData,
  LoginUsernameFormData,
  RegisterFormData,
  User,
} from "../schemas";

/**
 * Login with legacy single-field identifier (email or DNI).
 */
export async function login(
  credentials: LoginFormData,
): Promise<ApiResponse<User>> {
  const { data } = await api.post<ApiResponse<User>>("/api/auth/login", {
    identifier: credentials.identifier,
    password: credentials.password,
  });
  return data;
}

/**
 * Login with username - routes to POST /api/auth/login
 * with identifier = username
 */
export async function loginUsername(
  username: string,
  password: string,
): Promise<ApiResponse<User>> {
  const { data } = await api.post<ApiResponse<User>>("/api/auth/login", {
    identifier: username,
    password,
  });
  return data;
}

/**
 * Login with DNI - routes to POST /api/auth/login
 * with identifier = dni (8-digit Peruvian document)
 */
export async function loginDni(
  dni: string,
  password: string,
): Promise<ApiResponse<User>> {
  const { data } = await api.post<ApiResponse<User>>("/api/auth/login", {
    identifier: dni,
    password,
  });
  return data;
}

/**
 * Login with email - routes to POST /api/auth/login
 * with identifier = email
 */
export async function loginEmail(
  email: string,
  password: string,
): Promise<ApiResponse<User>> {
  const { data } = await api.post<ApiResponse<User>>("/api/auth/login", {
    identifier: email,
    password,
  });
  return data;
}

export async function registerUser(
  formData: RegisterFormData,
): Promise<ApiResponse<User>> {
  const { data } = await api.post<ApiResponse<User>>("/api/auth/register", {
    email: formData.email,
    password: formData.password,
    tipoDocumento: formData.tipoDocumento,
    numeroDocumento: formData.numeroDocumento,
    nombres: formData.nombres,
    apellidos: formData.apellidos,
    genero: formData.genero ?? null,
    telefono: formData.telefono ?? null,
    whatsapp: formData.whatsapp ?? null,
    emergencyName: formData.emergencyName ?? null,
    emergencyPhone: formData.emergencyPhone ?? null,
  });
  return data;
}

export async function getMe(): Promise<ApiResponse<User>> {
  const { data } = await api.get<ApiResponse<User>>("/api/auth/me");
  return data;
}

export async function logout(): Promise<ApiResponse<null>> {
  const { data } = await api.post<ApiResponse<null>>("/api/auth/logout", {});
  return data;
}
