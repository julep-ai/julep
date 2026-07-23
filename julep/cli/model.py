from __future__ import annotations

from dataclasses import dataclass, field

from julep.cli.config import JulepConfig
from julep.cli.discover import scan_agents


@dataclass(frozen=True)
class Agent:
    name: str
    kind: str
    file: str
    line: int
    tags: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Module:
    root: str
    agents: list[Agent]

    def by_name(self, name: str) -> Agent:
        for a in self.agents:
            if a.name == name:
                return a
        raise KeyError(name)


def build_module(cfg: JulepConfig) -> Module:
    agents = [
        Agent(
            name=info.name,
            kind=info.kind,
            file=info.file,
            line=info.line,
            tags=list(cfg.tags.get(info.name, [])),
            calls=list(info.calls),
        )
        for info in sorted(scan_agents(cfg), key=lambda i: i.name)
    ]
    return Module(root=str(cfg.root), agents=agents)
