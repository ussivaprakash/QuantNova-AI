import { readdir, readFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { resolveApiBaseUrl } from '../src/api-config.mjs';

export function verifyProductionBundle(bundle, expectedOrigin = resolveApiBaseUrl(undefined, 'production')) {
  if (!bundle.includes(expectedOrigin)) {
    throw new Error('Production API verification failed: expected Render origin is missing from the built bundle.');
  }
  if (!bundle.includes('/api/analyze?symbol=')) {
    throw new Error('Production API verification failed: the analysis API path is missing from the built bundle.');
  }
  if (bundle.includes('http://localhost:8000')) {
    throw new Error('Production API verification failed: the production bundle contains the localhost API fallback.');
  }
}

async function verifyBuiltAssets() {
  const assetsDirectory = join(process.cwd(), 'dist', 'assets');
  const assetNames = await readdir(assetsDirectory);
  const jsFiles = assetNames.filter((name) => name.endsWith('.js'));
  if (jsFiles.length === 0) {
    throw new Error('Production API verification failed: no JavaScript bundles were produced.');
  }

  const bundle = (await Promise.all(jsFiles.map((name) => readFile(join(assetsDirectory, name), 'utf8')))).join('\n');
  const expectedOrigin = resolveApiBaseUrl(process.env.VITE_API_BASE_URL, 'production');
  verifyProductionBundle(bundle, expectedOrigin);
  console.log('Production API bundle verified: Render origin present; analysis route present; localhost absent.');
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await verifyBuiltAssets();
}
