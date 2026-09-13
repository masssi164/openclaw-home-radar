import { spawn } from 'node:child_process';
import { isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';

const script = fileURLToPath(new URL('../core/cli.py', import.meta.url));
const commands = new Set(['status', 'collect', 'prepare', 'dossier']);

export function invoke(config, command, params = {}) {
  if (!commands.has(command)) throw new Error('Unsupported command');
  if (typeof config.dataRoot !== 'string' || !isAbsolute(config.dataRoot)) throw new Error('Configure absolute private dataRoot');
  const body = JSON.stringify(params);
  if (Buffer.byteLength(body) > 128 * 1024) throw new Error('Input too large');
  return new Promise((resolve, reject) => {
    const child = spawn(config.pythonPath || 'python3', [script, '--root', config.dataRoot, command],
      { shell: false, stdio: ['pipe', 'pipe', 'pipe'] });
    let output = ''; let failure;
    const timer = setTimeout(() => { failure = new Error('Radar operation timed out'); child.kill('SIGKILL'); }, 120000);
    child.stdout.on('data', chunk => {
      output += chunk.toString();
      if (Buffer.byteLength(output) > 4 * 1024 * 1024) { failure = new Error('Radar output too large'); child.kill('SIGKILL'); }
    });
    child.stderr.resume(); // Never echo stderr: upstream/config errors can contain private values.
    child.stdin.on('error', () => {});
    child.on('error', () => { clearTimeout(timer); reject(new Error('Could not start configured Python interpreter')); });
    child.on('close', code => {
      clearTimeout(timer);
      if (failure || code !== 0) return reject(failure || new Error('Radar operation failed; check local config and inputs'));
      try { resolve(JSON.parse(output)); } catch { reject(new Error('Invalid core output')); }
    });
    child.stdin.end(body);
  });
}

const empty = { type: 'object', properties: {}, additionalProperties: false };
export function registerTools(api) {
  const config = { ...api.pluginConfig };
  const specs = [
    ['radar_status', 'status', 'Read local evidence collection and dossier health.', empty],
    ['radar_collect', 'collect', 'Fetch operator-configured public feeds into private SQLite; does not judge or publish news.', empty],
    ['radar_prepare', 'prepare', 'Prepare private household questions, dossiers and evidence for host-agent research. This alone does not perform the research.', { type: 'object', properties: { limit: { type: 'integer', minimum: 1, maximum: 50 } }, additionalProperties: false }],
    ['radar_dossier', 'dossier', 'List or persist research dossiers with explicit evidence provenance. Never grants permission to act.', { type: 'object', properties: { action: { type: 'string', enum: ['list', 'upsert'] }, document: { type: 'object', additionalProperties: true } }, required: ['action'], additionalProperties: false }],
  ];
  for (const [name, command, description, parameters] of specs) {
    api.registerTool({ name, description, parameters, async execute(_id, params) {
      const details = await invoke(config, command, params);
      return { content: [{ type: 'text', text: JSON.stringify(details) }], details };
    } }, { name, optional: true });
  }
}
