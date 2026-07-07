# Tear Sheet Design-Risk Spike — Comparison Report

> **CORRECTION (2026-07-07):** the `incorrect_rate` and `grounding_C` columns below for tool-using
> (agentic-family) designs measure a data-scope mismatch between what the design legitimately saw (full
> tool/fixture data) and what the grading was scoped to (the narrow 15-field payload) — **not**
> fabrication or hallucination. Genuine fabrication, re-measured by tracing every flagged token back to
> its tool output, is ≈0% on all 7 models tested. Tables below are left unedited (raw benchmark output);
> see `results/CORRECTION-2026-07-07-grading-scope-artifact.md` for the corrected interpretation and the reproducible re-measurement.

## Worker model: `claude-sonnet-4-6`
| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | incorrect_rate | grounding_C | unsupported | plan_valid | iters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_shot | 12 | 0 | 2.0 | 2943.2 | 1146.8 | 0.0 | 0% | 7% | 2.2 | 2.8 | — | — |
| conservative | 12 | 0 | 3.1 | 4509.8 | 1233.5 | 0.0 | 17% | 3% | 2.0 | 2.9 | 100% | — |
| reflection | 12 | 0 | 8.1 | 14109.7 | 4070.2 | 0.0 | 17% | 3% | 0.5 | 0.5 | 100% | 3.0 |
| agentic | 12 | 0 | 3.0 | 7379.2 | 2373.8 | 0.0 | 0% | 27% | 10.7 | 5.8 | — | — |

**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs conservative** (headline — what placeholder discipline buys): inline-number incorrect-rate 7% vs 3% → Δ 4%.
2. **conservative vs reflection** (does reflection earn its cost): Δ unsupported-claims -2.4 for Δ calls 5.0 (mean iterations 3.0; converged early in 25% of runs).
3. **conservative vs agentic** (LLM orchestration cost/reliability): incorrect-rate 3% vs 27%; calls 3.1 vs 3.0; valid-pass 17% vs 0%.

