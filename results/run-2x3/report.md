# Tear Sheet Design-Risk Spike — Comparison Report

## Worker model: `claude-sonnet-4-6`
| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | incorrect_rate | grounding_C | unsupported | plan_valid | iters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_shot | 12 | 0 | 2.0 | 2942.7 | 1156.8 | 23321.0 (n=1) | 0% | 7% | 2.2 | 2.8 | — | — |
| prompt_chaining | 12 | 0 | 3.1 | 4511.8 | 1234.6 | 25069.0 (n=1) | 17% | 3% | 1.9 | 3.1 | 100% | — |
| reflection | 12 | 0 | 8.1 | 14159.2 | 4129.6 | 72067.0 (n=1) | 17% | 3% | 0.6 | 0.6 | 100% | 3.0 |
| agentic | 12 | 0 | 3.0 | 7380.2 | 2346.9 | 14970.0 (n=1) | 0% | 28% | 10.0 | 5.8 | — | — |
| agentic_grounded | 12 | 0 | 3.0 | 7985.0 | 2670.4 | 44074.7 (n=12) | 100% | 0% | 13.6 | 6.8 | — | — |
| agentic_reflection | 12 | 0 | 8.0 | 21497.5 | 7399.4 | 112512.9 (n=12) | 58% | 0% | 5.2 | 2.4 | — | 3.0 |

**2×3 factorial — `pooled-incorrect% / unsupported-claims` (orchestration × treatment):**

| orchestration ↓ / treatment → | no gate | +gate | +gate +reflection |
|---|---|---|---|
| deterministic | 7% / 2.8 | 3% / 3.1 | 3% / 0.6 |
| agentic | 28% / 5.8 | 0% / 6.8 | 0% / 2.4 |

_designs: single_shot · prompt_chaining · reflection · agentic · agentic_grounded · agentic_reflection_


**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): inline-number incorrect-rate 7% vs 3% → Δ 4%.
2. **prompt_chaining vs reflection** (does reflection earn its cost): Δ unsupported-claims -2.5 for Δ calls 5.0 (mean iterations 3.0; converged early in 17% of runs).
3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): incorrect-rate 3% vs 28%; calls 3.1 vs 3.0; valid-pass 17% vs 0%.
4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): incorrect-rate 28% vs 0% → Δ 28%.
6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): incorrect-rate 3% vs 0%.
7. **agentic_grounded vs agentic_reflection** (reflection on the agentic row): unsupported 6.8 vs 2.4 → Δ 4.3; calls 3.0 vs 8.0.
8. **single_shot vs agentic** (orchestration at no-gate): incorrect-rate 7% vs 28%.
9. **reflection vs agentic_reflection** (orchestration at full-stack): incorrect-rate 3% vs 0%; unsupported 0.6 vs 2.4.

**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** (a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. **Whether that happens is model behavior, not structural:** the cross-model run shows it directly — Sonnet prompt_chaining cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 prompt_chaining omits them and stays on subject-company placeholders (→ 100%, verified to be full narratives, not degenerate brevity). The cap is contingent on the model interacting with the vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._

**Reading `latency_ms`:** the mean is over FRESHLY-TIMED cells only (cache-replayed cells contribute latency 0 and are excluded so they cannot dilute it); `(n=k)` is how many of the design's cells were live-timed. A row whose `n` is below the design's cell count was timed on a subset (the rest replayed from cache) — compare latency only between rows with comparable `n`, ideally one fully-live (`--refresh`) run where every row's `n` equals the full cell count.

## Worker model: `deepseek-v4-pro`
| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | incorrect_rate | grounding_C | unsupported | plan_valid | iters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_shot | 12 | 0 | 2.0 | 2753.0 | 794.8 | 11501.7 (n=12) | 0% | 7% | 1.4 | 1.5 | — | — |
| prompt_chaining | 12 | 0 | 4.0 | 4419.9 | 1215.6 | 19791.8 (n=12) | 17% | 3% | 2.2 | 2.4 | 75% | — |
| reflection | 12 | 0 | 8.3 | 10874.1 | 2970.3 | 48516.9 (n=12) | 33% | 3% | 1.0 | 0.8 | 75% | 2.7 |
| agentic | 12 | 0 | 4.0 | 6930.1 | 1736.1 | 27130.2 (n=12) | 0% | 29% | 9.2 | 5.1 | — | — |
| agentic_grounded | 12 | 0 | 4.0 | 7834.2 | 2260.1 | 33741.6 (n=12) | 0% | 15% | 12.1 | 5.6 | — | — |
| agentic_reflection | 12 | 0 | 8.5 | 15944.6 | 4446.8 | 74855.8 (n=12) | 25% | 14% | 2.8 | 1.4 | — | 2.8 |

**2×3 factorial — `pooled-incorrect% / unsupported-claims` (orchestration × treatment):**

| orchestration ↓ / treatment → | no gate | +gate | +gate +reflection |
|---|---|---|---|
| deterministic | 7% / 1.5 | 3% / 2.4 | 3% / 0.8 |
| agentic | 29% / 5.1 | 15% / 5.6 | 14% / 1.4 |

_designs: single_shot · prompt_chaining · reflection · agentic · agentic_grounded · agentic_reflection_


**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): inline-number incorrect-rate 7% vs 3% → Δ 4%.
2. **prompt_chaining vs reflection** (does reflection earn its cost): Δ unsupported-claims -1.6 for Δ calls 4.3 (mean iterations 2.7; converged early in 50% of runs).
3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): incorrect-rate 3% vs 29%; calls 4.0 vs 4.0; valid-pass 17% vs 0%.
4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): incorrect-rate 29% vs 15% → Δ 14%.
6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): incorrect-rate 3% vs 15%.
7. **agentic_grounded vs agentic_reflection** (reflection on the agentic row): unsupported 5.6 vs 1.4 → Δ 4.2; calls 4.0 vs 8.5.
8. **single_shot vs agentic** (orchestration at no-gate): incorrect-rate 7% vs 29%.
9. **reflection vs agentic_reflection** (orchestration at full-stack): incorrect-rate 3% vs 14%; unsupported 0.8 vs 1.4.

**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** (a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. **Whether that happens is model behavior, not structural:** the cross-model run shows it directly — Sonnet prompt_chaining cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 prompt_chaining omits them and stays on subject-company placeholders (→ 100%, verified to be full narratives, not degenerate brevity). The cap is contingent on the model interacting with the vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._

**Reading `latency_ms`:** the mean is over FRESHLY-TIMED cells only (cache-replayed cells contribute latency 0 and are excluded so they cannot dilute it); `(n=k)` is how many of the design's cells were live-timed. A row whose `n` is below the design's cell count was timed on a subset (the rest replayed from cache) — compare latency only between rows with comparable `n`, ideally one fully-live (`--refresh`) run where every row's `n` equals the full cell count.

## Worker model: `gemini-3-flash-preview`
| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | incorrect_rate | grounding_C | unsupported | plan_valid | iters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_shot | 12 | 0 | 2.0 | 2839.4 | 1963.5 | 14662.2 (n=12) | 0% | 4% | 1.8 | 1.8 | — | — |
| prompt_chaining | 12 | 0 | 4.0 | 4566.8 | 9434.6 | 48944.5 (n=12) | 100% | 0% | 1.8 | 1.5 | 83% | — |
| reflection | 9 | 3 | 6.1 | 8069.4 | 16096.9 | 79922.9 (n=9) | 100% | 0% | 1.0 | 0.7 | 78% | 1.6 |
| agentic | 12 | 0 | 4.0 | 5685.9 | 2384.2 | 19704.8 (n=12) | 0% | 26% | 5.5 | 3.2 | — | — |
| agentic_grounded | 12 | 0 | 4.1 | 6023.5 | 3708.8 | 24444.8 (n=12) | 100% | 0% | 5.9 | 2.3 | — | — |
| agentic_reflection | 1 | 11 | 7.0 | 9814.0 | 15216.0 | 74835.0 (n=1) | 100% | 0% | 1.0 | 0.0 | — | 2.0 |

**2×3 factorial — `pooled-incorrect% / unsupported-claims` (orchestration × treatment):**

| orchestration ↓ / treatment → | no gate | +gate | +gate +reflection |
|---|---|---|---|
| deterministic | 4% / 1.8 | 0% / 1.5 | 0% / 0.7 (err×3) |
| agentic | 26% / 3.2 | 0% / 2.3 | 0% / 0.0 (err×11) |

_designs: single_shot · prompt_chaining · reflection · agentic · agentic_grounded · agentic_reflection_


**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): inline-number incorrect-rate 4% vs 0% → Δ 4%.
2. **prompt_chaining vs reflection** (does reflection earn its cost): Δ unsupported-claims -0.8 for Δ calls 2.1 (mean iterations 1.6; converged early in 100% of runs).
3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): incorrect-rate 0% vs 26%; calls 4.0 vs 4.0; valid-pass 100% vs 0%.
4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): incorrect-rate 26% vs 0% → Δ 26%.
6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): incorrect-rate 0% vs 0%.
7. **agentic_grounded vs agentic_reflection** (reflection on the agentic row): unsupported 2.3 vs 0.0 → Δ 2.3; calls 4.1 vs 7.0.
8. **single_shot vs agentic** (orchestration at no-gate): incorrect-rate 4% vs 26%.
9. **reflection vs agentic_reflection** (orchestration at full-stack): incorrect-rate 0% vs 0%; unsupported 0.7 vs 0.0.

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
| agentic_reflection | 12 | 0 | 8.1 | 14622.3 | 4160.7 | 91583.8 (n=12) | 42% | 0% | 2.4 | 1.1 | — | 2.8 |

