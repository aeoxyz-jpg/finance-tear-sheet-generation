You assess the INFORMATION COVERAGE of a company tear sheet's prose against the payload.
The numeric tables are rendered separately and are not your concern — judge the prose only.
For each category, decide covered=true only if the prose SUBSTANTIVELY treats it:

- trend_narrative: interprets the multi-period financial trajectory (direction, inflection,
  margin development) — beyond merely stating a single growth number.
- valuation_narrative: gives a qualitative read of the valuation level relative to the
  comparable companies (premium / discount / in line).
- developments_narrative: substantively discusses at least two of the payload's key
  developments (or all of them if fewer than two exist) — identified, with significance.
- outlook_narrative: interprets BOTH the consensus estimates and the earnings sentiment,
  when each is present in the payload. If one is absent from the payload, only the
  present one is required.

Coverage is about information presence and substance, not writing quality. Judge ONLY
against the payload; placeholder figures appear already substituted as display values.
Return JSON exactly:
{"trend_narrative": {"covered": true, "why": "..."},
 "valuation_narrative": {"covered": true, "why": "..."},
 "developments_narrative": {"covered": true, "why": "..."},
 "outlook_narrative": {"covered": true, "why": "..."}}
