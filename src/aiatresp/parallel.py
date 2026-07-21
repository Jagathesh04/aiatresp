"""RAM-aware parallel execution settings for expensive atomic calculations."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ParallelSettings:
    workers: int
    memory_budget_gb: float

    @classmethod
    def automatic(cls, memory_per_worker_gb: float = 2.0, max_workers: int = 16) -> "ParallelSettings":
        """Choose a safe process count; never exceed 16 or the RAM budget."""
        available_gb = 4.0
        by_memory = max(1, int(available_gb // memory_per_worker_gb))
        workers = min(max_workers, os.cpu_count() or 1, by_memory)
        return cls(workers=workers, memory_budget_gb=available_gb)
