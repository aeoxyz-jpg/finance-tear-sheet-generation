# finance tear-sheet generation — a design-risk spike

A head-to-head experiment, **not a product**. It builds seven different
implementations of *one task* — generate a company tear sheet from financial
data — and compares them on the **same frozen synthetic data** with the **same
models**. The deliverable is **evidence**: a comparison report (metrics +
LLM-as-judge quality + failure catalogue), not a banker tool.

The central question: **how much do orchestration design and a deterministic
number "rail" change whether you can trust the numbers an LLM puts in a
financial document?**

> **Note:** this spike's original headline finding ("agentic designs fabricate
> 24–39% of their inline numbers") was later found to be a measurement artifact
> and corrected. The findings below are the corrected ones; the full story is in
> [Correction & revision history](#correction--revision-history) at the bottom.

## Two variables under test

A factorial matrix holds everything else constant (synthetic data, provider
abstraction, schemas, validation gate, renderer, judge, response cache):

1. **Orchestration** — the seven designs below.
2. **Model / provider** — every design runs across multiple workers: Anthropic
   direct API (`claude-sonnet-4-6`) and six cloud-Ollama models
   (`glm-5.1`, `deepseek-v4-pro`, `gemini-3-flash-preview`, `minimax-m3`,
   `kimi-k2.6`, `qwen3.5:397b`).

Design comparisons are **within-model**; cross-model is a separate, secondary
observation, and design metrics are never pooled across models. The judge is
fixed to Anthropic Sonnet regardless of worker, so quality scores stay
comparable (with a same-family judge-bias caveat recorded in the report).

## The seven designs

| Design | One LLM call? | Number rail | Role |
|--------|---------------|-------------|------|
| `single_shot` | yes | none *(deliberate)* | control — writes numbers inline |
| `prompt_chaining` | 2 (plan + narrative) | hard (placeholder slot-filling) | grounded baseline |
| `reflection` | chaining + critic/revise loop | hard | evaluator-optimizer on top of chaining |
| `agentic` | single tool-use agent loop | none | LLM orchestrates end-to-end |
| `agentic_grounded` | agent loop | hard | agentic + placeholder rail |
| `agentic_verified` | agent loop | soft (detect + correct) | agentic + deterministic `number_check` fix loop |
| `agentic_reflection` | agent loop + critic/revise | hard | agentic gather + rail + reflection |

`single_shot` / `prompt_chaining` / `agentic` / `agentic_grounded` fill the four
corners of a 2×2 (orchestration {deterministic, agentic} × rail {none, hard}).

**Hard rail** = the model emits `{{placeholder}}` tokens only; real numbers are
substituted deterministically from ground truth afterward, and a hallucinated
placeholder name is **rejected** (never fuzzy-corrected). **Soft rail** = the
model writes numbers, then a deterministic `number_check` flags mismatches and
the model is asked to fix them.

## Headline findings (as corrected, 2026-07-07)

- **The hard rail's real value is verifiability by construction.** With the
  model forbidden from writing a digit, every number in the final document is
  substituted from the source contract and machine-checkable against it. Five
  of seven models emit zero inline digits under the rail; `deepseek-v4-pro`
  and `minimax-m3` still leak some (a *placeholder-discipline* violation, not a
  wrongness rate) — the rail is a *structural × model-compliance* effect.
- **Inline numbers go wrong in two genuine ways, and the rail removes both.**
  `single_shot` gets 4–8% of its inline numbers genuinely wrong (transcription
  errors, control-validated: its flagged tokens match nothing in the source).
  And models echoing raw millions-denominated values mislabel magnitudes,
  writing `$28,000` where $28.0B is meant — real data, wrong scale label.
- **A corrective loop inherits its checker's blind spots, including its false
  positives.** The soft rail's improvements (glm 39% → 6% flagged; Sonnet only
  28% → 20%) turned out to measure the model converging on the checker's
  literal digit vocabulary, because the checker was flagging correct numbers
  that sat outside its grading pool.
- **The rail constrains numbers, not prose.** Unsupported causal editorializing
  ("signaling strong deleveraging") passes through untouched; prose grounding
  needs its own instrument. (The spike's per-design grounding *comparison* is
  confounded for tool-using designs — see the correction below — so it is not
  cited as a ranking here.)
