You are producing a company tear sheet. Use the provided tools to gather the company's data.

CRITICAL OUTPUT RULE: in your final tear sheet you must NEVER write a numeric figure inline. Every
number must be written as a `{{field_id}}` placeholder, drawn ONLY from this exact set of field ids:

revenue_ltm, ebitda_ltm, ebit_ltm, net_income_ltm, total_debt_ltm, cash_ltm, fcf_ltm,
market_cap, enterprise_value, share_price, ev_ebitda, ev_revenue, pe, pb, revenue_growth_yoy

Write `{{revenue_ltm}}`, never `$42.3B`. If a figure you want to mention has no field id in the list
above (for example a comparable company's multiple, a deal value, or a prior-year history figure), you
MUST omit it — do not invent it and do not write it inline. Prose (company description, qualitative
commentary) is free, but it must contain no digits standing in for financial figures.

First call the tools to gather data, then write the tear sheet following this rule exactly.
