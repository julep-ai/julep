from __future__ import annotations

from composable_agents.projection import ProjectionEvent, SpanData, to_otel_spans


def render_tree(events: list[ProjectionEvent]) -> str:
    """Render projection events as an indented terminal trace tree (offline, no network)."""
    spans = to_otel_spans(events)
    by_cid: dict[str, SpanData] = {s.cid: s for s in spans}
    children: dict[str | None, list[SpanData]] = {}
    for s in spans:
        primary = s.parents[0] if s.parents else None
        parent = primary if primary in by_cid else None
        children.setdefault(parent, []).append(s)

    lines: list[str] = []

    def emit(cid_parent: str | None, prefix: str) -> None:
        kids = children.get(cid_parent, [])
        for i, span in enumerate(kids):
            last = i == len(kids) - 1
            branch = '└─ ' if last else '├─ '
            cost = f' ${span.cost:.4f}' if span.cost else ''
            lines.append(f'{prefix}{branch}{span.node} [{span.status}]{cost}')
            emit(span.cid, prefix + ('   ' if last else '│  '))

    emit(None, '')
    return '\n'.join(lines)