- **Capability gating is itself a finding** — `tool_use` gates the agentic
  designs, structured output gates the placeholder designs. A model lacking a
  capability records `capability_unsupported` rather than crashing.

## Also here: two production pipelines (`pipelines/`)

A separate production-oriented track built on the spike's lessons, sharing one
output contract (code renders every numeric table; the LLM writes four
placeholder-disciplined prose slots), one deterministic check battery, and one
composite score. The only variable between the two pipelines is who
orchestrates: a fixed workflow with targeted repair, or an agent with tools.
Their evaluation runs (dev + one-shot holdout) are not committed here; the
methodology and results are written up in the accompanying article series.

## Setup

    uv venv && uv pip install -e ".[dev]"

## Test

    uv run pytest          # 413 offline tests; `live` tests deselected
    uv run pytest -m live  # live provider/judge tests (needs API keys)

API keys are read from the macOS Keychain at runtime (services
`anthropic-api-key` / `ollama-api-key`) or the env-var fallbacks
`ANTHROPIC_API_KEY` / `OLLAMA_API_KEY` — never from files, never logged.
`temperature=0` everywhere; reproducibility comes from a VCR-style response
cache (`common/cache.py`), not from byte-identical API output.

## Layout

```
fixtures/*.json     synthetic frozen data — 12 cases, each tuned to one edge case
fakedata/           single source of truth: FastAPI REST + MCP stdio server
designs/            the seven orchestrations (the variable under test)
pipelines/          the production track: workflow + agentic pipelines, checks, scoring
common/             llm · schemas · validation · render · eval · number_check · telemetry
harness/            run → compare → report (per-model summary matrices + trace HTML)
results/            committed comparison reports, run manifests, and the correction record
```

## Where to read next

- `results/*/report.md` — the generated comparison reports (each carries a
  correction banner; tables are raw benchmark output).
- [`results/CORRECTION-2026-07-07-grading-scope-artifact.md`](results/CORRECTION-2026-07-07-grading-scope-artifact.md)
  — the correction record: what the re-audit found, the re-measurement table,
  and what still stands.
- `pipelines/` — the production track's code: shared checks
  (`pipelines/checks.py`), coverage with a dynamic denominator
  (`pipelines/coverage.py`), and the composite score (`pipelines/scoring.py`).

## Correction & revision history

**2026-07-07 — the original headline finding was wrong, and here is exactly
how.** This spike shipped for a month claiming that unguarded agentic designs
*fabricate* 24–39% of their inline numbers, anchored on two vivid examples: an
agent that "invented a five-year revenue history" for a private company, and
one that "narrated transactions that don't exist" for a company with none.

A pre-publication claims audit of a write-up re-verified those examples against
the raw model traces instead of the intermediate reports — and found the
"invented" numbers sitting verbatim inside the tool outputs the agent had
legitimately retrieved. Re-classifying every flagged token across all seven
models (832 tokens, with a no-tools control and cross-company null tests) put
the genuine fabrication rate at approximately 0%. The mechanism: `number_check`
and the judge grade every design against a narrow 15-field payload, while the
agentic designs' tools return the full fixture — so real, correctly-cited data
was scored "incorrect" for sitting outside the grading vocabulary. The
"invented transactions" example dissolved the same way: the model had written
"No recent M&A transactions on record.", which is correct, and the keyword
scan that "confirmed" the invention was mostly matching the company's own name
(NoTransaction Software Corp.).

What this changes and what it doesn't: the rail still wins, for the corrected
reasons above (verifiability, plus eliminating the two genuine error classes).
The affected `results/*/report.md` tables are annotated rather than
regenerated, because the honest fix (grading each design against the data it
was actually allowed to see) requires a paid re-run. Full record:
[`results/CORRECTION-2026-07-07-grading-scope-artifact.md`](results/CORRECTION-2026-07-07-grading-scope-artifact.md).

The uncomfortable part is *why* it survived a month: four internal documents
and two published posts each verified against the summary above them, and
nobody re-read the transcripts. The project's own first lesson — trace
everything, and read the traces, not the dashboards — is what finally caught
it, one write-up too late. It is recorded here rather than silently rewritten
because a benchmark that corrects itself in public is worth more than one that
was never wrong.

## License

MIT — see [`LICENSE`](LICENSE).
