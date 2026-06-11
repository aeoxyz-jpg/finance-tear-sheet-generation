# finance tear-sheet generation — a design-risk spike

A head-to-head experiment, **not a product**. It builds seven different
implementations of *one task* — generate a company tear sheet from financial
data — and compares them on the **same frozen synthetic data** with the **same
models**. The deliverable is **evidence**: a comparison report (metrics +
LLM-as-judge quality + failure catalogue), not a banker tool.

The central question: **how much does orchestration design, and a deterministic
number "rail", change how often an LLM fabricates financial numbers?**

## Two variables under test

A factorial matrix holds everything else constant (synthetic data, provider
abstraction, schemas, validation gate, renderer, judge, response cache):

1. **Orchestration** — the seven designs below.
2. **Model / provider** — every design runs across multiple workers: Anthropic
   direct API (`claude-sonnet-4-6`) and six cloud-Ollama models
   (`glm-5.1`, `deepseek-v4-pro`, `gemini-3-flash-preview`, `minimax-m3`,
   `kimi-k2.6`, `qwen3.5:397b`).

Design comparisons are **within-model**; cross-model is a separate, secondary
observation — design metrics are never pooled across models. The judge is fixed
to Anthropic Sonnet regardless of worker, so quality scores stay comparable
(with a same-family judge-bias caveat recorded in the report).

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
model writes numbers, then a deterministic `number_check` detects and corrects
wrong ones.

## Headline findings

- **The hard rail collapses agentic number-fabrication to 0%** on Sonnet
  (28% → 0) and glm-5.1 (39% → 0), and on 5 of 7 models overall. It is a
  *structural × model-compliance* effect: models that leak inline numbers
  despite the placeholder instruction (deepseek, minimax) only partially drop.
- **The soft rail is model-dependent** — glm 39% → 6%, but Sonnet only 28% →
  20% (Sonnet re-fabricates persistently across correction rounds).
- **The hard rail does not fix prose hallucination** — `agentic_grounded` still
  shows the highest unsupported-claim count; constraining numeric *output*
  doesn't constrain interpretive *claims*.
- **Capability gating is itself a finding** — `tool_use` gates the agentic
  designs, structured output gates the placeholder designs. A model lacking a
  capability records `capability_unsupported` rather than crashing.

See [`docs/pipeline-architecture-and-learnings.md`](docs/pipeline-architecture-and-learnings.md)
for the full architecture, prompts, and empirical write-up.

## Setup

    uv venv && uv pip install -e ".[dev]"

## Test

    uv run pytest          # 369 offline tests; `live` tests deselected
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
common/             llm · schemas · validation · render · eval · number_check · telemetry
harness/            run → compare → report (per-model summary matrices + trace HTML)
results/            committed comparison reports + run manifests
docs/               specs, plans, and the architecture/learnings write-up
```

## Where to read next

- [`docs/pipeline-architecture-and-learnings.md`](docs/pipeline-architecture-and-learnings.md) — best entry point: the designs, the rail concept, the empirical learnings.
- [`docs/agentic-failure-mode-diagnostic.md`](docs/agentic-failure-mode-diagnostic.md) — trace-based evidence for *why* agentic fabricates.
- [`docs/superpowers/specs/2026-06-06-tearsheet-spike-design.md`](docs/superpowers/specs/2026-06-06-tearsheet-spike-design.md) — the authoritative consolidated spec.
- `results/*/report.md` — the generated comparison reports.

## License

MIT — see [`LICENSE`](LICENSE).
