import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || "",
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "",
);

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
