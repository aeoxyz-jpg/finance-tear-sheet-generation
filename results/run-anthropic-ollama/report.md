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
| single_shot | 12 | 0 | 2.0 | 2942.7 | 1156.8 | 23321.0 (n=1) | 0% | 7% | 2.2 | 2.8 | — | — |
| prompt_chaining | 12 | 0 | 3.1 | 4511.8 | 1234.6 | 25069.0 (n=1) | 17% | 3% | 1.9 | 3.1 | 100% | — |
| reflection | 12 | 0 | 8.1 | 14159.2 | 4129.6 | 72067.0 (n=1) | 17% | 3% | 0.6 | 0.6 | 100% | 3.0 |
| agentic | 12 | 0 | 3.0 | 7380.2 | 2346.9 | 14970.0 (n=1) | 0% | 28% | 10.0 | 5.8 | — | — |
| agentic_grounded | 12 | 0 | 3.0 | 7985.0 | 2670.4 | 44074.7 (n=12) | 100% | 0% | 13.6 | 6.8 | — | — |
| agentic_verified | 12 | 0 | 4.8 | 15189.5 | 4551.4 | 38724.8 (n=12) | 0% | 20% | 12.0 | 5.3 | — | 2.8 |

**2×2 factorial — pooled incorrect-rate (orchestration × number rail):**

| orchestration ↓ / rail → | none | hard (placeholder) |
|---|---|---|
| deterministic | 7% (single_shot) | 3% (prompt_chaining) |
| agentic | 28% (agentic) | 0% (agentic_grounded) |


**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): inline-number incorrect-rate 7% vs 3% → Δ 4%.
2. **prompt_chaining vs reflection** (does reflection earn its cost): Δ unsupported-claims -2.5 for Δ calls 5.0 (mean iterations 3.0; converged early in 17% of runs).
3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): incorrect-rate 3% vs 28%; calls 3.1 vs 3.0; valid-pass 17% vs 0%.
4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): incorrect-rate 28% vs 0% → Δ 28%.
5. **agentic vs agentic_verified** (what soft number_check correction buys): incorrect-rate 28% vs 20% → Δ 7%; calls 3.0 vs 4.8.
6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): incorrect-rate 3% vs 0%.

**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** (a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. **Whether that happens is model behavior, not structural:** the cross-model run shows it directly — Sonnet prompt_chaining cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 prompt_chaining omits them and stays on subject-company placeholders (→ 100%, verified to be full narratives, not degenerate brevity). The cap is contingent on the model interacting with the vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._

**Reading `latency_ms`:** the mean is over FRESHLY-TIMED cells only (cache-replayed cells contribute latency 0 and are excluded so they cannot dilute it); `(n=k)` is how many of the design's cells were live-timed. A row whose `n` is below the design's cell count was timed on a subset (the rest replayed from cache) — compare latency only between rows with comparable `n`, ideally one fully-live (`--refresh`) run where every row's `n` equals the full cell count.

## Worker model: `glm-5.1:cloud`
| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | incorrect_rate | grounding_C | unsupported | plan_valid | iters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_shot | 12 | 0 | 2.0 | 2713.8 | 714.2 | 16843.0 (n=1) | 0% | 6% | 1.1 | 0.9 | — | — |
| prompt_chaining | 12 | 0 | 4.0 | 4237.7 | 1061.8 | 34822.0 (n=1) | 25% | 4% | 1.0 | 1.7 | 83% | — |
| reflection | 12 | 0 | 8.7 | 10705.5 | 2852.8 | 53493.0 (n=1) | 17% | 3% | 0.2 | 0.1 | 83% | 2.8 |
| agentic | 12 | 0 | 3.0 | 5180.0 | 1274.1 | 8724.0 (n=1) | 0% | 39% | 5.2 | 4.2 | — | — |
| agentic_grounded | 12 | 0 | 3.4 | 6342.7 | 1760.2 | 47595.3 (n=12) | 42% | 0% | 11.2 | 6.3 | — | — |
| agentic_verified | 12 | 0 | 4.8 | 9502.2 | 1889.2 | 21305.0 (n=12) | 0% | 6% | 5.1 | 3.6 | — | 2.8 |

**2×2 factorial — pooled incorrect-rate (orchestration × number rail):**

| orchestration ↓ / rail → | none | hard (placeholder) |
|---|---|---|
| deterministic | 6% (single_shot) | 4% (prompt_chaining) |
| agentic | 39% (agentic) | 0% (agentic_grounded) |


**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): inline-number incorrect-rate 6% vs 4% → Δ 3%.
2. **prompt_chaining vs reflection** (does reflection earn its cost): Δ unsupported-claims -1.6 for Δ calls 4.7 (mean iterations 2.8; converged early in 58% of runs).
3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): incorrect-rate 4% vs 39%; calls 4.0 vs 3.0; valid-pass 25% vs 0%.
4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): incorrect-rate 39% vs 0% → Δ 39%.
5. **agentic vs agentic_verified** (what soft number_check correction buys): incorrect-rate 39% vs 6% → Δ 33%; calls 3.0 vs 4.8.
6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): incorrect-rate 4% vs 0%.

