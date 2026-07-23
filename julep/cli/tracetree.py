from __future__ import annotations

from julep.projection import ProjectionEvent, SpanData, to_otel_spans


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
            if span.cost is not None:
                cost = f' ${span.cost:.4f}'
            elif (
                span.attrs.get("llm.cost.status") == "unknown"
                or "llm.model" in span.attrs
                or "llm.usage" in span.attrs
            ):
                # Older stored events predate llm.cost.status but still carry
                # model/usage attrs, so remote traces can render them honestly.
                cost = " cost=unknown"
            else:
                cost = ''
            lines.append(f'{prefix}{branch}{span.node} [{span.status}]{cost}')
            emit(span.cid, prefix + ('   ' if last else '│  '))

    emit(None, '')
    return '\n'.join(lines)
