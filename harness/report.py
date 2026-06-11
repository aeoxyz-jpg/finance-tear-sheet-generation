# harness/report.py
"""Aggregate RunResults into a markdown comparison report (one matrix per worker model)."""
from __future__ import annotations
from harness.metrics import summarize_run, aggregate

_DESIGN_ORDER = ["single_shot", "prompt_chaining", "reflection", "agentic",
                 "agentic_grounded", "agentic_verified", "agentic_reflection"]

_READING_NOTES = (
    "**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own "
    "metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** "
    "(a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not "
    "the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the "
    "narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. "
    "**Whether that happens is model behavior, not structural:** the cross-model run shows it directly "
    "— Sonnet prompt_chaining cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 "
    "prompt_chaining omits them and stays on subject-company placeholders (→ 100%, verified to be full "
    "narratives, not degenerate brevity). The cap is contingent on the model interacting with the "
    "vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) "
    "leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend "
    "the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._\n\n"
    "**Reading `latency_ms`:** the mean is over FRESHLY-TIMED cells only (cache-replayed cells contribute "
    "latency 0 and are excluded so they cannot dilute it); `(n=k)` is how many of the design's cells were "
    "live-timed. A row whose `n` is below the design's cell count was timed on a subset (the rest replayed "
    "from cache) — compare latency only between rows with comparable `n`, ideally one fully-live (`--refresh`) "
    "run where every row's `n` equals the full cell count."
)

_AGENTIC_FAILURE_NOTE = (
    "## Why agentic underperforms (failure-mode analysis)\n\n"
    "agentic's high incorrect-rate / grounding_C / unsupported in the matrix above are **not a weaker "
    "model** — it is the *same* worker model as prompt_chaining. The gap is purely orchestration, and it "
    "traces to three compounding mechanisms (observed in the Anthropic run; PRIV is illustrative):\n\n"
    "1. **No placeholder rail (structural).** prompt_chaining/reflection are forced to write every figure "
    "as a `{{field_id}}` token drawn from the 15 subject fields that *exist*; the renderer substitutes "
    "real values, so the model's hands never touch a digit and it **physically cannot reference data "
    "the payload lacks**. agentic writes figures inline — every number passes through the model's "
    "working memory with no constraint blocking fabrication.\n"
    "2. **Format-completion pressure → fabrication.** Told to produce a *complete* tear sheet, agentic "
    "reproduces the canonical banker layout (multi-year history, full comps) and fills the cells with "
    "invented data when the payload is point-in-time. On PRIV (LTM-only payload) it fabricated a 5-year "
    "revenue history `$180M→$310M` where only the `$325M` LTM column is real (~28 invented figures), and "
    "invented market caps (`$850M`, `$1,100M`) for comparables whose table carries no market-cap field — "
    "despite the prompt's explicit \"never invent numbers.\"\n"
    "3. **Editorial autonomy → unsupported causal/directionality.** Free prose lets it assert causes the "
    "data never supports (\"signaling strong deleveraging\", \"reflecting improving operational "
    "efficiency\", \"signals an inorganic growth strategy\") — these feed grounding_C and unsupported.\n\n"
    "prompt_chaining, constrained to placeholders, scored incorrect=0 on the same company. **The placeholder "
    "vocabulary acts as a hard anti-fabrication rail; the agentic cost (27% vs 3% incorrect, grounding_C "
    "10.7 vs 2.0) is what removing that rail buys.** That is the spike's headline design-risk finding."
)


def _fmt(x, pct=False):
    if x is None:
        return "—"
    if pct:
        return f"{x * 100:.0f}%"
    return f"{x:.1f}" if isinstance(x, float) else str(x)


def _matrix_table(model: str, agg: dict) -> str:
    head = ("| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | "
            "incorrect_rate | grounding_C | unsupported | plan_valid | iters |")
    sep = "|" + "---|" * 13
    rows = [head, sep]
    for d in _DESIGN_ORDER:
        r = agg.get((model, d))
        if r is None:
            continue
        if r["capability_unsupported"]:
            rows.append(f"| {d} | — | — | _capability_unsupported_ |" + " |" * 9)
            continue
        rows.append(f"| {d} | {r['n']} | {_fmt(r.get('n_error', 0))} | {_fmt(r['calls'])} | {_fmt(r['input_tokens'])} | "
                    f"{_fmt(r['output_tokens'])} | {_fmt(r['latency_ms'])} (n={r.get('latency_timed_n', 0)}) | "
                    f"{_fmt(r['validation_pass_rate'], pct=True)} | "
                    f"{_fmt(r['pooled_incorrect_rate'], pct=True)} | "
                    f"{_fmt(r['grounding_c'])} | {_fmt(r['unsupported_claims'])} | "
                    f"{_fmt(r['plan_valid_rate'], pct=True)} | {_fmt(r['mean_iterations'])} |")
    return "\n".join(rows)


