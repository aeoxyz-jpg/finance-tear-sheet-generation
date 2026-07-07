# Correction (2026-07-07): the "agentic fabrication" headline was a grading-scope artifact

The benchmark reports in this directory tree originally supported the claim that the `agentic`
design "writes 24–39% of its inline numbers wrong". A trace-level re-audit shows that claim is
false as a statement about model behavior. This document is the public record of the correction;
the affected `report.md` files carry a banner pointing here. The report tables themselves are
left unedited (they are raw benchmark output).

## What was wrong

`common/number_check.py` builds its "correct" number pool only from `build_payload()`'s
15-field LTM contract (`common/payload.py`), and `common/eval.py`'s judge receives the same
narrow payload as its grounding reference. That matches what the deterministic designs
(`single_shot`, `prompt_chaining`) are shown. But the `agentic` designs' data tools
(`designs/agentic_tools.py` → `fakedata/store.py`) return the full fixture — 5-year financial
history, comparables with market caps, transactions, consensus estimates. The agent legitimately
cited that data; the grader, scoped to 15 fields, counted the citations as "incorrect" and the
judge counted the corresponding prose as ungrounded. The design-vs-design comparison therefore
measured vocabulary asymmetry, not fabrication.

## Re-measurement

Every `number_check` "incorrect" token in every agentic cell was re-matched against that cell's
own recorded tool outputs (exact values, bounded power-of-1000 scale variants, sign-insensitive,
plus a small set of manually verified analyst formulas such as net debt = debt − cash and
implied EV = peer multiple × LTM EBITDA). Matcher validation: the `single_shot` control (no
tools) classifies 20/20 of its flagged tokens as matching nothing (0% false positives);
cross-company null tests bound the loose layers at a 20–24% false-positive ceiling and the
strict exact-scale layer at 5.8%.

| model · run | flagged "incorrect" | tool-backed | derived | unsupported | published rate | genuine-fabrication rate |
|---|---:|---:|---:|---:|---:|---:|
| Sonnet · run-anthropic-ollama | 177 | 93.2% | 6.8% | 0.0% | 28.2% | 0.0% |
| glm-5.1 · run-anthropic-ollama | 103 | 90.3% | 9.7% | 0.0% | 39.1% | 0.0% |
| Sonnet · run-2x3 | 177 | 93.2% | 6.8% | 0.0% | 28.2% | 0.0% |
| deepseek-v4-pro · run-2x3 | 123 | 91.9% | 8.1% | 0.0% | 30.8% | 0.0% |
| gemini-3-flash · run-2x3 | 62 | 100% | 0% | 0.0% | 26.7% | 0.0% |
| glm-5.1 · run-2x3 | 103 | 90.3% | 9.7% | 0.0% | 39.1% | 0.0% |
| kimi-k2.6 · run-2x3 | 78 | 92.3% | 7.7% | 0.0% | 24.7% | 0.0% |
| minimax-m3 · run-2x3 | 93 | 88.2% | 10.8% | 1.1% | 27.1% | 0.4% |
| qwen3.5:397b · run-2x3 | 58 | 100% | 0% | 0.0% | 24.4% | 0.0% |

The classifier and its full per-cell output are included for transparency in
`results/correction-2026-07-07/` (`classify.py`, `final_report.json`). Note the per-cell result
JSONs it reads (full traces incl. tool outputs) are not committed to this repository; the
aggregated `final_report.json` carries the per-cell classification the table above summarizes.

The two flagship examples correct as follows. **PRIV** ("invented a five-year history"): the
fixture contains the full FY-3→LTM history, the agent's `get_financials` call returned it, and
the model quoted it faithfully — 31/35 flagged tokens are literal tool citations, 4 are correct,
explicitly-hedged derivations. **NOTX** ("invents transactions when there are none"): the
generated narrative says, verbatim, "No recent M&A transactions on record." — a correct
statement of absence; the 22 judge-flagged sentences in that cell are real tool-sourced data
flagged against the narrow reference.

## What still stands

- `single_shot`'s 4–8% incorrect rate is genuine (its input and its grading pool coincide, and
  the control confirms its flagged tokens match nothing in the source).
- A real defect the artifact was hiding: **scale-suffix mislabeling**. Models echo tool values
  denominated in bare millions and write "$28,000" or "$1,800" where $28.0B / $1.8B is meant —
  30–40% of the flagged mass. Real data, wrong magnitude label.
- The hard rail's 0% inline-number result is mechanically true; its value proposition is
  machine-verifiability plus the elimination of both genuine error classes above — not the
  curing of a fabrication epidemic that didn't exist.
- The `agentic_verified` deltas (39→6, 28→20) measured convergence to the checker's literal
  digit vocabulary (the checker flagged correct out-of-pool numbers), and the deepseek/minimax
  leak rates under the hard rail are placeholder-discipline violations, not wrongness rates.
- The separate production-pipelines track (not committed here; described in Part 2 of the accompanying write-up series) is unaffected: both pipelines and their
  judge share the same extended payload scope.

## Deferred fix

The grading reference must match each design's legitimate data access — either grade tool-using
designs against payload ∪ tool outputs, or restrict tools to the payload contract. Both
invalidate the affected report columns and require a paid re-run, so the reports are annotated
rather than regenerated.