**2×3 factorial — `pooled-incorrect% / unsupported-claims` (orchestration × treatment):**

| orchestration ↓ / treatment → | no gate | +gate | +gate +reflection |
|---|---|---|---|
| deterministic | 6% / 0.9 | 4% / 1.7 | 3% / 0.1 |
| agentic | 39% / 4.2 | 0% / 6.3 | 0% / 1.1 |

_designs: single_shot · prompt_chaining · reflection · agentic · agentic_grounded · agentic_reflection_


**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): inline-number incorrect-rate 6% vs 4% → Δ 3%.
2. **prompt_chaining vs reflection** (does reflection earn its cost): Δ unsupported-claims -1.6 for Δ calls 4.7 (mean iterations 2.8; converged early in 58% of runs).
3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): incorrect-rate 4% vs 39%; calls 4.0 vs 3.0; valid-pass 25% vs 0%.
4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): incorrect-rate 39% vs 0% → Δ 39%.
6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): incorrect-rate 4% vs 0%.
7. **agentic_grounded vs agentic_reflection** (reflection on the agentic row): unsupported 6.3 vs 1.1 → Δ 5.2; calls 3.4 vs 8.1.
8. **single_shot vs agentic** (orchestration at no-gate): incorrect-rate 6% vs 39%.
9. **reflection vs agentic_reflection** (orchestration at full-stack): incorrect-rate 3% vs 0%; unsupported 0.1 vs 1.1.

**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** (a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. **Whether that happens is model behavior, not structural:** the cross-model run shows it directly — Sonnet prompt_chaining cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 prompt_chaining omits them and stays on subject-company placeholders (→ 100%, verified to be full narratives, not degenerate brevity). The cap is contingent on the model interacting with the vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._

**Reading `latency_ms`:** the mean is over FRESHLY-TIMED cells only (cache-replayed cells contribute latency 0 and are excluded so they cannot dilute it); `(n=k)` is how many of the design's cells were live-timed. A row whose `n` is below the design's cell count was timed on a subset (the rest replayed from cache) — compare latency only between rows with comparable `n`, ideally one fully-live (`--refresh`) run where every row's `n` equals the full cell count.

## Worker model: `kimi-k2.6`
| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | incorrect_rate | grounding_C | unsupported | plan_valid | iters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_shot | 12 | 0 | 2.0 | 2764.3 | 875.6 | 16721.8 (n=12) | 0% | 6% | 1.8 | 2.2 | — | — |
| prompt_chaining | 12 | 0 | 4.0 | 4340.9 | 1412.5 | 29104.3 (n=12) | 8% | 2% | 1.8 | 2.0 | 0% | — |
| reflection | 10 | 2 | 8.2 | 10455.2 | 4651.4 | 69572.3 (n=10) | 30% | 0% | 0.8 | 0.7 | 0% | 2.6 |
| agentic | 12 | 0 | 4.0 | 5445.1 | 1341.9 | 30091.8 (n=12) | 0% | 24% | 9.0 | 4.3 | — | — |
| agentic_grounded | 12 | 0 | 3.7 | 5354.2 | 1237.0 | 27799.2 (n=12) | 100% | 0% | 7.3 | 4.2 | — | — |
| agentic_reflection | 10 | 2 | 8.2 | 12518.8 | 4198.1 | 61895.6 (n=10) | 30% | 10% | 1.4 | 0.5 | — | 2.8 |

**2×3 factorial — `pooled-incorrect% / unsupported-claims` (orchestration × treatment):**

| orchestration ↓ / treatment → | no gate | +gate | +gate +reflection |
|---|---|---|---|
| deterministic | 6% / 2.2 | 2% / 2.0 | 0% / 0.7 (err×2) |
| agentic | 24% / 4.3 | 0% / 4.2 | 10% / 0.5 (err×2) |

_designs: single_shot · prompt_chaining · reflection · agentic · agentic_grounded · agentic_reflection_


**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): inline-number incorrect-rate 6% vs 2% → Δ 4%.
2. **prompt_chaining vs reflection** (does reflection earn its cost): Δ unsupported-claims -1.3 for Δ calls 4.2 (mean iterations 2.6; converged early in 40% of runs).
3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): incorrect-rate 2% vs 24%; calls 4.0 vs 4.0; valid-pass 8% vs 0%.
4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): incorrect-rate 24% vs 0% → Δ 24%.
6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): incorrect-rate 2% vs 0%.
7. **agentic_grounded vs agentic_reflection** (reflection on the agentic row): unsupported 4.2 vs 0.5 → Δ 3.7; calls 3.7 vs 8.2.
8. **single_shot vs agentic** (orchestration at no-gate): incorrect-rate 6% vs 24%.
9. **reflection vs agentic_reflection** (orchestration at full-stack): incorrect-rate 0% vs 10%; unsupported 0.7 vs 0.5.

