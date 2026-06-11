# common/render.py
from __future__ import annotations
from jinja2 import Environment, StrictUndefined, TemplateError
from markupsafe import Markup
from common.schemas import Payload

_env = Environment(undefined=StrictUndefined, autoescape=True)

_SHELL = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{{ entity }} — Tear Sheet</title>
<style>body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto}
table{border-collapse:collapse;margin:1rem 0}td,th{border:1px solid #ccc;padding:4px 8px}
.gaps{color:#888}</style></head>
<body>
<h1>{{ entity }}</h1><p>As of {{ as_of }}</p>
<section class="narrative">{{ narrative_html }}</section>
{% for name, rows in tables.items() %}{% if rows %}
<h2>{{ name }}</h2>
<table><tr>{% for col in rows[0].keys() %}<th>{{ col }}</th>{% endfor %}</tr>
{% for row in rows %}<tr>{% for v in row.values() %}<td>{{ v }}</td>{% endfor %}</tr>{% endfor %}
</table>
{% endif %}{% endfor %}
{% if gaps %}<p class="gaps">Data gaps: {{ gaps | join(", ") }}</p>{% endif %}
</body></html>"""


def render(payload: Payload, narrative: str) -> str:
    context = {fid: (pf.display if pf.value is not None else "—")
               for fid, pf in payload.fields.items()}
    narrative_html = _env.from_string(narrative).render(**context)
    shell = _env.from_string(_SHELL)
    return shell.render(
        entity=payload.entity, as_of=payload.as_of,
        narrative_html=Markup(narrative_html), tables=payload.tables, gaps=payload.gaps,
    )


def safe_render(payload: Payload, narrative: str) -> str | None:
    """Render, returning None on any Jinja template error (hallucinated placeholder OR malformed template syntax).

    A `{{token}}` that maps to no payload field or a malformed template (e.g. unclosed expression,
    bad tag) is a measured failure mode — the validation gate records it (placeholder_ok=False).
    Rendering must not abort the matrix over it, so a design's rendered artifact is simply absent
    (None) for that cell. `render` stays strict.
    """
    try:
        return render(payload, narrative)
    except TemplateError:
        return None
