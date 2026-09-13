# Home Radar 0.2 — restart-safe question-driven research

Status: implemented alpha contract, 2026-09-13. Research quality remains subject to
live editorial evaluation; structural validation does not establish truth.

## Objective

Connect a public development to a household goal, prior obstacle, changed enabling
condition and practical consequence. Search can begin with an unresolved question
without a new article. Neither a feed digest nor an installed-software update list
satisfies this objective. Include accessibility, privacy, effort, sustainability,
robotics and non-electronic alternatives when relevant. Never manufacture novelty.

## Architecture decision

Retain the native OpenClaw host, Node ESM tool bridge, Python 3.10+ standard library
and one private SQLite evidence database. Do not add LangChain, LangGraph, a cloud
vector store, queue service or graph database before measured need. The original
alpha extracted the deterministic collector from a private Python application;
it is not based on an external RSS aggregator package. Feedparser is a useful
HTTP/feed reference, not an installed dependency. OpenClaw supplies the configured
model, search tools, memory, scheduling and channel adapters. The package neither
selects a model nor launches its own AI runtime.

The host owns reasoning; the core owns accounting. Feed text, imported context and
model output remain data, not execution authority. No automatic purchases,
installation, credentials in feeds or household configuration in the npm package.

## Implemented pipeline

1. **Collect:** configured RSS/Atom, GitHub releases and Hugging Face metadata;
   retain content revisions and source provenance. Ignore HTML layout IDs in revision
   fingerprints while retaining substantive text, links and prices; aliases preserve
   pre-upgrade evidence IDs and sighting history. Conditional ETag/Last-Modified
   requests; 304 is unchanged, not broken XML. Serialize requests per hostname.
   HTTP errors schedule deferred retry with exponential delay, Retry-After and
   GitHub rate-reset support. No sleeping retry loop. Validators commit only after
   successful parse and persistence. Continue with healthy sources and expose
   degraded status. Authentication remains outside this public-source collector.
2. **Start/resume:** `radar_newsroom action=start` atomically snapshots all
   not-yet-triaged item IDs. At most one active run per runtime. Concurrent new
   evidence belongs to the next run; a new invocation resumes an unfinished one.
3. **Triage:** `batch` pages 1–50 pending items; `assess` accepts explicit semantic
   relevance, reason and context links. No automatic keyword classification.
   Each committed batch survives restart. A profile-content change on the next
   run reopens archived evidence. Fresh telemetry should be kept outside the
   stable profile to avoid needless full re-triage.
4. **Investigate:** host reads question dossiers even with zero new items. Public
   queries use minimal generic context. Compare decisive primary evidence against
   live household capabilities; record counterevidence, simpler alternatives,
   unknowns and reconsideration triggers. Upsert dossiers preserving prior evidence.
5. **Editorial gate:** host verifies factual support and household benefit; core
   requires full snapshot triage before `finish`. Store a canonical report or an
   explicit internal `no_findings` reason. This is an accounting gate, not an
   automated fact checker. No-findings is a successful, intentionally silent run.
6. **Delivery:** persist report, SHA-256 and semantic material key, then `dispatch`
   BEFORE host I/O. Matrix and audio receipts are independent. Only an actual
   Matrix receipt confirms delivered. Unknown delivery remains pending and blocks
   blind replay. A proven failed delivery can return to ready. The host must
   reconcile scheduler history/Matrix receipts before retry. Silence, failure and
   pending delivery are distinct. Audio never blocks text.

## Host workflow and budget

Suggested baseline: collect every 30 minutes, editorial once daily in the user's
local timezone. This is operator configuration, not an installation side effect.
Use batches of 25; maximum 50. Triage every snapshot item, with deeper investigation
of at most three strongest questions per edition. Start with up to twelve public
search queries, reserving two for counterevidence. If decisive evidence is absent,
retain the question with next acquisition step; do not ask the user to do research.
Budgets guide host orchestration; they are not hard model-usage enforcement.
Time exhaustion checkpoints progress, never labels partial coverage complete.

Scheduler prompts should reference the repository workflow and private adapter
contract. No frozen tool list; inherit host capability policy. Alert the operator
after the first editorial error. A long running gateway task must not be started
before a required gateway restart. Restart recovery resumes research; uncertain
external delivery requires receipt reconciliation rather than automatic resend.

## Evidence and source coverage

Discovery publishers are not independent confirmation of claims they copied from
one press release. Primary release feeds can establish a version or feature, not
that the household experienced a bug. Model listings are not runnable-fit proof.
Use exact documentation/model cards, measured local baselines where appropriate,
and separate publication time from retrieval time. Feed coverage is configurable;
search beyond feeds is essential for sustainability and other undercovered goals.

Use a stable goal ID -> obstacle -> new evidence -> capability -> prerequisites
chain. Track observed/user-stated/inferred/external-claim/tested provenance. A stale
baseline is not silently upgraded to current fact. Private paths and inventory
never enter public search queries or the shared report.

## State and compatibility

One runtime database contains items, reviews, triage, dossiers, source health,
HTTP cache, run snapshots and channel receipts. The original alpha preview remains
available but must not be treated as all-evidence coverage. Existing private adapters
can continue to supply inventory and speech; they do not own another collector.
Migration uses SQLite backup API and idempotent row import; old databases remain
archived, not deleted. No automatic schema downgrade. SQLite busy timeout is 30s;
WAL is deliberately not forced for portable/network filesystem installations.

## Acceptance and limits

Automated regression cases: resume after process boundary, incomplete coverage
cannot finish, profile changes revisit archives, invalid assessments are atomic,
304 caching, malformed XML cannot poison validators, persistent rate-limit deferral,
independent audio/text receipt states, uncertain send cannot replay, material-key
duplicate suppression, fixed subprocess invocation, private package boundary.
Live acceptance separately checks collection, a question investigation, saved
report and actual Matrix receipt. A text-send receipt is not proof of human reading;
audio service acceptance is not proof of audibility. A single live run is not a
longitudinal relevance benchmark.

Still evaluation/backlog, not shipped guarantees: learned semantic event clustering,
feedback-trained ranking, automatic baseline synchronization, automatic receipt
reconciler, hard search-budget enforcement, source diversity metrics, labelled
opportunity-recall benchmark. The host supplies these manual/agent decisions today.
Core receipts are assertions supplied by authorized host tools, not independently
verified network receipts. No exactly-once claim across SQLite and Matrix.

## Research basis (primary sources checked 2026-09-13)

- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents): composable workflows and explicit gates inform the host/core split.
- [Feedparser: HTTP validators](https://feedparser.readthedocs.io/en/stable/http-etag.html): conditional retrieval informs our standard-library implementation.
- [GitHub REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api): per-host serialization and deferred rate-limit retries; unauthenticated 304 is not advertised as free quota.
- [OpenClaw delivery](https://docs.openclaw.ai/automation/cron-jobs/delivery): separate execution, completion and delivery; native failure alerts.
- [SQLite transactions](https://www.sqlite.org/lang_transaction.html): short database transactions, serialized writes and durable run snapshots.

These are design inputs, not evidence that this application's editorial quality
has already been independently demonstrated.
