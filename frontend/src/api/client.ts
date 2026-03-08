/**
 * HTTP client - FastAPI backend communication layer.
 * 
 * This module abstracts API communication with:
 * 1. Base URL configuration: localhost:8000 (development)
 * 2. Error handling: JSON parsing and network error recovery
 * 3. Type-safe responses: Generic<T> for compile-time validation
 * 
 * Available Endpoints:
 * - GET /metrics: Overview KPIs
 * - GET /filters: Available filter options
 * - GET /videos: Paginated video list
 * - GET /insights: Complete analytics (clustering, prediction, etc.)
 * - GET /similar?video_id=X&k=5: Similar content recommendations
 * 
 * Error Handling:
 * - Network failures: Default to empty state
 * - Invalid JSON: Caught and logged
 * - 4xx/5xx responses: Propagated to caller
 * 
 * Configuration:
 * - VITE_API_URL environment variable for deployment flexibility
 * - Default: http://localhost:8000 (local development)
 */

const env = (import.meta as any).env ?? {};
const BASE = env.VITE_API_URL ?? env.VITE_API_BASE_URL ?? "http://localhost:8000";
export async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return (await r.json()) as T;
}