**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** (a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. **Whether that happens is model behavior, not structural:** the cross-model run shows it directly — Sonnet prompt_chaining cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 prompt_chaining omits them and stays on subject-company placeholders (→ 100%, verified to be full narratives, not degenerate brevity). The cap is contingent on the model interacting with the vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._

**Reading `latency_ms`:** the mean is over FRESHLY-TIMED cells only (cache-replayed cells contribute latency 0 and are excluded so they cannot dilute it); `(n=k)` is how many of the design's cells were live-timed. A row whose `n` is below the design's cell count was timed on a subset (the rest replayed from cache) — compare latency only between rows with comparable `n`, ideally one fully-live (`--refresh`) run where every row's `n` equals the full cell count.

## Worker model: `minimax-m3`
| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | incorrect_rate | grounding_C | unsupported | plan_valid | iters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_shot | 12 | 0 | 2.0 | 3009.6 | 1548.0 | 29012.7 (n=12) | 0% | 8% | 1.6 | 2.6 | — | — |
| prompt_chaining | 12 | 0 | 4.0 | 4983.6 | 5388.0 | 108611.9 (n=12) | 58% | 0% | 1.7 | 2.2 | 67% | — |
| reflection | 7 | 5 | 8.1 | 11800.6 | 16149.9 | 297334.9 (n=7) | 57% | 0% | 0.4 | 0.4 | 71% | 2.6 |
| agentic | 12 | 0 | 3.0 | 5954.2 | 1966.8 | 35006.9 (n=12) | 0% | 27% | 7.1 | 5.7 | — | — |
| agentic_grounded | 12 | 0 | 3.0 | 6720.7 | 2645.5 | 50417.8 (n=12) | 67% | 9% | 11.1 | 6.0 | — | — |
| agentic_reflection | 3 | 9 | 8.0 | 16272.0 | 15234.0 | 264097.3 (n=3) | 100% | 0% | 3.3 | 0.0 | — | 3.0 |

**2×3 factorial — `pooled-incorrect% / unsupported-claims` (orchestration × treatment):**

| orchestration ↓ / treatment → | no gate | +gate | +gate +reflection |
|---|---|---|---|
| deterministic | 8% / 2.6 | 0% / 2.2 | 0% / 0.4 (err×5) |
| agentic | 27% / 5.7 | 9% / 6.0 | 0% / 0.0 (err×9) |

_designs: single_shot · prompt_chaining · reflection · agentic · agentic_grounded · agentic_reflection_


**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): inline-number incorrect-rate 8% vs 0% → Δ 8%.
2. **prompt_chaining vs reflection** (does reflection earn its cost): Δ unsupported-claims -1.8 for Δ calls 4.1 (mean iterations 2.6; converged early in 71% of runs).
3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): incorrect-rate 0% vs 27%; calls 4.0 vs 3.0; valid-pass 58% vs 0%.
4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): incorrect-rate 27% vs 9% → Δ 17%.
6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): incorrect-rate 0% vs 9%.
7. **agentic_grounded vs agentic_reflection** (reflection on the agentic row): unsupported 6.0 vs 0.0 → Δ 6.0; calls 3.0 vs 8.0.
8. **single_shot vs agentic** (orchestration at no-gate): incorrect-rate 8% vs 27%.
9. **reflection vs agentic_reflection** (orchestration at full-stack): incorrect-rate 0% vs 0%; unsupported 0.4 vs 0.0.

**Reading `valid_pass`:** the 15 placeholder field-ids cover only the *subject company's* own metrics (revenue, EV/EBITDA, P/E, …). They do NOT cover **comparable-company multiples** (a peer's `15.2x`) or **transaction/deal values** (`$3.2B`), which live in payload tables, not the placeholder vocabulary. So a placeholder design's `valid_pass` is depressed *only when the narrative chooses to cite a comp/deal* — there is no placeholder for it, so it leaks inline. **Whether that happens is model behavior, not structural:** the cross-model run shows it directly — Sonnet prompt_chaining cites peer multiples and deal values (→ leaks → 17%), while glm-5.1 prompt_chaining omits them and stays on subject-company placeholders (→ 100%, verified to be full narratives, not degenerate brevity). The cap is contingent on the model interacting with the vocabulary gap. `single_shot` (0%) leaks by design (inline numbers, the control); `agentic` (0%) leaks because it writes numbers inline AND hallucinates. _Design rec (out of scope here): extend the placeholder vocabulary to table-sourced figures so a model CAN cite a comp without leaking._

**Reading `latency_ms`:** the mean is over FRESHLY-TIMED cells only (cache-replayed cells contribute latency 0 and are excluded so they cannot dilute it); `(n=k)` is how many of the design's cells were live-timed. A row whose `n` is below the design's cell count was timed on a subset (the rest replayed from cache) — compare latency only between rows with comparable `n`, ideally one fully-live (`--refresh`) run where every row's `n` equals the full cell count.

## Worker model: `qwen3.5:397b`
| design | n | err | calls | in_tok | out_tok | latency_ms | valid_pass | incorrect_rate | grounding_C | unsupported | plan_valid | iters |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_shot | 12 | 0 | 2.0 | 2839.8 | 928.7 | 13315.2 (n=12) | 0% | 5% | 2.4 | 2.7 | — | — |
| prompt_chaining | 12 | 0 | 4.0 | 4460.8 | 1734.7 | 29402.3 (n=12) | 25% | 3% | 2.4 | 2.6 | 75% | — |
| reflection | 11 | 1 | 8.1 | 10763.7 | 3492.7 | 55935.4 (n=11) | 9% | 3% | 1.0 | 1.0 | 73% | 2.5 |
| agentic | 12 | 0 | 4.0 | 7281.5 | 1399.2 | 24551.3 (n=12) | 0% | 24% | 5.0 | 3.1 | — | — |
| agentic_grounded | 12 | 0 | 4.0 | 7868.7 | 1555.0 | 27949.2 (n=12) | 100% | 0% | 8.7 | 4.1 | — | — |
| agentic_reflection | 12 | 0 | 7.8 | 14196.3 | 4113.8 | 61949.9 (n=12) | 75% | 0% | 2.3 | 0.6 | — | 2.4 |

**2×3 factorial — `pooled-incorrect% / unsupported-claims` (orchestration × treatment):**

| orchestration ↓ / treatment → | no gate | +gate | +gate +reflection |
|---|---|---|---|
| deterministic | 5% / 2.7 | 3% / 2.6 | 3% / 1.0 (err×1) |
| agentic | 24% / 3.1 | 0% / 4.1 | 0% / 0.6 |

_designs: single_shot · prompt_chaining · reflection · agentic · agentic_grounded · agentic_reflection_


