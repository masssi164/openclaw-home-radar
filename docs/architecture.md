# Architecture and release boundary

## Product

Home Radar is a household-aware research assistant, not an update notifier. Its target is to connect developments across sources and time with an operator's enduring goals, actual capabilities and constraints. Sustainability, non-electronic solutions and robotics belong in scope when they serve those goals; the system is not limited to installed brands.

## Reuse the host

- **OpenClaw:** agent reasoning, configured model providers, memory access, tool authority, orchestration, scheduling and delivery.
- **JavaScript ESM / Node.js:** native plugin registration, validated tool boundaries and process integration.
- **Python standard library:** reusable deterministic collection and local evidence processing; no independent agent platform.
- **SQLite:** local evidence, provenance, revisions and research state. No external database service required.
- **JSON / JSON Schema:** portable user configuration, constraints, dossier structures and validated tool input.
- **RSS/Atom and HTTPS APIs:** broad news discovery plus primary-source verification signals. Search-provider access is replaceable; SearXNG and commercial APIs are infrastructure choices, not the reasoning engine.

The initial release is explicitly an alpha. Packaged tools and persistent research structures do not prove that an autonomous journalist delivers non-obvious useful findings. End-to-end evaluation and host integration must establish that separately.

## Separate code from private state

The repository and package contain logic, schemas, tests and synthetic examples. Runtime state belongs in a separately configured directory outside the installation checkout. User configuration is never embedded into a build or copied into package examples. Do not publish household inventory, personal goals, credentials, addresses, room IDs, prompts containing private context, collected articles or audio.

Credentials are supplied through the host's existing authorization mechanisms. Publication of source code is not authorization to upload user data. A private data directory is a separation mechanism, not encryption; local access controls, backups and device security remain operator responsibilities.

## Target research lifecycle

1. Maintain the actual household baseline and sourced, time-aware goals.
2. Collect news widely and preserve potentially useful weak signals.
3. Maintain a question dossier: goal → current limitation → enabling development → proposed new capability → local prerequisites.
4. Form a hypothesis from multiple independent evidence roles, not repeated coverage of one press release.
5. Investigate the strongest objection and existing simpler alternatives.
6. Publish only when there is useful information beyond an update dashboard, with a scoped, supported decision and an agent-owned next step.
7. Retain unresolved questions with ownership, evidence gaps and reconsideration triggers.

Structured data and publication gates help make this auditable; they do not create understanding or establish factual truth. Unknown facts remain unknown. A productive evaluation must include true positive opportunities, not merely correct rejections or silence.

## Optional adapters

Home Assistant supplies inventory/capabilities and, when configured, delivery. It is not a mandatory runtime dependency for the core. Speech is an output adapter, not a bundled voice/model or forced cloud service. Search adapters can vary. A graph database is optional and requires measured benefit over the initial relational baseline.

## Start and migration

Installing/loading the plugin must not silently start timers, load models, send messages, play audio or modify devices. Configure private state and explicitly enable desired host workflows. Existing personal deployments are migrated only after compatibility and end-to-end acceptance; publishing this alpha does not replace any running deployment.

## Acceptance

Validate packaging exclusion of private data, runtime-directory separation, tool schemas, fixed subprocess invocation, provenance persistence and synthetic-fixture tests. Then compare a dossier-driven investigator against article-level relevance under the same corpus, household snapshot and research budget. Count relevant new opportunities, evidence correctness, research work removed from the user, cost and recall. A successful collector or plugin import alone is not a successful journalist.
