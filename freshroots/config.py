"""Runtime configuration.

Rule thresholds come from Raghav's documented rules in the case. Everything
marked ASSUMPTION is a prototype choice that Freshroots has not approved.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

RULE_VERSION = "rules-v0.1.0-prototype"

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    data_dir: Path = PROJECT_ROOT / "data" / "raw"
    db_path: Path = PROJECT_ROOT / "data" / "freshroots.db"

    # Documented rules (case, pages 2-3)
    high_demand_threshold: float = 0.20      # last 4 weeks > 20% above 12-week average
    high_demand_multiplier: float = 1.5      # reorder at 1.5x standard quantity
    recent_weeks: int = 4
    baseline_weeks: int = 12
    stockout_weeks: float = 6.0              # below 6 weeks of cover
    overstock_weeks: float = 14.0            # above 14 weeks of cover
    perishable_min_weeks: float = 3.0
    perishable_max_weeks: float = 4.0
    festival_uplift: float = 0.25            # +25% in festival months

    # ASSUMPTION: perishable windows replace the 6/14-week windows for
    # perishable SKUs ("tighter windows"). Set False to apply both.
    perishable_replaces_standard_windows: bool = True

    # Exception layer (deterministic statistics, not business rules)
    anomaly_modified_z: float = 3.5
    demand_drop_threshold: float = 0.20

    # Optional LLM explainer; disabled unless explicitly configured.
    llm_provider: str = "disabled"

    def to_json(self) -> str:
        d = asdict(self)
        d["data_dir"] = str(self.data_dir)
        d["db_path"] = str(self.db_path)
        return json.dumps(d, sort_keys=True)

    def rule_params(self) -> dict:
        """Parameters that change recommendation output (stored with each run)."""
        d = json.loads(self.to_json())
        for k in ("data_dir", "db_path", "llm_provider"):
            d.pop(k)
        d["rule_version"] = RULE_VERSION
        return d


def database_target(cfg: Config) -> str:
    """Neon/Postgres URL when DATABASE_URL is set, otherwise the SQLite file."""
    return os.environ.get("DATABASE_URL", "").strip() or str(cfg.db_path)


def load_config() -> Config:
    env = os.environ
    kwargs: dict = {}
    if env.get("FRESHROOTS_DATA_DIR"):
        kwargs["data_dir"] = Path(env["FRESHROOTS_DATA_DIR"])
    if env.get("FRESHROOTS_DB_PATH"):
        kwargs["db_path"] = Path(env["FRESHROOTS_DB_PATH"])
    elif env.get("VERCEL"):
        # The deployed bundle is read-only; without DATABASE_URL, keep a throwaway SQLite file in /tmp.
        kwargs["db_path"] = Path("/tmp/freshroots.db")
    if env.get("FRESHROOTS_LLM_PROVIDER"):
        kwargs["llm_provider"] = env["FRESHROOTS_LLM_PROVIDER"].strip().lower()
    elif env.get("GEMINI_API_KEY"):
        kwargs["llm_provider"] = "gemini"
    if env.get("FRESHROOTS_PERISHABLE_REPLACES_STANDARD"):
        kwargs["perishable_replaces_standard_windows"] = (
            env["FRESHROOTS_PERISHABLE_REPLACES_STANDARD"].strip().lower() in {"1", "true", "yes"}
        )
    return Config(**kwargs)
