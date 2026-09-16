import type { z } from "zod";
import { UserSchema } from "./user.schema";

export const LoginResponseSchema = UserSchema;
export type LoginResponse = z.infer<typeof LoginResponseSchema>;

export const RegisterResponseSchema = UserSchema;
export type RegisterResponse = z.infer<typeof RegisterResponseSchema>;