**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** (a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. **Whether that happens is model behavior, not structural:** the cross-model run shows it directly — Sonnet conservative cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 conservative omits them and stays on subject-company placeholders (→ 100%, verified to be full narratives, not degenerate brevity). The cap is contingent on the model interacting with the vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._

**Reading `latency_ms`:** 0 under cache replay (every call was a cache hit). Token counts and call counts are preserved through the cache; latency is not. A clean latency profile needs a single live `--refresh` run.

## Worker model: `glm-5.1:cloud`
| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | incorrect_rate | grounding_C | unsupported | plan_valid | iters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_shot | 12 | 0 | 2.0 | 2668.2 | 2054.9 | 3260.3 | 0% | 5% | 0.5 | 0.7 | — | — |
| conservative | 12 | 0 | 4.0 | 4372.4 | 6145.7 | 0.0 | 100% | 0% | 1.2 | 1.0 | 25% | — |
| reflection | 6 | 6 | 6.7 | 8451.3 | 12794.8 | 0.0 | 100% | 0% | 0.0 | 0.0 | 17% | 1.8 |
| agentic | 12 | 0 | 3.0 | 5195.5 | 1688.7 | 0.0 | 0% | 32% | 5.9 | 3.9 | — | — |

**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs conservative** (headline — what placeholder discipline buys): inline-number incorrect-rate 5% vs 0% → Δ 5%.
2. **conservative vs reflection** (does reflection earn its cost): Δ unsupported-claims -1.0 for Δ calls 2.7 (mean iterations 1.8; converged early in 100% of runs).
3. **conservative vs agentic** (LLM orchestration cost/reliability): incorrect-rate 0% vs 32%; calls 4.0 vs 3.0; valid-pass 100% vs 0%.

**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** (a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. **Whether that happens is model behavior, not structural:** the cross-model run shows it directly — Sonnet conservative cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 conservative omits them and stays on subject-company placeholders (→ 100%, verified to be full narratives, not degenerate brevity). The cap is contingent on the model interacting with the vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._

**Reading `latency_ms`:** 0 under cache replay (every call was a cache hit). Token counts and call counts are preserved through the cache; latency is not. A clean latency profile needs a single live `--refresh` run.

## Why agentic underperforms (failure-mode analysis)

agentic's high incorrect-rate / grounding_C / unsupported in the matrix above are **not a weaker model** — it is the *same* worker model as conservative. The gap is purely orchestration, and it traces to three compounding mechanisms (observed in the Anthropic run; PRIV is illustrative):

1. **No placeholder rail (structural).** conservative/reflection are forced to write every figure as a `{{field_id}}` token drawn from the 15 subject fields that *exist*; the renderer substitutes real values, so the model's hands never touch a digit and it **physically cannot reference data the payload lacks**. agentic writes figures inline — every number passes through the model's working memory with no constraint blocking fabrication.
2. **Format-completion pressure → fabrication.** Told to produce a *complete* tear sheet, agentic reproduces the canonical banker layout (multi-year history, full comps) and fills the cells with invented data when the payload is point-in-time. On PRIV (LTM-only payload) it fabricated a 5-year revenue history `$180M→$310M` where only the `$325M` LTM column is real (~28 invented figures), and invented market caps (`$850M`, `$1,100M`) for comparables whose table carries no market-cap field — despite the prompt's explicit "never invent numbers."
3. **Editorial autonomy → unsupported causal/directionality.** Free prose lets it assert causes the data never supports ("signaling strong deleveraging", "reflecting improving operational efficiency", "signals an inorganic growth strategy") — these feed grounding_C and unsupported.

conservative, constrained to placeholders, scored incorrect=0 on the same company. **The placeholder vocabulary acts as a hard anti-fabrication rail; the agentic cost (27% vs 3% incorrect, grounding_C 10.7 vs 2.0) is what removing that rail buys.** That is the spike's headline design-risk finding.

## Capability gating
Every design ran on every model.

## Cross-model observation (secondary)
Design metrics are NOT pooled across models (a within-model comparison is the only valid one). Compare a single design's robustness across models here. **Judge-bias caveat:** the judge is fixed to Anthropic Sonnet; same-family judges may mildly favor their own family's output, so cross-model quality scores are indicative, not definitive.

## Failure catalog
- **single_shot / claude-sonnet-4-6 / ACME**: number leak: $42.3, $14.5, $11.6, $8.8, $7.5; 3 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / MEGA**: number leak: $1,680.0, $410.0, $332.0, $230.0, $188.0; 1 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / THIN**: number leak: $630, $132, $102, $70, $52; 1 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / LOSS**: number leak: $4.0, $580, $780, $920, $610; 5 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / PRIV**: number leak: $325, $82, $63, $45, $32; 3 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / BANK**: number leak: $10.9, $2.7, $2.5, $73.0, $18.0; 1 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / NOTX**: number leak: $8.2, $2.3, $1.8, $1.4, $1.1; 3 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / MERG**: number leak: $21.5, $5.0, $3.9, $2.8, $2.2; 4 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / ADRC**: number leak: $5.3, $1.4, $1.1, $810, $660; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / CONG**: number leak: $52.0, $10.2, $7.9, $5.7, $4.6; 1 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / HYPR**: number leak: $7.4, $680, $490, $310, $380; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / AMBG**: number leak: $2,950.0, $720.0, $550.0, $402.0, $310.0; 2 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / ACME**: number leak: $3.2, 15.2x, 18.1x, 14.0x
- **conservative / claude-sonnet-4-6 / MEGA**: number leak: $12.0, $8.5, 5.1x, 5.8x, 6.1x; 1 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / THIN**: 1 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / LOSS**: 1 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / PRIV**: number leak: $45, 9.8x, 11.2x; 6 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / BANK**: number leak: $1.8; 2 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / NOTX**: number leak: 8.1x, 9.2x, 7.8x; 1 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / MERG**: number leak: $11.9, $2.8, $1.9, $3.4, $1.6; 2 incorrect inline number(s); 2 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / ADRC**: number leak: $850, 10.2x, 9.8x, 8.9x; 3 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / CONG**: number leak: $4.2, $6.8, 6.8x, 6.0x, 7.5x; 1 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / HYPR**: number leak: 42.0x, 31.0x, 45.0x; 2 hallucinated sentence(s)
- **conservative / claude-sonnet-4-6 / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x; 4 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / ACME**: number leak: $3.2, 15.2x, 18.1x, 14.0x
- **reflection / claude-sonnet-4-6 / MEGA**: number leak: $12.0, $8.5, 5.1x, 5.8x, 6.1x; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / PRIV**: number leak: 9.8x, 11.2x; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / BANK**: bad placeholders: [transactions.value]; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / NOTX**: number leak: 8.1x, 9.2x, 7.8x; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / MERG**: number leak: $11.9, $2.8, $1.9, $3.4, $1.6; 2 incorrect inline number(s)
- **reflection / claude-sonnet-4-6 / ADRC**: number leak: 10.2x, 9.8x, 8.9x; bad placeholders: transactions[0].value; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / CONG**: number leak: $4.2, $6.8, 6.8x, 6.0x, 7.5x
- **reflection / claude-sonnet-4-6 / HYPR**: number leak: 42.0x, 31.0x, 45.0x; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x
- **agentic / claude-sonnet-4-6 / ACME**: number leak: $000, $312.50, $250.0, $241.5, $13.5; 5 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / MEGA**: number leak: $400.00, $2,000,000, $1,960,000, $48.20, $12,000; 6 incorrect inline number(s); 13 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / THIN**: number leak: $8.00, $800, $950, $420, $490; 21 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / LOSS**: number leak: $500, $7.00, $3,500, $4,400, $2,800; 13 incorrect inline number(s); 11 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / PRIV**: number leak: $180, $215, $260, $310, $325; 35 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / BANK**: number leak: $45.00, $45,000, $8,200, $10,500, $10,900; 8 incorrect inline number(s); 11 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / NOTX**: number leak: $5,200, $7,900, $8,200, $72.00, $18,000; 9 incorrect inline number(s); 22 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / MERG**: number leak: $11.95, $2.8, $1.95, $140.00, $35,000; 6 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / ADRC**: number leak: 26.4%, 10.3%, 8.5%, 11.8%, 9.5x; 18 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / CONG**: number leak: $170.00, $85.0, $91.0, $38,000, $42,000; 32 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / HYPR**: number leak: $7.4, $56.00, $28,000, $25,500, $500; 5 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / AMBG**: number leak: $26.00, $6,500, $6,900, $400, $1,200; 30 incorrect inline number(s); 8 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / ACME**: number leak: $42.3, $14.5, $8.8, $7.5, $13.5; 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / MEGA**: number leak: $1680.0, $410.0, $230.0, $188.0, $120.0
- **single_shot / glm-5.1:cloud / THIN**: number leak: $630, $132, $70, $102, $52; 1 incorrect inline number(s)
- **single_shot / glm-5.1:cloud / LOSS**: number leak: $4.0, $580, $920, $610, $300; 3 incorrect inline number(s)
- **single_shot / glm-5.1:cloud / PRIV**: number leak: $325, $82, $45, $32, $30; 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / BANK**: number leak: $10.9, $2.7, $2.5, $73.0, $18.0; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / NOTX**: number leak: $8.2, $2.3, $1.4, $1.1, $2.0; 2 incorrect inline number(s)
- **single_shot / glm-5.1:cloud / MERG**: number leak: $21.5, $5.0, $2.8, $3.5, $8.0; 2 incorrect inline number(s)
- **single_shot / glm-5.1:cloud / ADRC**: number leak: $5.3, $1.4, $810, $2.8, $1.5; 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / CONG**: number leak: $52.0, $10.2, $5.7, $4.6, $18.0; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / HYPR**: number leak: $7.4, $680, $310, $380, $3.0
- **single_shot / glm-5.1:cloud / AMBG**: number leak: $3.0, $720, $402, $310, $800; 1 incorrect inline number(s)
- **conservative / glm-5.1:cloud / ACME**: 2 hallucinated sentence(s)
- **conservative / glm-5.1:cloud / LOSS**: 1 hallucinated sentence(s)
- **conservative / glm-5.1:cloud / PRIV**: 1 hallucinated sentence(s)
- **conservative / glm-5.1:cloud / BANK**: 2 hallucinated sentence(s)
- **conservative / glm-5.1:cloud / ADRC**: 7 hallucinated sentence(s)
- **conservative / glm-5.1:cloud / CONG**: 1 hallucinated sentence(s)
- **conservative / glm-5.1:cloud / HYPR**: 1 hallucinated sentence(s)
- **reflection / glm-5.1:cloud / PRIV**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **reflection / glm-5.1:cloud / BANK**: ERROR: JSONDecodeError('Unterminated string starting at: line 13 column 7 (char 427)')
- **reflection / glm-5.1:cloud / MERG**: ERROR: JSONDecodeError('Unterminated string starting at: line 24 column 15 (char 889)')
- **reflection / glm-5.1:cloud / ADRC**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **reflection / glm-5.1:cloud / HYPR**: ERROR: JSONDecodeError('Unterminated string starting at: line 12 column 15 (char 454)')
- **reflection / glm-5.1:cloud / AMBG**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **agentic / glm-5.1:cloud / ACME**: number leak: $312.50, $250.0, $241.5, $13.5, $5.0; 4 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / MEGA**: number leak: $400, $2.0, $1.96, $1.20, $1.68; 16 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / THIN**: number leak: $8.00, $800, $950, $200, $50; 4 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / LOSS**: number leak: $7.00, $3.5, $4.4, $900, $1.2; 12 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / PRIV**: number leak: $325, $82, $63, $45, $32; 10 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / BANK**: number leak: $45.00, $45.0, $10.9, $8.2, $2.7; 6 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / NOTX**: number leak: $72.00, $18.0, $19.5, $8.2, $5.2; 7 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / MERG**: number leak: $140, $35.0, $39.5, $4.5, $8.0; 6 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / ADRC**: number leak: 26.4%, 12%, 25%, 27%, 8.5%; 6 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / CONG**: number leak: $170, $85, $91, $18, $12; 7 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / HYPR**: number leak: $56.00, $28.0, $25.5, $3.0, $500; 7 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / AMBG**: number leak: $26.00, $6,500, $6,900, $2,950, $720; 6 incorrect inline number(s); 6 hallucinated sentence(s)

## Run manifest
- fixture_set_version: 1
- judge: claude-sonnet-4-6
- workers: claude-sonnet-4-6, glm-5.1:cloud
- prompt_hashes: 7 prompt files hashed