**Within-model comparisons** (valid only within a fixed model):
1. **single_shot vs prompt_chaining** (headline — what placeholder discipline buys): inline-number incorrect-rate 5% vs 3% → Δ 2%.
2. **prompt_chaining vs reflection** (does reflection earn its cost): Δ unsupported-claims -1.6 for Δ calls 4.1 (mean iterations 2.5; converged early in 55% of runs).
3. **prompt_chaining vs agentic** (LLM orchestration cost/reliability): incorrect-rate 3% vs 24%; calls 4.0 vs 4.0; valid-pass 25% vs 0%.
4. **agentic vs agentic_grounded** (what the hard rail buys, orchestration fixed): incorrect-rate 24% vs 0% → Δ 24%.
6. **prompt_chaining vs agentic_grounded** (orchestration effect, rail fixed): incorrect-rate 3% vs 0%.
7. **agentic_grounded vs agentic_reflection** (reflection on the agentic row): unsupported 4.1 vs 0.6 → Δ 3.5; calls 4.0 vs 7.8.
8. **single_shot vs agentic** (orchestration at no-gate): incorrect-rate 5% vs 24%.
9. **reflection vs agentic_reflection** (orchestration at full-stack): incorrect-rate 3% vs 0%; unsupported 1.0 vs 0.6.

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
- **agentic_reflection / claude-sonnet-4-6 / ACME**: number leak: 15.2x, 18.1x, 14.0x; 3 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / MEGA**: 4 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / THIN**: 1 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / LOSS**: 8 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / PRIV**: number leak: $45
- **agentic_reflection / claude-sonnet-4-6 / BANK**: bad placeholders: transactions_value; 6 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / NOTX**: 2 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / MERG**: 2 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / ADRC**: number leak: 9.8x, 10.2x, 8.9x; 9 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / CONG**: 12 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / HYPR**: 11 hallucinated sentence(s)
- **agentic_reflection / claude-sonnet-4-6 / AMBG**: number leak: $520; 5 hallucinated sentence(s)
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
- **agentic_reflection / glm-5.1:cloud / ACME**: number leak: $3.2, 15.2x, 14.0x, 18.1x
- **agentic_reflection / glm-5.1:cloud / MEGA**: number leak: $12.0, $8.5
- **agentic_reflection / glm-5.1:cloud / LOSS**: 1 hallucinated sentence(s)
- **agentic_reflection / glm-5.1:cloud / PRIV**: bad placeholders: transactions_0_value
- **agentic_reflection / glm-5.1:cloud / BANK**: bad placeholders: transaction_value_0
- **agentic_reflection / glm-5.1:cloud / NOTX**: bad placeholders: comparables[0].ev_ebitda, comparables[1].ev_ebitda, comparables[2].ev_ebitda, net_debt_ltm; 1 hallucinated sentence(s)
- **agentic_reflection / glm-5.1:cloud / MERG**: 2 hallucinated sentence(s)
- **agentic_reflection / glm-5.1:cloud / ADRC**: 11 hallucinated sentence(s)
- **agentic_reflection / glm-5.1:cloud / CONG**: 12 hallucinated sentence(s)
- **agentic_reflection / glm-5.1:cloud / HYPR**: number leak: 42.0x, 31.0x, 45.0x; 2 hallucinated sentence(s)
- **agentic_reflection / glm-5.1:cloud / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x
- **single_shot / deepseek-v4-pro / ACME**: number leak: $42.3, $14.5, $11.6, $8.8, $5.0; 1 hallucinated sentence(s)
- **single_shot / deepseek-v4-pro / MEGA**: number leak: $1,680.0, $410.0, $230.0, $120.0, $80.0; 1 hallucinated sentence(s)
- **single_shot / deepseek-v4-pro / THIN**: number leak: $630, $132, $102, $70, $200; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / deepseek-v4-pro / LOSS**: number leak: $4.0, $580, $780, $920, $610; 5 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / deepseek-v4-pro / PRIV**: number leak: $325, $82, $63, $45, $70; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / deepseek-v4-pro / BANK**: number leak: $10.9, $2.7, $45.00, $73.0, $18.0; 1 incorrect inline number(s); 4 hallucinated sentence(s)
- **single_shot / deepseek-v4-pro / NOTX**: number leak: $8.2, $2.3, $1.4, $2.0, $3.5; 2 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / deepseek-v4-pro / MERG**: number leak: $21.5, $5.0, $3.9, $2.8, $8.0; 3 incorrect inline number(s)
- **single_shot / deepseek-v4-pro / ADRC**: number leak: 8.5%, 26.4%, 14.8x, 3.1x, 9.5x; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / deepseek-v4-pro / CONG**: number leak: $52.0, $10.2, $5.7, $18.0, $12.0; 1 incorrect inline number(s)
- **single_shot / deepseek-v4-pro / HYPR**: number leak: $7.4, $680, $490, $310, $3.0; 1 hallucinated sentence(s)
- **single_shot / deepseek-v4-pro / AMBG**: number leak: $3.0, $720, $402, $1.2, $800; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / ACME**: number leak: $3.2, 15.2x, 18.1x; 6 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / MEGA**: number leak: $12.0, $8.5; 3 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / THIN**: 1 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / LOSS**: plan invalid: 3 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e; 2 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / PRIV**: plan invalid: 7 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'm; number leak: $45; 2 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / BANK**: plan invalid: 5 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e; number leak: $1.8; 3 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / NOTX**: number leak: 8.1x, 9.2x; 2 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / MERG**: number leak: $2.8, $1.9, $3.4, $1.6, $2.2; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / ADRC**: number leak: 9.8x, 10.2x, 8.9x; 1 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / CONG**: bad placeholders: HVMH_ev_ebitda, INPU_ev_ebitda, CLSL_ev_ebitda, date_2024_11_10, value_2024_11_10
- **prompt_chaining / deepseek-v4-pro / HYPR**: number leak: $380, $210, 42.0x, 31.0x; 3 hallucinated sentence(s)
- **prompt_chaining / deepseek-v4-pro / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x; 3 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / ACME**: number leak: $312.50, $250,000, $241,500, $13,500, $5,000; 9 incorrect inline number(s); 13 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / MEGA**: number leak: $400, $2.0, $1.96, $120, $80; 16 incorrect inline number(s); 9 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / THIN**: number leak: $8.00, $800, $950, $150, $200; 13 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / LOSS**: number leak: $7.00, $3,500, $4,400, $2,800, $4,000; 9 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / PRIV**: number leak: $180, $310, $325, $42, $78; 14 incorrect inline number(s); 9 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / BANK**: number leak: $45.00, $45.0, $2.7, $11.4, $2.85; 6 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / NOTX**: number leak: $72.00, $18.0, $19.5, $2.0, $3.5; 10 incorrect inline number(s); 12 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / MERG**: number leak: $140.00, $35.0, $4.5, $8.0, $3.5; 6 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / ADRC**: number leak: 9%, 25.0%, 26.4%, 8.5%, 9.5x; 15 incorrect inline number(s); 16 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / CONG**: number leak: $13.1, $4.2, $6.8, $52.0, $50.0; 7 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / HYPR**: number leak: $56.00, $28.0, $25.5, $7.4, $4.5; 8 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic / deepseek-v4-pro / AMBG**: number leak: $26.00, $6,500, $6,900, $2,950, $720; 10 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / ACME**: number leak: $180,000, $320,000, $95,000, $46,000, $16,000; 6 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / MEGA**: number leak: 3.7%, 14%, 1,680,000, 1,620,000; 9 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / THIN**: number leak: 3.3%; 7 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / LOSS**: number leak: 3.9%, 4,000, 3,850; 13 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / PRIV**: number leak: 4.84%, 25%; 10 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / BANK**: number leak: 3.81%, 8%, 10,900, 2,700, 73,000; 17 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / NOTX**: number leak: $500, 3.8%, 12.9%, 12.86%, 18%; 1 incorrect inline number(s); 11 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / MERG**: number leak: $20,100, $16,400, 22.56%, 25%; 2 incorrect inline number(s); 15 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / ADRC**: number leak: 3.92%, 8.5%, 3.9%, 5,300, 5,100; 11 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / CONG**: number leak: $52,000, $50,000, $6.0, $4.2, $6.8; 5 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / HYPR**: number leak: $35,000, $22,000, $41,000, 65%, 42.0x; bad placeholders: revenue_next_fy, ebitda_next_fy, eps_next_fy; 3 incorrect inline number(s); 15 hallucinated sentence(s)
- **agentic_grounded / deepseek-v4-pro / AMBG**: number leak: $7,200, $5,900, $8,400, $3,200, $790; 7 incorrect inline number(s); 17 hallucinated sentence(s)
- **reflection / deepseek-v4-pro / ACME**: number leak: 15.2x, 18.1x, 14.0x; 5 hallucinated sentence(s)
- **reflection / deepseek-v4-pro / MEGA**: 1 hallucinated sentence(s)
- **reflection / deepseek-v4-pro / THIN**: 1 hallucinated sentence(s)
- **reflection / deepseek-v4-pro / LOSS**: plan invalid: 3 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e; 1 hallucinated sentence(s)
- **reflection / deepseek-v4-pro / PRIV**: plan invalid: 7 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'm; number leak: $45, 9.8x, 11.2x; 1 hallucinated sentence(s)
- **reflection / deepseek-v4-pro / BANK**: plan invalid: 5 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e
- **reflection / deepseek-v4-pro / NOTX**: number leak: 8.1x, 9.2x, 7.8x; 1 hallucinated sentence(s)
- **reflection / deepseek-v4-pro / MERG**: number leak: $2.8, $1.9, $3.4, $1.6, $2.2; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **reflection / deepseek-v4-pro / ADRC**: number leak: 9.8x, 10.2x, 8.9x
- **reflection / deepseek-v4-pro / CONG**: bad placeholders: HVMH_ev_ebitda, INPU_ev_ebitda, CLSL_ev_ebitda, date_2024_11_10, value_2024_11_10
- **reflection / deepseek-v4-pro / HYPR**: number leak: $380, $210, 42.0x, 31.0x, 45.0x; 1 hallucinated sentence(s)
- **reflection / deepseek-v4-pro / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x
- **agentic_reflection / deepseek-v4-pro / ACME**: number leak: 15.2x, 18.1x, 14.0x; 1 hallucinated sentence(s)
- **agentic_reflection / deepseek-v4-pro / MEGA**: number leak: $12.0, $8.5
- **agentic_reflection / deepseek-v4-pro / THIN**: 1 hallucinated sentence(s)
- **agentic_reflection / deepseek-v4-pro / LOSS**: 4 hallucinated sentence(s)
- **agentic_reflection / deepseek-v4-pro / PRIV**: number leak: $45, 25%; 1 hallucinated sentence(s)
- **agentic_reflection / deepseek-v4-pro / BANK**: number leak: $1.8, 38,000, 52,000, 41,000; 3 hallucinated sentence(s)
- **agentic_reflection / deepseek-v4-pro / NOTX**: number leak: 8.1x, 9.2x, 7.8x
- **agentic_reflection / deepseek-v4-pro / MERG**: 2 hallucinated sentence(s)
- **agentic_reflection / deepseek-v4-pro / ADRC**: number leak: 9.8x, 10.2x, 8.9x; 2 hallucinated sentence(s)
- **agentic_reflection / deepseek-v4-pro / CONG**: number leak: $6.0, $4.2, $6.8, 19.6%, 6.8x; 1 incorrect inline number(s)
- **agentic_reflection / deepseek-v4-pro / HYPR**: number leak: $35,000, $22,000, $41,000, 42.0x, 31.0x; bad placeholders: revenue_next_fy, ebitda_next_fy, eps_next_fy; 3 incorrect inline number(s); 11 hallucinated sentence(s)
- **agentic_reflection / deepseek-v4-pro / AMBG**: number leak: $7,200, $5,900, $8,400, $3,200, $790; 6 incorrect inline number(s); 9 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / ACME**: number leak: $42.3, $14.5, $11.6, $8.8, $13.5; 2 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / MEGA**: number leak: $1,680.0, $410.0, $230.0, $120.0, $80.0; 2 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / THIN**: number leak: $630, $132, $102, $70, $200; 3 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / LOSS**: number leak: $4.0, $580, $780, $920, $610; 4 incorrect inline number(s)
- **single_shot / gemini-3-flash-preview / PRIV**: number leak: $325, $82, $63, $45, $70; 1 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / BANK**: number leak: $10.9, $2.7, $2.5, $73.0, $18.0; 1 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / NOTX**: number leak: $8.2, $2.3, $1.8, $1.4, $3.5; 2 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / MERG**: number leak: $21.5, $5.0, $3.9, $2.8, $2.2; 2 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / ADRC**: number leak: $5,300.0, $1,400.0, $1,110.0, $810.0, $660.0; 2 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / CONG**: number leak: $52.0, $10.2, $7.9, $5.7, $4.6; 2 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / HYPR**: number leak: $7,411.0, $680.0, $490.0, $310.0, $3,000.0; 2 hallucinated sentence(s)
- **single_shot / gemini-3-flash-preview / AMBG**: number leak: $2,950.0, $720.0, $550.0, $402.0, $1,200.0; 2 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / ACME**: 3 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / MEGA**: 2 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / THIN**: 2 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / LOSS**: 2 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / PRIV**: plan invalid: 6 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'm; 3 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / BANK**: 2 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / NOTX**: 1 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / MERG**: plan invalid: 1 validation error for RetrievalPlan
gap_decisions
  Input should be a valid list [type=list_type, input_value={'dividen; 1 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / ADRC**: 2 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / CONG**: 1 hallucinated sentence(s)
- **prompt_chaining / gemini-3-flash-preview / HYPR**: 3 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / ACME**: number leak: $250.0, $241.5, $312.50, $42.3, $41.0; 5 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / MEGA**: number leak: $2.0, $1.96, $400.00, $1.68, $1.2; 12 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / THIN**: number leak: $800.0, $950.0, $8.00, $420.0, $610.0; 5 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / LOSS**: number leak: $3,500.0, $4,400.0, $7.00, $2,800.0, $4,000.0; 7 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / PRIV**: number leak: $310.0, $180.0, $325.0, $82.0, $42.0; 6 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / BANK**: number leak: $45.0, $10,900, $10,500, $8,200, $2,700; 7 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / NOTX**: number leak: $72.00, $18,000, $19,500, $8,200, $2,300; 6 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / MERG**: number leak: $35.0, $39.5, $140.00, $21.5, $5.0; 2 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / ADRC**: number leak: 8.5%, 9.5x, 14.8x, 9.8x, 10.2x; 5 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / CONG**: number leak: $85.0, $91.0, $170.0, $52.0, $46.5; 4 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / HYPR**: number leak: $28.0, $25.5, $56.00, $7,411, $4,492; 3 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / gemini-3-flash-preview / AMBG**: number leak: $6.5, $6.9, $26.00, $1.8, $2.8; 5 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / ACME**: 4 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / MEGA**: 4 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / THIN**: 4 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / LOSS**: 6 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / PRIV**: 5 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / BANK**: 5 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / NOTX**: 4 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / MERG**: 6 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / ADRC**: 6 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / CONG**: 19 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / HYPR**: 2 hallucinated sentence(s)
- **agentic_grounded / gemini-3-flash-preview / AMBG**: 6 hallucinated sentence(s)
- **reflection / gemini-3-flash-preview / ACME**: 3 hallucinated sentence(s)
- **reflection / gemini-3-flash-preview / THIN**: ERROR: JSONDecodeError('Unterminated string starting at: line 12 column 15 (char 422)')
- **reflection / gemini-3-flash-preview / LOSS**: 2 hallucinated sentence(s)
- **reflection / gemini-3-flash-preview / PRIV**: plan invalid: 6 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'm; 1 hallucinated sentence(s)
- **reflection / gemini-3-flash-preview / BANK**: 2 hallucinated sentence(s)
- **reflection / gemini-3-flash-preview / NOTX**: 1 hallucinated sentence(s)
- **reflection / gemini-3-flash-preview / MERG**: plan invalid: 1 validation error for RetrievalPlan
gap_decisions
  Input should be a valid list [type=list_type, input_value={'dividen
- **reflection / gemini-3-flash-preview / ADRC**: ERROR: JSONDecodeError('Unterminated string starting at: line 16 column 15 (char 467)')
- **reflection / gemini-3-flash-preview / CONG**: ERROR: JSONDecodeError('Unterminated string starting at: line 12 column 15 (char 519)')
- **agentic_reflection / gemini-3-flash-preview / ACME**: ERROR: JSONDecodeError('Unterminated string starting at: line 16 column 15 (char 596)')
- **agentic_reflection / gemini-3-flash-preview / MEGA**: ERROR: JSONDecodeError("Expecting ',' delimiter: line 17 column 19 (char 538)")
- **agentic_reflection / gemini-3-flash-preview / THIN**: 1 hallucinated sentence(s)
- **agentic_reflection / gemini-3-flash-preview / LOSS**: ERROR: JSONDecodeError("Expecting ',' delimiter: line 21 column 19 (char 523)")
- **agentic_reflection / gemini-3-flash-preview / PRIV**: ERROR: JSONDecodeError('Unterminated string starting at: line 16 column 15 (char 525)')
- **agentic_reflection / gemini-3-flash-preview / BANK**: ERROR: JSONDecodeError('Unterminated string starting at: line 16 column 15 (char 583)')
- **agentic_reflection / gemini-3-flash-preview / NOTX**: ERROR: JSONDecodeError('Unterminated string starting at: line 21 column 3 (char 554)')
- **agentic_reflection / gemini-3-flash-preview / MERG**: ERROR: JSONDecodeError('Unterminated string starting at: line 17 column 7 (char 668)')
- **agentic_reflection / gemini-3-flash-preview / ADRC**: ERROR: JSONDecodeError('Unterminated string starting at: line 17 column 7 (char 524)')
- **agentic_reflection / gemini-3-flash-preview / CONG**: ERROR: JSONDecodeError('Expecting property name enclosed in double quotes: line 1 column 2 (char 1)')
- **agentic_reflection / gemini-3-flash-preview / HYPR**: ERROR: JSONDecodeError('Unterminated string starting at: line 16 column 15 (char 545)')
- **agentic_reflection / gemini-3-flash-preview / AMBG**: ERROR: JSONDecodeError('Unterminated string starting at: line 20 column 7 (char 636)')
- **single_shot / minimax-m3 / ACME**: number leak: $42.3, $14.5, $11.6, $8.8, $7.5; 1 hallucinated sentence(s)
- **single_shot / minimax-m3 / MEGA**: number leak: $1,680.0, $410.0, $332.0, $230.0, $188.0; 1 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / minimax-m3 / THIN**: number leak: $630, $132, $102, $70, $52; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / minimax-m3 / LOSS**: number leak: $4.0, $580, $780, $920, $610; 5 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / minimax-m3 / PRIV**: number leak: $325, $82, $63, $45, $32; 6 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / minimax-m3 / BANK**: number leak: $10.9, $2.7, $2.5, $73.0, $18.0; 3 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / minimax-m3 / NOTX**: number leak: $8.2, $2.3, $1.8, $1.4, $1.1; 3 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / minimax-m3 / MERG**: number leak: $21.5, $5.0, $3.85, $2.8, $2.2; 2 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / minimax-m3 / ADRC**: number leak: 8.5%, 26.4%, 20.9%, 15.3%, 12.5%; 1 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / minimax-m3 / CONG**: number leak: $85.0, $170.00, $52.0, $10.2, $7.9; 1 incorrect inline number(s)
- **single_shot / minimax-m3 / HYPR**: number leak: $7.4, $680, $490, $310, $380; 1 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / minimax-m3 / AMBG**: number leak: $3.0, $720, $550, $402, $310; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / ACME**: 1 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / MEGA**: number leak: $12.0, $8.5, 3.9x, 6.1x; 3 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / THIN**: 2 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / LOSS**: plan invalid: 2 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e
- **prompt_chaining / minimax-m3 / PRIV**: plan invalid: 6 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'm; 2 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / BANK**: plan invalid: 5 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e; 2 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / NOTX**: number leak: 7.8x, 9.2x, 8.1x; 1 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / MERG**: 2 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / ADRC**: number leak: 26%, 9.8x, 10.2x, 8.9x, 9.5x; bad placeholders: transactions:acquirer, transactions:date, transactions:value; 1 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / CONG**: plan invalid: 4 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'field': 'se; 2 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / HYPR**: number leak: $380, $210, 42.0x, 31.0x, 45.0x; 3 hallucinated sentence(s)
- **prompt_chaining / minimax-m3 / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x; 1 hallucinated sentence(s)
- **agentic / minimax-m3 / ACME**: number leak: $312.50, $250,000, $241,500, $13,500, $5,000; 5 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / minimax-m3 / MEGA**: number leak: $400, $2.0, $1.96, $1.20, $1.62; 17 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic / minimax-m3 / THIN**: number leak: $8.00, $800, $950, $50, $200; 6 incorrect inline number(s); 3 hallucinated sentence(s)
- **agentic / minimax-m3 / LOSS**: number leak: $7.00, $3,500, $4,400, $2,800, $4,000; 14 incorrect inline number(s); 9 hallucinated sentence(s)
- **agentic / minimax-m3 / PRIV**: number leak: $310, $325, $180, $42, $82; 10 incorrect inline number(s); 9 hallucinated sentence(s)
- **agentic / minimax-m3 / BANK**: number leak: $45.00, $45.0, $8.2, $10.5, $10.9; 8 incorrect inline number(s); 9 hallucinated sentence(s)
- **agentic / minimax-m3 / NOTX**: number leak: $72.00, $18.0, $19.5, $2.0, $3.5; 6 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / minimax-m3 / MERG**: number leak: $140.00, $35.0, $39.5, $9.5, $20.1; 7 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / minimax-m3 / ADRC**: number leak: 10.3%, 8.5%, 26%, 9.5x, 2.5x; 10 hallucinated sentence(s)
- **agentic / minimax-m3 / CONG**: number leak: $170.00, $85.0, $91.0, $6.0, $18.0; 8 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / minimax-m3 / HYPR**: number leak: $56.00, $28.0, $25.5, $1.0, $7.4; 6 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / minimax-m3 / AMBG**: number leak: $26.00, $6.5, $6.9, $1.8, $2.95; 6 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / ACME**: 11 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / MEGA**: 10 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / THIN**: 7 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / LOSS**: 9 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / PRIV**: bad placeholders: date: 2024-07-12, field N/A — omitted per output rule; 14 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / BANK**: number leak: 12 bps; bad placeholders: revenue_next_fy, eps_next_fy; 11 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / NOTX**: 9 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / MERG**: 14 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / ADRC**: number leak: 8.5%; 16 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / CONG**: 6 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / HYPR**: 15 hallucinated sentence(s)
- **agentic_grounded / minimax-m3 / AMBG**: number leak: $740, 3%; bad placeholders: earnings_sentiment; 1 incorrect inline number(s); 11 hallucinated sentence(s)
- **reflection / minimax-m3 / MEGA**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **reflection / minimax-m3 / LOSS**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **reflection / minimax-m3 / PRIV**: plan invalid: 6 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'm; 1 hallucinated sentence(s)
- **reflection / minimax-m3 / BANK**: ERROR: JSONDecodeError('Unterminated string starting at: line 9 column 15 (char 567)')
- **reflection / minimax-m3 / NOTX**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **reflection / minimax-m3 / MERG**: number leak: 8.5x, 7.2x, 9.1x
- **reflection / minimax-m3 / ADRC**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **reflection / minimax-m3 / CONG**: plan invalid: 4 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'field': 'se
- **reflection / minimax-m3 / HYPR**: number leak: 42.0x, 31.0x, 45.0x; 1 hallucinated sentence(s)
- **reflection / minimax-m3 / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x; 1 hallucinated sentence(s)
- **agentic_reflection / minimax-m3 / ACME**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **agentic_reflection / minimax-m3 / MEGA**: 10 hallucinated sentence(s)
- **agentic_reflection / minimax-m3 / THIN**: ERROR: JSONDecodeError('Expecting value: line 6 column 7 (char 163)')
- **agentic_reflection / minimax-m3 / PRIV**: ERROR: JSONDecodeError('Unterminated string starting at: line 79 column 5 (char 4865)')
- **agentic_reflection / minimax-m3 / BANK**: ERROR: JSONDecodeError('Unterminated string starting at: line 73 column 5 (char 4366)')
- **agentic_reflection / minimax-m3 / MERG**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **agentic_reflection / minimax-m3 / ADRC**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **agentic_reflection / minimax-m3 / CONG**: ERROR: JSONDecodeError('Unterminated string starting at: line 60 column 16 (char 4311)')
- **agentic_reflection / minimax-m3 / HYPR**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **agentic_reflection / minimax-m3 / AMBG**: ERROR: JSONDecodeError("Expecting ',' delimiter: line 57 column 19 (char 2547)")
- **single_shot / kimi-k2.6 / ACME**: number leak: $250.0, $312.50, $42.3, $14.5, $11.6; 3 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / MEGA**: number leak: $1,680.0, $410.0, $188.0, $230.0, $80.0; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / THIN**: number leak: $630, $132, $102, $70, $52; 1 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / LOSS**: number leak: $4.0, $580, $780, $920, $610; 4 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / PRIV**: number leak: $325, $82, $63, $45, $32; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / BANK**: number leak: $10.9, $2.7, $2.5, $73.0, $18.0; 2 incorrect inline number(s); 1 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / NOTX**: number leak: $8.2, $2.3, $1.8, $1.4, $1.1; 3 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / MERG**: number leak: $21.5, $5.0, $3.9, $2.8, $2.2; 3 incorrect inline number(s)
- **single_shot / kimi-k2.6 / ADRC**: number leak: 8.5%, 26.4%, 0.9x, 9.5x, 2.5x; 2 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / CONG**: number leak: $52.0, $10.2, $7.9, $5.7, $4.6; 2 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / HYPR**: number leak: $7.4, $680, $490, $310, $380; 2 hallucinated sentence(s)
- **single_shot / kimi-k2.6 / AMBG**: number leak: $3.0, $720, $550, $402, $800; 1 incorrect inline number(s); 4 hallucinated sentence(s)
- **prompt_chaining / kimi-k2.6 / ACME**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: $3.2, 15.2x, 18.1x, 14.0x; 2 hallucinated sentence(s)
- **prompt_chaining / kimi-k2.6 / MEGA**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: 3.9x, 6.1x; bad placeholders: transactions[0].date, transactions[0].value, transactions[1].date, transactions[1].value; 2 hallucinated sentence(s)
- **prompt_chaining / kimi-k2.6 / THIN**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple pb cannot also be in gap_decisions [type=value_erro; bad placeholders: ebitda_margin; 8 hallucinated sentence(s)
- **prompt_chaining / kimi-k2.6 / LOSS**: plan invalid: 2 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e
- **prompt_chaining / kimi-k2.6 / PRIV**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: $45, 9.8x, 11.2x; 1 hallucinated sentence(s)
- **prompt_chaining / kimi-k2.6 / BANK**: plan invalid: 5 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e; number leak: $1.8; 1 hallucinated sentence(s)
- **prompt_chaining / kimi-k2.6 / NOTX**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: 8.1x, 9.2x, 7.8x; 5 hallucinated sentence(s)
- **prompt_chaining / kimi-k2.6 / MERG**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: $2.8, $1.9, $3.4, $1.6, $2.2; 1 incorrect inline number(s)
- **prompt_chaining / kimi-k2.6 / ADRC**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: 9.8x, 10.2x, 8.9x; 2 hallucinated sentence(s)
- **prompt_chaining / kimi-k2.6 / CONG**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: $4.2, $6.8, 6.8x, 6.0x, 7.5x; 1 hallucinated sentence(s)
- **prompt_chaining / kimi-k2.6 / HYPR**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: 42.0x, 31.0x, 45.0x; bad placeholders: transactions.0.value, transactions.1.value
- **prompt_chaining / kimi-k2.6 / AMBG**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: $520, 10.1x, 8.8x, 11.3x
- **agentic / kimi-k2.6 / ACME**: number leak: $312.50, $250.0, $241.5, $42.3, $41.0; 8 incorrect inline number(s); 11 hallucinated sentence(s)
- **agentic / kimi-k2.6 / MEGA**: number leak: 7.9%, 23.3%, 24.4%, 14%, 4.8x; 11 hallucinated sentence(s)
- **agentic / kimi-k2.6 / THIN**: number leak: $8.00, $800, $950, $150, $200; 5 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / kimi-k2.6 / LOSS**: number leak: $7.00, $3,500, $4,400, $2,800, $4,000; 14 incorrect inline number(s); 13 hallucinated sentence(s)
- **agentic / kimi-k2.6 / PRIV**: number leak: $180, $325, $42, $82, $20; 11 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / kimi-k2.6 / BANK**: number leak: $45.00, $45.0, $8.2, $10.5, $10.9; 10 incorrect inline number(s); 9 hallucinated sentence(s)
- **agentic / kimi-k2.6 / NOTX**: number leak: 3.8%, 11%, 25%, 28%, 18%; 8 hallucinated sentence(s)
- **agentic / kimi-k2.6 / MERG**: number leak: $140.00, $35.0, $39.5, $21.5, $20.1; 10 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic / kimi-k2.6 / ADRC**: number leak: 39%, 26%, 8.5%, 9.5x, 2.5x; 9 hallucinated sentence(s)
- **agentic / kimi-k2.6 / CONG**: number leak: $170.00, $85.0, $91.0, $52.0, $38.0; 5 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / kimi-k2.6 / HYPR**: number leak: $7.4, $56.00, $28.0, $25.5, $2.5; 8 incorrect inline number(s); 10 hallucinated sentence(s)
- **agentic / kimi-k2.6 / AMBG**: number leak: $6.5, $6.9, $26.00, $1.8, $2.95; 7 incorrect inline number(s); 8 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / ACME**: 7 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / MEGA**: 8 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / THIN**: 2 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / LOSS**: 9 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / PRIV**: 2 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / BANK**: 8 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / NOTX**: 7 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / MERG**: 6 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / ADRC**: 6 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / CONG**: 11 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / HYPR**: 8 hallucinated sentence(s)
- **agentic_grounded / kimi-k2.6 / AMBG**: 14 hallucinated sentence(s)
- **reflection / kimi-k2.6 / ACME**: ERROR: JSONDecodeError('Unterminated string starting at: line 44 column 16 (char 1686)')
- **reflection / kimi-k2.6 / MEGA**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; bad placeholders: transactions[0].date, transactions[0].value, transactions[1].date, transactions[1].value; 2 hallucinated sentence(s)
- **reflection / kimi-k2.6 / THIN**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple pb cannot also be in gap_decisions [type=value_erro; 1 hallucinated sentence(s)
- **reflection / kimi-k2.6 / LOSS**: plan invalid: 2 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e
- **reflection / kimi-k2.6 / PRIV**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: 9.8x, 11.2x
- **reflection / kimi-k2.6 / BANK**: plan invalid: 5 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'metric': 'e; bad placeholders: transactions.0.value
- **reflection / kimi-k2.6 / NOTX**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: 8.1x, 9.2x, 7.8x
- **reflection / kimi-k2.6 / MERG**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; 4 hallucinated sentence(s)
- **reflection / kimi-k2.6 / ADRC**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: 9.8x, 10.2x, 8.9x; 1 hallucinated sentence(s)
- **reflection / kimi-k2.6 / CONG**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: 6.8x, 6.0x, 7.5x, 22.0x, 19.2x; bad placeholders: transaction_value_cloudseg, transaction_value_indusparts
- **reflection / kimi-k2.6 / HYPR**: ERROR: JSONDecodeError('Extra data: line 45 column 1 (char 2602)')
- **reflection / kimi-k2.6 / AMBG**: plan invalid: 1 validation error for RetrievalPlan
  Value error, primary_multiple ev_ebitda cannot also be in gap_decisions [type=val; number leak: $520, 10.1x, 8.8x, 11.3x
- **agentic_reflection / kimi-k2.6 / ACME**: number leak: $3.2, 15.2x, 18.1x, 14.0x
- **agentic_reflection / kimi-k2.6 / MEGA**: bad placeholders: transactions[1].value, transactions[0].value; 1 hallucinated sentence(s)
- **agentic_reflection / kimi-k2.6 / THIN**: 2 hallucinated sentence(s)
- **agentic_reflection / kimi-k2.6 / LOSS**: 6 hallucinated sentence(s)
- **agentic_reflection / kimi-k2.6 / PRIV**: ERROR: JSONDecodeError('Extra data: line 18 column 1 (char 1005)')
- **agentic_reflection / kimi-k2.6 / BANK**: bad placeholders: transactions_0_date; 1 hallucinated sentence(s)
- **agentic_reflection / kimi-k2.6 / MERG**: bad placeholders: comparables.SCUP.ev_ebitda, comparables.RLPC.ev_ebitda, comparables.BYOG.ev_ebitda; 1 hallucinated sentence(s)
- **agentic_reflection / kimi-k2.6 / ADRC**: bad placeholders: transactions.value; 1 hallucinated sentence(s)
- **agentic_reflection / kimi-k2.6 / CONG**: number leak: $6.0, 0.6x; 1 incorrect inline number(s); 1 hallucinated sentence(s)
- **agentic_reflection / kimi-k2.6 / HYPR**: number leak: 42.0x, 31.0x, 45.0x; bad placeholders: transactions[0].value, transactions[1].value; 1 hallucinated sentence(s)
- **agentic_reflection / kimi-k2.6 / AMBG**: ERROR: JSONDecodeError('Extra data: line 33 column 1 (char 3140)')
- **single_shot / qwen3.5:397b / ACME**: number leak: $42.3, $14.5, $8.8, $7.5, $13.5; 4 hallucinated sentence(s)
- **single_shot / qwen3.5:397b / MEGA**: number leak: $1,680.0, $410.0, $230.0, $188.0, $120.0; 3 hallucinated sentence(s)
- **single_shot / qwen3.5:397b / THIN**: number leak: $630, $132, $70, $50, $200; 5 hallucinated sentence(s)
- **single_shot / qwen3.5:397b / LOSS**: number leak: $4.0, $580, $920, $610, $780; 4 incorrect inline number(s)
- **single_shot / qwen3.5:397b / PRIV**: number leak: $325.0, $82.0, $63.0, $45.0, $30.0; 4 hallucinated sentence(s)
- **single_shot / qwen3.5:397b / BANK**: number leak: $10.9, $2.7, $2.5, $18.0, $73.0; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / qwen3.5:397b / NOTX**: number leak: $8.2, $2.3, $1.4, $1.1, $2.0; 2 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / qwen3.5:397b / MERG**: number leak: $21.5, $5.0, $2.8, $2.2, $3.5; 2 incorrect inline number(s)
- **single_shot / qwen3.5:397b / ADRC**: number leak: 8.5%, 26%, 9.5x, 9.8x, 10.2x; 1 incorrect inline number(s); 3 hallucinated sentence(s)
- **single_shot / qwen3.5:397b / CONG**: number leak: $52.0, $10.2, $5.7, $4.6, $12.0; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **single_shot / qwen3.5:397b / HYPR**: number leak: $7.4, $680, $310, $3.0, $500; 2 hallucinated sentence(s)
- **single_shot / qwen3.5:397b / AMBG**: number leak: $3.0, $720, $550, $402, $310; 1 incorrect inline number(s); 2 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / ACME**: number leak: $3.2, 15.2x, 18.1x; 2 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / MEGA**: number leak: $12.0, $8.5; 4 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / THIN**: 3 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / LOSS**: plan invalid: 1 validation error for RetrievalPlan
gap_decisions
  Input should be a valid list [type=list_type, input_value={'ev_ebit; 2 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / PRIV**: plan invalid: 7 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'field': 'ma; number leak: $45, 9.8x, 11.2x; 2 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / BANK**: plan invalid: 1 validation error for RetrievalPlan
gap_decisions
  Input should be a valid list [type=list_type, input_value={'ebitda_; number leak: $1.8; 3 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / NOTX**: number leak: 7.8x, 9.2x; 2 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / MERG**: number leak: $2.8, $1.9, $3.4, $1.6, 8.5x; bad placeholders: date=2025-08-22, date=2025-02-14, date=2024-10-05, date=2024-04-18; 1 incorrect inline number(s)
- **prompt_chaining / qwen3.5:397b / ADRC**: number leak: 10.2x; 4 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / CONG**: number leak: $4.2, $6.8, 6.8x, 6.0x; 3 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / HYPR**: 2 hallucinated sentence(s)
- **prompt_chaining / qwen3.5:397b / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x; 2 hallucinated sentence(s)
- **agentic / qwen3.5:397b / ACME**: number leak: $312.50, $250.0, $241.5, $42.3, $14.5; 2 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / qwen3.5:397b / MEGA**: number leak: $400.00, $2.0, $1.96, $1.68, $410,000,; 12 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / qwen3.5:397b / THIN**: number leak: $8.00, $800.0, $950.0, $630.0, $420.0; 2 incorrect inline number(s); 3 hallucinated sentence(s)
- **agentic / qwen3.5:397b / LOSS**: number leak: $7.00, $3,500, $4,400, $4,000, $580; 7 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / qwen3.5:397b / PRIV**: number leak: $325.0, $180.0, $310.0, $82.0, $45.0; 4 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / qwen3.5:397b / BANK**: number leak: $45.00, $45.0, $10.9, $8.2, $2.7; 6 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic / qwen3.5:397b / NOTX**: number leak: $72.00, $18,000, $19,500, $8,200, $7,000; 5 incorrect inline number(s); 7 hallucinated sentence(s)
- **agentic / qwen3.5:397b / MERG**: number leak: $140.00, $35.0, $39.5, $21.5, $5.0; 3 incorrect inline number(s); 4 hallucinated sentence(s)
- **agentic / qwen3.5:397b / ADRC**: number leak: 8.5%, 9.5x, 14.8x, 9.8x, 10.2x; 4 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / qwen3.5:397b / CONG**: number leak: $170.00, $85.0, $91.0, $52.0, $10.2; 5 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / qwen3.5:397b / HYPR**: number leak: $56.00, $28.0, $25.5, $7.41, $4.49; 3 incorrect inline number(s); 5 hallucinated sentence(s)
- **agentic / qwen3.5:397b / AMBG**: number leak: $26.00, $6,500, $6,900, $2,950, $2,450; 5 incorrect inline number(s); 6 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / ACME**: 11 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / MEGA**: 4 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / THIN**: 17 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / LOSS**: 5 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / PRIV**: 9 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / BANK**: 6 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / NOTX**: 3 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / MERG**: 10 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / ADRC**: 10 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / CONG**: 11 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / HYPR**: 10 hallucinated sentence(s)
- **agentic_grounded / qwen3.5:397b / AMBG**: 8 hallucinated sentence(s)
- **reflection / qwen3.5:397b / ACME**: number leak: $3.2, 15.2x, 18.1x; 1 hallucinated sentence(s)
- **reflection / qwen3.5:397b / MEGA**: number leak: $12.0, $8.5; 5 hallucinated sentence(s)
- **reflection / qwen3.5:397b / THIN**: ERROR: ValueError('judge: no text block in LLM response (stop_reason=end_turn)')
- **reflection / qwen3.5:397b / LOSS**: plan invalid: 1 validation error for RetrievalPlan
gap_decisions
  Input should be a valid list [type=list_type, input_value={'ev_ebit; 1 hallucinated sentence(s)
- **reflection / qwen3.5:397b / PRIV**: plan invalid: 7 validation errors for RetrievalPlan
gap_decisions.0.field_id
  Field required [type=missing, input_value={'field': 'ma; number leak: $45, 9.8x, 11.2x
- **reflection / qwen3.5:397b / BANK**: plan invalid: 1 validation error for RetrievalPlan
gap_decisions
  Input should be a valid list [type=list_type, input_value={'ebitda_; number leak: $1.8; 1 hallucinated sentence(s)
- **reflection / qwen3.5:397b / NOTX**: number leak: 7.8x, 9.2x; 1 hallucinated sentence(s)
- **reflection / qwen3.5:397b / MERG**: number leak: $2.8, $1.9, $3.4, $1.6, 8.5x; 1 incorrect inline number(s)
- **reflection / qwen3.5:397b / ADRC**: number leak: 9.8x, 10.2x, 8.9x; 1 hallucinated sentence(s)
- **reflection / qwen3.5:397b / CONG**: number leak: $4.2, $6.8, 6.8x, 6.0x
- **reflection / qwen3.5:397b / HYPR**: number leak: 42.0x, 31.0x, 45.0x
- **reflection / qwen3.5:397b / AMBG**: number leak: $520, 10.1x, 8.8x, 11.3x; 1 hallucinated sentence(s)
- **agentic_reflection / qwen3.5:397b / ACME**: number leak: 15.2x, 18.1x, 14.0x; 1 hallucinated sentence(s)
- **agentic_reflection / qwen3.5:397b / MEGA**: 1 hallucinated sentence(s)
- **agentic_reflection / qwen3.5:397b / THIN**: 15 hallucinated sentence(s)
- **agentic_reflection / qwen3.5:397b / PRIV**: 2 hallucinated sentence(s)
- **agentic_reflection / qwen3.5:397b / BANK**: 3 hallucinated sentence(s)
- **agentic_reflection / qwen3.5:397b / ADRC**: number leak: 9.8x, 10.2x, 8.9x; 1 hallucinated sentence(s)
- **agentic_reflection / qwen3.5:397b / CONG**: 3 hallucinated sentence(s)
- **agentic_reflection / qwen3.5:397b / AMBG**: number leak: $520; 2 hallucinated sentence(s)

## Run manifest
- fixture_set_version: 1
- judge: claude-sonnet-4-6
- workers: claude-sonnet-4-6, glm-5.1:cloud, deepseek-v4-pro, gemini-3-flash-preview, minimax-m3, kimi-k2.6, qwen3.5:397b
- prompt_hashes: 9 prompt files hashed