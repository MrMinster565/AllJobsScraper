from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Job:
    id: str
    title: str
    url: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    posted: str = ""
    phones: list[str] = field(default_factory=list)

    def text(self) -> str:
        """Everything we know about the job, as one string for matching."""
        return "\n".join(p for p in (self.title, self.company, self.location, self.description) if p)


@dataclass
class Match:
    job: Job
    score: int  # 0-100
    reason: str = ""
