import { readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const directory = new URL('./', import.meta.url);
// These suites serve source files and fixtures directly or start their own loopback server.
const offlineSuites = [
  'gallery-regressions.js',
  'locale-regressions.js',
  'local-engine-regressions.mjs',
  'local-workspace-regressions.mjs',
  'mcp-regressions.mjs',
  'polish-regressions.js',
  'pose-pair-regressions.js',
  'pose-picker-regressions.js',
  'provider-connection-regressions.js',
  'reference-regressions.js',
  'theme-regressions.js',
  'v16-proxy.mjs',
];
const suites = process.argv.includes('--offline') ? offlineSuites : readdirSync(directory)
  .filter(name => /^v\d+(?:-.*)?\.m?js$/.test(name) || /-regressions\.(?:m?js|cjs)$/.test(name)).sort();
const failed = [];
for (const suite of suites) {
  console.log('\n'+suite);
  const result = spawnSync(process.execPath, [fileURLToPath(new URL(suite, directory))], {stdio:'inherit'});
  if (result.status !== 0) failed.push(suite);
}
console.log(`\n${suites.length - failed.length} / ${suites.length} suites passed`);
if (failed.length) {
  console.error('Failed suites: '+failed.join(', '));
  process.exitCode = 1;
}