def _within_model_comparisons(model: str, agg: dict) -> str:
    ss, cons = agg.get((model, "single_shot")), agg.get((model, "prompt_chaining"))
    refl, agen = agg.get((model, "reflection")), agg.get((model, "agentic"))
    lines = ["**Within-model comparisons** (valid only within a fixed model):"]

    def ok(r):
        return r is not None and not r["capability_unsupported"]

    if ok(ss) and ok(cons):
        delta = ss["pooled_incorrect_rate"] - cons["pooled_incorrect_rate"]
        lines.append(f"1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): "
                     f"inline-number incorrect-rate {_fmt(ss['pooled_incorrect_rate'], pct=True)} vs "
                     f"{_fmt(cons['pooled_incorrect_rate'], pct=True)} → Δ {_fmt(delta, pct=True)}.")
    if ok(cons) and ok(refl):
        d_unsup = refl["unsupported_claims"] - cons["unsupported_claims"]
        d_calls = refl["calls"] - cons["calls"]
        conv = refl.get("converged_rate")
        conv_note = (f" converged early in {_fmt(conv, pct=True)} of runs"
                     if conv is not None else "")
        lines.append(f"2. **prompt_chaining vs reflection** (does reflection earn its cost): "
                     f"Δ unsupported-claims {_fmt(d_unsup)} for Δ calls {_fmt(d_calls)} "
                     f"(mean iterations {_fmt(refl['mean_iterations'])};{conv_note or ' convergence n/a'}).")
    if ok(cons) and ok(agen):
        lines.append(f"3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): "
                     f"incorrect-rate {_fmt(cons['pooled_incorrect_rate'], pct=True)} vs "
                     f"{_fmt(agen['pooled_incorrect_rate'], pct=True)}; calls {_fmt(cons['calls'])} vs "
                     f"{_fmt(agen['calls'])}; valid-pass {_fmt(cons['validation_pass_rate'], pct=True)} vs "
                     f"{_fmt(agen['validation_pass_rate'], pct=True)}.")
    ag, agg_, agv = agg.get((model, "agentic")), agg.get((model, "agentic_grounded")), agg.get((model, "agentic_verified"))
    pc = agg.get((model, "prompt_chaining"))
    if ok(ag) and ok(agg_):
        d = ag["pooled_incorrect_rate"] - agg_["pooled_incorrect_rate"]
        lines.append(f"4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): "
                     f"incorrect-rate {_fmt(ag['pooled_incorrect_rate'], pct=True)} vs "
                     f"{_fmt(agg_['pooled_incorrect_rate'], pct=True)} → Δ {_fmt(d, pct=True)}.")
    if ok(ag) and ok(agv):
        d = ag["pooled_incorrect_rate"] - agv["pooled_incorrect_rate"]
        lines.append(f"5. **agentic vs agentic_verified** (what soft number_check correction buys): "
                     f"incorrect-rate {_fmt(ag['pooled_incorrect_rate'], pct=True)} vs "
                     f"{_fmt(agv['pooled_incorrect_rate'], pct=True)} → Δ {_fmt(d, pct=True)}; "
                     f"calls {_fmt(ag['calls'])} vs {_fmt(agv['calls'])}.")
    if ok(pc) and ok(agg_):
        lines.append(f"6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): "
                     f"incorrect-rate {_fmt(pc['pooled_incorrect_rate'], pct=True)} vs "
                     f"{_fmt(agg_['pooled_incorrect_rate'], pct=True)}.")
    ar = agg.get((model, "agentic_reflection"))
    if ok(agg_) and ok(ar):
        d = agg_["unsupported_claims"] - ar["unsupported_claims"]
        lines.append(f"7. **agentic_grounded vs agentic_reflection** (reflection on the agentic row): "
                     f"unsupported {_fmt(agg_['unsupported_claims'])} vs {_fmt(ar['unsupported_claims'])} "
                     f"→ Δ {_fmt(d)}; calls {_fmt(agg_['calls'])} vs {_fmt(ar['calls'])}.")
    if ok(ss) and ok(ag):
        lines.append(f"8. **single_shot vs agentic** (orchestration at no-gate): "
                     f"incorrect-rate {_fmt(ss['pooled_incorrect_rate'], pct=True)} vs "
                     f"{_fmt(ag['pooled_incorrect_rate'], pct=True)}.")
    if ok(refl) and ok(ar):
        lines.append(f"9. **reflection vs agentic_reflection** (orchestration at full-stack): "
                     f"incorrect-rate {_fmt(refl['pooled_incorrect_rate'], pct=True)} vs "
                     f"{_fmt(ar['pooled_incorrect_rate'], pct=True)}; unsupported "
                     f"{_fmt(refl['unsupported_claims'])} vs {_fmt(ar['unsupported_claims'])}.")
    return "\n".join(lines)


