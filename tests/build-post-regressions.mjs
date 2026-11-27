import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const script = fileURLToPath(new URL('./build-post-regressions.py', import.meta.url));
const env = { ...process.env, PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8' };

const candidates = process.env.PYTHON
  ? [[process.env.PYTHON, []]]
  : process.platform === 'win32'
    ? [['python', []], ['py', ['-3']], ['python3', []]]
    : [['python3', []], ['python', []]];

let result;
for (const [cmd, prefix] of candidates) {
  result = spawnSync(cmd, [...prefix, script], { stdio: 'inherit', env });
  if (!result.error || result.error.code !== 'ENOENT') break;
}

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
