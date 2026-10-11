from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    database_path: Path
    log_level: str = "INFO"

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            database_path=Path(os.getenv("NETOPS_DATABASE_PATH", "var/netops-autopilot.db")),
            log_level=os.getenv("NETOPS_LOG_LEVEL", "INFO").upper(),
        )

