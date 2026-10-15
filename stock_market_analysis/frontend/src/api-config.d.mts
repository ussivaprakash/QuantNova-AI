export const DEFAULT_PRODUCTION_API_ORIGIN: string;
export function normalizeApiBaseUrl(value: unknown, mode?: string): string;
export function resolveApiBaseUrl(value: unknown, mode?: string, developmentOrigin?: string): string;
export function buildApiUrl(baseUrl: string, path: string): string;
