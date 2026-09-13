# Home Radar for OpenClaw

**0.1.0-alpha.1 — working research tools, not a finished autonomous journalist.**

Turn public developments into investigations of household needs, using private
local context. The host OpenClaw agent does the reasoning and web research; this
plugin supplies evidence collection, question-based dossiers and a research
contract. It does not call a separate paid model API or run its own AI service.

## What works

- Native OpenClaw plugin with optional `radar_status`, `radar_collect`,
  `radar_prepare` and `radar_dossier` tools.
- RSS/Atom news feeds, GitHub releases and Hugging Face metadata collection.
- SQLite evidence revision deduplication, source health and provenance.
- Persistent household research questions with evidence, unknowns and next searches.
- Preparation of a bounded context bundle plus a question-driven research contract.
- Separate private runtime data; no household data or delivery endpoints in this repository.

## Technology

Node.js ESM and the native OpenClaw `definePluginEntry` / `registerTool` API wrap a
Python 3.10+ standard-library core (SQLite, urllib, XML, JSON). No build framework,
cloud database, mandatory graph database, frontend or additional daemon.

Tested against **OpenClaw 2026.9.4**. The alpha pins that host peer version because
the plugin API is evolving. Node follows the host's supported engines:
24.16+ within 24.x, or 26.1+. SDK registration was checked against the installed
host without installing the plugin into the live gateway.

## Start locally

1. Choose a private absolute directory **outside this checkout**, e.g.
   `/srv/private/home-radar`. Restrict access to its owning account.
2. Create `config/` there. Copy `examples/profile.json` to `config/profile.json`
   and `examples/sources.json` to `config/sources.json`.
3. Populate these privately. The only sample feed is a disabled placeholder,
   not a working source subscription. Supply actual HTTPS news-feed URLs and
   distinguish `news_discovery` from `primary_release` sources. Nothing is fetched
   until you explicitly collect.
4. Install this local plugin using the host's `openclaw plugins install` command
   with this checkout path, then enable/configure `home-radar` following the
   host's plugin workflow. This README does not change your gateway itself.

Example entry inside your **private OpenClaw configuration**:

```json
{
  "plugins": {
    "entries": {
      "home-radar": {
        "enabled": true,
        "config": {
          "dataRoot": "/srv/private/home-radar",
          "pythonPath": "python3"
        }
      }
    }
  },
  "tools": { "allow": ["home-radar"] }
}
```

Merge with your existing allowlist rather than replacing unrelated entries.
A configured Python executable is operator-controlled; tool calls cannot choose
commands, executable paths, file paths, destinations or shell snippets.

Call `radar_collect`, then `radar_prepare`. Have your agent follow
[the research workflow](docs/workflow.md), researching meaningful questions rather
than generating release summaries. Store results with `radar_dossier`.
The tools are optional and registration creates no state, timer or network activity.

Standalone core smoke test (explicit root required):

```sh
python3 core/cli.py --root /srv/private/home-radar status < /dev/null
```

## Private context and provenance

`profile.json` contains your own assets, needs, constraints and priorities. Use
records with IDs, observed timestamps, source references and a distinction between
facts, user statements and inference. Empty arrays mean unknown, not that a
household has no needs. Do not reconstruct missing purpose as fact.

`data/radar.sqlite` contains public-source evidence and private dossiers together.
Treat the whole runtime directory as private. Sending `radar_prepare` to an
external model sends its included household context to that configured provider;
local storage alone does **not** make the entire workflow local. Minimize context
and select an appropriate host model. Search queries must not leak private names,
addresses, endpoints or household identifiers.

Only fetch public feeds you trust to configure. Feed text remains untrusted data;
never follow embedded instructions. This is not a network sandbox for arbitrary
untrusted source URLs. No credentials are required or supported in feed URLs.

## Research dossier

See [the schema](schemas/dossier.schema.json). `radar_dossier` accepts:

```json
{
  "action": "upsert",
  "document": {
    "id": "local-speech-latency",
    "question": "Can local speech now meet the household's response-time target?",
    "goal": "Useful private voice assistance",
    "constraints": ["Reuse existing hardware"],
    "unknowns": ["Measured latency on the actual device"],
    "next_searches": ["Primary runtime documentation and reproducible latency tests"],
    "evidence": [],
    "decision": "investigate"
  }
}
```

Evidence records require `claim`, `source`, `observed_at`, and `basis` (observed,
user-stated, inferred, external-claim, or tested). A proposal requires evidence and
an explicit reason; this structural gate is not proof that a claim is true.
Dossier listing currently returns at most 100 latest records.

## Deliberately not implemented yet

- Automatic household inventory, dependency graph and profile synchronisation.
- Autonomous scheduled multi-step newsroom, semantic cross-source discovery,
  model evaluation, reviewer arbitration and feedback learning.
- Brave/SearXNG adapters or automatic search-budget management.
- Home Assistant, chat and speech adapters; these belong in separately configured
  host integration. No household-specific inventory or audio code was copied.
- Any installation, purchase, device actuation, model replacement or migration.

The host can orchestrate the existing tools, but that must not be mistaken for
an already verified end-to-end autonomous service. A future schedule should call
that orchestration only after its behaviour and delivery routes are tested.

## Verification and packaging

```sh
npm test
npm pack --dry-run --json
```

Tests use synthetic fixtures and temporary directories, no live devices or API
keys. The package `files` allowlist excludes runtime data and tests from the npm
artifact; `.gitignore` excludes common state files. Review both the package and
Git tracking before sharing. Never publish a private project's history.

Official host references: [building plugins](https://docs.openclaw.ai/plugins/building-plugins),
[manifest](https://docs.openclaw.ai/plugins/manifest),
[entry helper](https://docs.openclaw.ai/plugins/sdk-entrypoints/define-plugin-entry).