**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** (a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. **Whether that happens is model behavior, not structural:** the cross-model run shows it directly — Sonnet prompt_chaining cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 prompt_chaining omits them and stays on subject-company placeholders (→ 100%, verified to be full narratives, not degenerate brevity). The cap is contingent on the model interacting with the vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._

**Reading `latency_ms`:** the mean is over FRESHLY-TIMED cells only (cache-replayed cells contribute latency 0 and are excluded so they cannot dilute it); `(n=k)` is how many of the design's cells were live-timed. A row whose `n` is below the design's cell count was timed on a subset (the rest replayed from cache) — compare latency only between rows with comparable `n`, ideally one fully-live (`--refresh`) run where every row's `n` equals the full cell count.

## Why agentic underperforms (failure-mode analysis)

agentic's high incorrect-rate / grounding_C / unsupported in the matrix above are **not a weaker model** — it is the *same* worker model as prompt_chaining. The gap is purely orchestration, and it traces to three compounding mechanisms (observed in the Anthropic run; PRIV is illustrative):

1. **No placeholder rail (structural).** prompt_chaining/reflection are forced to write every figure as a `{{field_id}}` token drawn from the 15 subject fields that *exist*; the renderer substitutes real values, so the model's hands never touch a digit and it **physically cannot reference data the payload lacks**. agentic writes figures inline — every number passes through the model's working memory with no constraint blocking fabrication.
2. **Format-completion pressure → fabrication.** Told to produce a *complete* tear sheet, agentic reproduces the canonical banker layout (multi-year history, full comps) and fills the cells with invented data when the payload is point-in-time. On PRIV (LTM-only payload) it fabricated a 5-year revenue history `$180M→$310M` where only the `$325M` LTM column is real (~28 invented figures), and invented market caps (`$850M`, `$1,100M`) for comparables whose table carries no market-cap field — despite the prompt's explicit "never invent numbers."
3. **Editorial autonomy → unsupported causal/directionality.** Free prose lets it assert causes the data never supports ("signaling strong deleveraging", "reflecting improving operational efficiency", "signals an inorganic growth strategy") — these feed grounding_C and unsupported.

prompt_chaining, constrained to placeholders, scored incorrect=0 on the same company. **The placeholder vocabulary acts as a hard anti-fabrication rail; the agentic cost (27% vs 3% incorrect, grounding_C 10.7 vs 2.0) is what removing that rail buys.** That is the spike's headline design-risk finding.

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
- **single_shot / claude-sonnet-4-6 / ADRC**: number leak: 8.5%, 26.4%, 0.9x, 9.5x, 2.5x; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / CONG**: number leak: $52.0, $10.2, $7.9, $5.7, $4.6; 1 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / HYPR**: number leak: $7.4, $680, $490, $310, $380; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / claude-sonnet-4-6 / AMBG**: number leak: $2,950.0, $720.0, $550.0, $402.0, $310.0; 2 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / ACME**: number leak: $3.2, 15.2x, 18.1x, 14.0x
- **prompt_chaining / claude-sonnet-4-6 / MEGA**: number leak: $12.0, $8.5, 5.1x, 5.8x, 6.1x; 1 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / THIN**: 1 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / LOSS**: 1 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / PRIV**: number leak: $45, 9.8x, 11.2x; 6 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / BANK**: number leak: $1.8; 2 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / NOTX**: number leak: 8.1x, 9.2x, 7.8x; 1 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / MERG**: number leak: $11.9, $2.8, $1.9, $3.4, $1.6; 2 incorrect inline number(s); 2 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / ADRC**: number leak: 9.8x, 10.2x, 8.9x; 2 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / CONG**: number leak: $4.2, $6.8, 6.8x, 6.0x, 7.5x; 1 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / HYPR**: number leak: 42.0x, 31.0x, 45.0x; 2 hallucinated sentence(s)
- **prompt_chaining / claude-sonnet-4-6 / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x; 4 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / ACME**: number leak: $3.2, 15.2x, 18.1x, 14.0x
- **reflection / claude-sonnet-4-6 / MEGA**: number leak: $12.0, $8.5, 5.1x, 5.8x, 6.1x; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / PRIV**: number leak: 9.8x, 11.2x; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / BANK**: bad placeholders: [transactions.value]; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / NOTX**: number leak: 8.1x, 9.2x, 7.8x; 1 hallucinated sentence(s)
- **reflection / claude-sonnet-4-6 / MERG**: number leak: $11.9, $2.8, $1.9, $3.4, $1.6; 2 incorrect inline number(s)
- **reflection / claude-sonnet-4-6 / ADRC**: number leak: 9.8x, 10.2x, 8.9x, 9.6x; 2 hallucinated sentence(s)
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
- **agentic / claude-sonnet-4-6 / ADRC**: number leak: 26.4%, 10.3%, 8.5%, 11.8%, 9.5x; 7 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / CONG**: number leak: $170.00, $85.0, $91.0, $38,000, $42,000; 32 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / HYPR**: number leak: $7.4, $56.00, $28,000, $25,500, $500; 5 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / claude-sonnet-4-6 / AMBG**: number leak: $26.00, $6,500, $6,900, $400, $1,200; 30 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / ACME**: 18 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / MEGA**: 12 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / THIN**: 8 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / LOSS**: 13 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / PRIV**: 12 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / BANK**: 16 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / NOTX**: 12 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / MERG**: 13 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / ADRC**: 19 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / CONG**: 10 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / HYPR**: 17 hallucinated sentence(s)
- **agentic_grounded / claude-sonnet-4-6 / AMBG**: 13 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / ACME**: number leak: $000, $312.50, $250,000, $241,500, $13.5; 4 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / MEGA**: number leak: $400.00, $12, 10.5%, 23.3%, 24.4%; 14 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / THIN**: number leak: $420, $50, $35, $150, $158; 26 incorrect inline number(s); 12 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / LOSS**: number leak: $500, $2,800, $320, $580, $920; 16 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / PRIV**: number leak: $180, $215, $260, $310; 9 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / BANK**: number leak: $8,200, $10,500, $2,600, $11,400, $2.85; 9 incorrect inline number(s); 14 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / NOTX**: number leak: $5,200, $5.2, $7,900, $7.9, $1,500; 27 incorrect inline number(s); 22 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / MERG**: number leak: $11,950, $2.8, $1.95, $4,500, $24,000; 16 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / ADRC**: number leak: 26.4%, 10.3%, 8.5%, 11.8%, 9.5x; 8 incorrect inline number(s); 17 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / CONG**: number leak: $38,000.0, $38.0, $52,000.0, $52.0, $13.1; 5 incorrect inline number(s); 9 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / HYPR**: number leak: $12,200, $1,400, $0.92, $800, $22; 10 incorrect inline number(s); 13 hallucinated sentence(s)
- **agentic_verified / claude-sonnet-4-6 / AMBG**: number leak: $26.00, $6,500, $6,900, $400, $1,200; 14 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / ACME**: number leak: $42.3, $14.5, $8.8, $7.5, $13.5; 3 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / MEGA**: number leak: $1680.0, $410.0, $332.0, $230.0, $188.0
- **single_shot / glm-5.1:cloud / THIN**: number leak: $630, $132, $102, $70, $52; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / LOSS**: number leak: $4.0, $580, $780, $920, $610; 4 incorrect inline number(s)
- **single_shot / glm-5.1:cloud / PRIV**: number leak: $325, $82, $63, $45, $32; 2 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / BANK**: number leak: $10.9, $2.7, $2.5, $73.0, $18.0; 2 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / NOTX**: number leak: $8.2, $2.3, $1.8, $1.4, $1.1; 3 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / MERG**: number leak: $21.5, $5.0, $2.8, $2.2, $3.5; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / ADRC**: number leak: 8.5%, 26.4%, 15.3%, 9.5x, 2.5x; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / CONG**: number leak: $52.0, $10.2, $5.7, $4.6, $12.0
- **single_shot / glm-5.1:cloud / HYPR**: number leak: $7.4, $680, $490, $310, $380; 1 hallucinated sentence(s)
- **single_shot / glm-5.1:cloud / AMBG**: number leak: $3.0, $720, $402, $310, $400; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **prompt_chaining / glm-5.1:cloud / ACME**: bad placeholders: comparables_0_ev_ebitda, comparables_1_ev_ebitda, comparables_2_ev_ebitda, transactions_0_date, transactions_0_value; 2 hallucinated sentence(s)
- **prompt_chaining / glm-5.1:cloud / MEGA**: plan invalid: 3 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'field': 'di; number leak: 3.9x, 6.1x; bad placeholders: date_0, value_0, date_1, value_1
- **prompt_chaining / glm-5.1:cloud / THIN**: 1 hallucinated sentence(s)
- **prompt_chaining / glm-5.1:cloud / PRIV**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: $45, 9.8x, 11.2x; 1 hallucinated sentence(s)
- **prompt_chaining / glm-5.1:cloud / BANK**: number leak: $1.8; 1 hallucinated sentence(s)
- **prompt_chaining / glm-5.1:cloud / NOTX**: number leak: 8.1x, 9.2x, 7.8x; 1 hallucinated sentence(s)
- **prompt_chaining / glm-5.1:cloud / MERG**: number leak: $2.2, $1.6, $3.4, $1.9, $2.8; 1 incorrect inline number(s)
- **prompt_chaining / glm-5.1:cloud / ADRC**: 1 hallucinated sentence(s)
- **prompt_chaining / glm-5.1:cloud / CONG**: number leak: 6.8x, 6.0x, 22.0x; bad placeholders: value, value; 2 hallucinated sentence(s)
- **prompt_chaining / glm-5.1:cloud / HYPR**: bad placeholders: date, value, date, value; 3 hallucinated sentence(s)
- **prompt_chaining / glm-5.1:cloud / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x
- **reflection / glm-5.1:cloud / ACME**: bad placeholders: comparables_0_ev_ebitda, comparables_1_ev_ebitda, comparables_2_ev_ebitda, transactions_0_date, transactions_0_value
- **reflection / glm-5.1:cloud / MEGA**: plan invalid: 3 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'field': 'di; number leak: 3.9x, 6.1x; bad placeholders: date_0, value_0, date_1, value_1
- **reflection / glm-5.1:cloud / PRIV**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: 9.8x, 11.2x; bad placeholders: transaction_0_value
- **reflection / glm-5.1:cloud / BANK**: bad placeholders: transactions_0_value
- **reflection / glm-5.1:cloud / NOTX**: number leak: 8.1x, 9.2x, 7.8x
- **reflection / glm-5.1:cloud / MERG**: number leak: $2.2, $1.6, $3.4, $1.9, $2.8; 1 incorrect inline number(s)
- **reflection / glm-5.1:cloud / ADRC**: number leak: 9.8x, 10.2x, 8.9x; 1 hallucinated sentence(s)
- **reflection / glm-5.1:cloud / CONG**: number leak: 6.8x, 6.0x, 22.0x; 1 hallucinated sentence(s)
- **reflection / glm-5.1:cloud / HYPR**: number leak: 42.0x, 45.0x, 31.0x; bad placeholders: date, value, date, value; 1 hallucinated sentence(s)
- **reflection / glm-5.1:cloud / AMBG**: number leak: 10.1x, 8.8x, 11.3x; bad placeholders: transactions_0_value, transactions_0_date
- **agentic / glm-5.1:cloud / ACME**: number leak: $312.50, $250.0, $241.5, $13.5, $5.0; 5 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / MEGA**: number leak: $400, $2.0, $1.96, $1.68, $410; 18 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / THIN**: number leak: $8.00, $800, $950, $150, $200; 6 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / LOSS**: number leak: $7.00, $3.5, $4.4, $1.2, $300; 14 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / PRIV**: number leak: $180, $310, $325, $42, $82; 9 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / BANK**: number leak: $45.00, $45,000, $10,900, $8,200, $2,700; 6 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / NOTX**: number leak: $72.00, $18.0, $19.5, $1.5, $3.5; 6 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / MERG**: number leak: $140, $35.0, $39.5, $21.5, $9.5; 6 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / ADRC**: number leak: 26.4%, 15.3%, 8.5%, 0.9x, 9.5x; 9 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / CONG**: number leak: $170, $85, $91, $52, $38; 12 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / HYPR**: number leak: $56.00, $28.0, $25.5, $1.0, $4.5; 8 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / glm-5.1:cloud / AMBG**: number leak: $26.00, $6,500, $6,900, $2,950, $1,800; 4 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / ACME**: 11 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / MEGA**: 10 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / THIN**: number leak: 3.3%, 12.96%; 8 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / LOSS**: number leak: 11.1%, 4,000, 3,600; 12 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / PRIV**: 14 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / BANK**: number leak: 11.2%, 10,900, 9,800, 45,000, 73,000; 9 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / NOTX**: bad placeholders: field_id, earnings_sentiment_score; 9 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / MERG**: number leak: 31.1%, 25%, 21,500, 16,400; 12 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / ADRC**: 16 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / CONG**: 14 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / HYPR**: number leak: 65%, 42.0x, 31.0x, 45.0x; bad placeholders: earnings_sentiment; 9 hallucinated sentence(s)
- **agentic_grounded / glm-5.1:cloud / AMBG**: number leak: 20.4%, 3%, 2,950, 2,450; bad placeholders: earnings_sentiment; 10 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / ACME**: number leak: $312.50, $250.0, $241.5, $13.5, $5.0; 4 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / MEGA**: number leak: $400, 24.4%, 14%; 4 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / THIN**: number leak: $8.00, $800, $950, $630, $132; 5 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / LOSS**: number leak: $7.00; 8 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / PRIV**: number leak: 20%, 25%; 5 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / BANK**: number leak: $45.00, $45,000, $10,900, $2,700, $1,800; 5 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / NOTX**: number leak: $72.00, $18.0, $19.5, $1.5, $3.5; 1 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / MERG**: number leak: $140, $35.0, $39.5, $21.5, $9.5; 6 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / ADRC**: number leak: 26.4%, 15.3%, 8.5%, 0.9x, 9.5x; 4 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / CONG**: number leak: $170, $85, $91, $52, $38,000; 5 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / HYPR**: number leak: $56.00, $28.0, $25.5, $680, $490; 5 hallucinated sentence(s)
- **agentic_verified / glm-5.1:cloud / AMBG**: number leak: $26.00, $6,500, $6,900, $2,950, $720; 6 hallucinated sentence(s)

## Run manifest
- fixture_set_version: 1
- judge: claude-sonnet-4-6
- workers: claude-sonnet-4-6, glm-5.1:cloud
- prompt_hashes: 9 prompt files hashed