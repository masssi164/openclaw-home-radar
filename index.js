import { definePluginEntry } from 'openclaw/plugin-sdk/plugin-entry';
import { registerTools } from './src/tools.js';
export default definePluginEntry({
  id: 'home-radar', name: 'Home Radar',
  description: 'Question-driven household research tools with private local state',
  register: registerTools,
});
