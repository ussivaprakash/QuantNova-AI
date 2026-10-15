import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';

const expectedOrigin = 'https://quantnova-ai.onrender.com';
const assetsDirectory = join(process.cwd(), 'dist', 'assets');
const assetNames = await readdir(assetsDirectory);
const jsFiles = assetNames.filter((name) => name.endsWith('.js'));

if (jsFiles.length === 0) {
  throw new Error('Production API verification failed: no JavaScript bundles were produced.');
}

const bundle = (await Promise.all(jsFiles.map((name) => readFile(join(assetsDirectory, name), 'utf8')))).join('\n');
if (!bundle.includes(expectedOrigin)) {
  throw new Error('Production API verification failed: expected Render origin is missing from the built bundle.');
}
if (!bundle.includes('/api/analyze?symbol=')) {
  throw new Error('Production API verification failed: the analysis API path is missing from the built bundle.');
}
if (bundle.includes('http://localhost:8000')) {
  throw new Error('Production API verification failed: the production bundle contains the localhost API fallback.');
}

console.log('Production API bundle verified: Render origin present; localhost API fallback absent.');
