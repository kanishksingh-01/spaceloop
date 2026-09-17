import { createClient } from "@supabase/supabase-js";
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || "https://wdpuojfsgvcfjyponnjg.supabase.co",
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""
);