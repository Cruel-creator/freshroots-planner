import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from freshroots.config import Config  # noqa: E402
from freshroots.engine import evaluate_sku  # noqa: E402

LABELS = [f"2026-W{w:02d}" for w in range(31, 43)]  # 12 consecutive weeks


@pytest.fixture
def cfg():
    return Config()


def flat(value, n=12):
    return {w: float(value) for w in LABELS[-n:]}


def run_sku(cfg, *, units=None, stock=600.0, perishable=False, std=100.0, festival=False, **kw):
    return evaluate_sku(
        sku_id="T1", window_labels=LABELS, weekly_units=units if units is not None else flat(100),
        stock=stock, is_perishable=perishable, standard_qty=std, festival=festival, cfg=cfg, **kw)