def _capability_section(summaries: list[dict]) -> str:
    gated = {(s["worker_model"], s["design"], s.get("missing_capability"))
             for s in summaries if s.get("capability_unsupported")}
    if not gated:
        return "Every design ran on every model."
    lines = ["(which design a model cannot run, and why):"]
    for model, design, cap in sorted(gated):
        lines.append(f"- `{model}` cannot run **{design}** — missing `{cap or 'unknown'}`.")
    return "\n".join(lines)


def _failure_catalog(results: list[dict]) -> str:
    lines = ["## Failure catalog"]
    any_failure = False
    for r in results:
        if r.get("capability_unsupported"):
            continue
        val = r.get("validation") or {}
        nc = r.get("number_check") or {}
        judge = r.get("judge") or {}
        problems = []
        extra = r.get("extra") or {}
        if extra.get("plan_error"):
            problems.append(f"plan invalid: {extra['plan_error'][:120]}")
        if r.get("error"):
            problems.append(f"ERROR: {r['error']}")
        if val.get("number_leak"):
            problems.append(f"number leak: {', '.join(val.get('leaked_tokens', [])[:5])}")
        if val.get("bad_placeholders"):
            problems.append(f"bad placeholders: {', '.join(val['bad_placeholders'][:5])}")
        if nc.get("incorrect"):
            problems.append(f"{nc['incorrect']} incorrect inline number(s)")
        if judge.get("grounding_c_count"):
            problems.append(f"{judge['grounding_c_count']} hallucinated sentence(s)")
        if problems:
            any_failure = True
            lines.append(f"- **{r['design']} / {r['worker_model']} / {r['company']}**: "
                         + "; ".join(problems))
    if not any_failure:
        lines.append("- (none)")
    return "\n".join(lines)


def _factorial_2x3(model: str, agg: dict) -> str:
    """orchestration × treatment, each cell = `pooled-incorrect% / unsupported-claims`.
    incorrect drops left→middle (gate axis); unsupported drops middle→right (reflection axis)."""
    def cell(d):
        r = agg.get((model, d))
        if not r or r["capability_unsupported"]:
            return "—"
        nerr = r.get("n_error", 0)
        if r.get("n", 0) == 0:                       # every run errored -> no valid metric
            return f"err×{nerr}"
        base = f"{_fmt(r['pooled_incorrect_rate'], pct=True)} / {_fmt(r['unsupported_claims'])}"
        return base + (f" (err×{nerr})" if nerr else "")
    return (
        "**2×3 factorial — `pooled-incorrect% / unsupported-claims` (orchestration × treatment):**\n\n"
        "| orchestration ↓ / treatment → | no gate | +gate | +gate +reflection |\n"
        "|---|---|---|---|\n"
        f"| deterministic | {cell('single_shot')} | {cell('prompt_chaining')} | {cell('reflection')} |\n"
        f"| agentic | {cell('agentic')} | {cell('agentic_grounded')} | {cell('agentic_reflection')} |\n\n"
        "_designs: single_shot · prompt_chaining · reflection · agentic · agentic_grounded · agentic_reflection_\n"
    )


def build_report(results: list[dict], manifest: dict) -> str:
    summaries = [summarize_run(r) for r in results]
    agg = aggregate(summaries)
    models = sorted({s["worker_model"] for s in summaries})

    parts = ["# Tear Sheet Design-Risk Spike — Comparison Report", ""]
    for model in models:
        parts.append(f"## Worker model: `{model}`")
        parts.append(_matrix_table(model, agg))
        parts.append("")
        parts.append(_factorial_2x3(model, agg))
        parts.append("")
        parts.append(_within_model_comparisons(model, agg))
        parts.append("")
        parts.append(_READING_NOTES)
        parts.append("")

    parts.append(_AGENTIC_FAILURE_NOTE)
    parts.append("")

    parts.append("## Capability gating")
    parts.append(_capability_section(summaries))
    parts.append("")

    parts.append("## Cross-model observation (secondary)")
    parts.append("Design metrics are NOT pooled across models (a within-model comparison is the only "
                 "valid one). Compare a single design's robustness across models here. "
                 "**Judge-bias caveat:** the judge is fixed to Anthropic Sonnet; same-family judges may "
                 "mildly favor their own family's output, so cross-model quality scores are indicative, "
                 "not definitive.")
    parts.append("")

    parts.append(_failure_catalog(results))
    parts.append("")

    parts.append("## Run manifest")
    parts.append(f"- fixture_set_version: {manifest.get('fixture_set_version')}")
    parts.append(f"- judge: {manifest.get('judge', {}).get('model_id')}")
    parts.append(f"- workers: {', '.join(w['model_id'] for w in manifest.get('workers', []))}")
    parts.append(f"- prompt_hashes: {len(manifest.get('prompt_hashes', {}))} prompt files hashed")
    return "\n".join(parts)
