import test from 'node:test';
import assert from 'node:assert/strict';
import {
  DEFAULT_PRODUCTION_API_ORIGIN,
  buildApiUrl,
  normalizeApiBaseUrl,
  resolveApiBaseUrl,
} from '../src/api-config.mjs';
import { verifyProductionBundle } from './verify-production-api.mjs';

test('missing production configuration resolves to the verified Render origin', () => {
  assert.equal(resolveApiBaseUrl(undefined, 'production'), DEFAULT_PRODUCTION_API_ORIGIN);
});

test('blank production configuration resolves to the verified Render origin', () => {
  assert.equal(resolveApiBaseUrl('   ', 'production'), DEFAULT_PRODUCTION_API_ORIGIN);
});

test('valid production override is preserved', () => {
  assert.equal(resolveApiBaseUrl('https://api.example.com', 'production'), 'https://api.example.com');
});

test('trailing slash and /api suffix are normalized away', () => {
  assert.equal(normalizeApiBaseUrl('https://api.example.com/api///', 'production'), 'https://api.example.com');
  assert.equal(normalizeApiBaseUrl('https://api.example.com///', 'production'), 'https://api.example.com');
});

test('analysis request URL includes the API path exactly once and preserves query parameters', () => {
  const url = buildApiUrl('https://quantnova-ai.onrender.com/api/', '/api/analyze?symbol=RELIANCE.NS&period=1y');
  assert.equal(url, 'https://quantnova-ai.onrender.com/api/analyze?symbol=RELIANCE.NS&period=1y');
});

test('production build verifier rejects a localhost API URL', () => {
  assert.throws(() => verifyProductionBundle(
    `${DEFAULT_PRODUCTION_API_ORIGIN}/api/analyze?symbol=RELIANCE.NS http://localhost:8000`,
  ), /localhost API fallback/);
});

test('production build verifier rejects a bundle missing the expected origin', () => {
  assert.throws(() => verifyProductionBundle('/api/analyze?symbol=RELIANCE.NS'), /Render origin is missing/);
});

test('invalid or blank override falls back; development keeps its local default', () => {
  assert.equal(resolveApiBaseUrl('not-a-url', 'production'), DEFAULT_PRODUCTION_API_ORIGIN);
  assert.equal(resolveApiBaseUrl('', 'development', 'http://localhost:8000'), 'http://localhost:8000');
  assert.equal(normalizeApiBaseUrl('http://localhost:8000', 'production'), '');
});
