import { createClient, type SupabaseClient } from '@supabase/supabase-js'

export const supabaseConfig = {
  url: process.env.NEXT_PUBLIC_SUPABASE_URL ?? '',
  anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? '',
}

let browserClient: SupabaseClient | null = null

export function getBrowserSupabaseClient(): SupabaseClient | null {
  if (!supabaseConfig.url || !supabaseConfig.anonKey) return null
  if (browserClient) return browserClient
  browserClient = createClient(supabaseConfig.url, supabaseConfig.anonKey)
  return browserClient
}
