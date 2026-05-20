from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_title: str = "模具制造与注塑生产协同 Agent"
    app_version: str = "2.0.0"
    frontend_base_url: str = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:8900")
    upload_dir: str = os.getenv("UPLOAD_DIR", "data/uploads")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
