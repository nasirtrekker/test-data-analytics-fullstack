const env = (import.meta as any).env ?? {};
const BASE = env.VITE_API_URL ?? env.VITE_API_BASE_URL ?? "http://localhost:8000";
export async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return (await r.json()) as T;
}
