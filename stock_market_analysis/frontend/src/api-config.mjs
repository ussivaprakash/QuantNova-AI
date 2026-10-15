export const DEFAULT_PRODUCTION_API_ORIGIN = 'https://quantnova-ai.onrender.com';

export function normalizeApiBaseUrl(value, mode = 'production') {
  if (typeof value !== 'string' || value.trim() === '') return '';

  try {
    const url = new URL(value.trim());
    const localDevelopmentHost = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
    const protocolAllowed = url.protocol === 'https:' || (mode !== 'production' && localDevelopmentHost && url.protocol === 'http:');
    if (!protocolAllowed || url.username || url.password || url.search || url.hash) return '';

    const path = url.pathname.replace(/\/+$/, '');
    if (path !== '' && path.toLowerCase() !== '/api') return '';
    return url.origin;
  } catch {
    return '';
  }
}

export function resolveApiBaseUrl(value, mode = 'production', developmentOrigin = '') {
  const normalized = normalizeApiBaseUrl(value, mode);
  if (normalized) return normalized;
  return mode === 'production' ? DEFAULT_PRODUCTION_API_ORIGIN : normalizeApiBaseUrl(developmentOrigin, mode);
}

export function buildApiUrl(baseUrl, path) {
  const normalizedBase = normalizeApiBaseUrl(baseUrl, 'development');
  if (!normalizedBase) throw new Error('Invalid analysis API base URL.');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}
