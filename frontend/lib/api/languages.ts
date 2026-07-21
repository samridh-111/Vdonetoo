import type { Language } from "@/lib/types/language";
import { apiFetch } from "./client";

export async function listLanguages(): Promise<Language[]> {
  return apiFetch<Language[]>("/api/v1/languages");
}
