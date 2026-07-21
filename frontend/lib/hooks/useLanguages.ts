"use client";

import { useQuery } from "@tanstack/react-query";
import { listLanguages } from "@/lib/api/languages";

export function useLanguages() {
  return useQuery({ queryKey: ["languages"], queryFn: listLanguages });
}
