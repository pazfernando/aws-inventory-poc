"""EndOfLife lifecycle provider (Change endoflife).

Primary contingency lifecycle source when AWS Health is unavailable. Backed by
endoflife.date data for AWS products. Each entry carries the official source link
as evidence. The provider is offline-capable (baked seed + on-disk runtime cache)
and self-refreshing by age; refresh is non-fatal.

Dataset shape (JSON):
    {
      "updated_at": "YYYY-MM-DD",
      "products": { "<product>": [ {endoflife entry}, ... ], ... }
    }
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from aws_lifecycle_inventory.lifecycle.models import LifecycleEvidence
from aws_lifecycle_inventory.lifecycle.providers.endoflife_data import (
    API_BASE,
    ENDOFLIFE_PRODUCTS,
    lookup_keys,
)
from aws_lifecycle_inventory.models import ResourceVersionRecord

SOURCE = "ENDOFLIFE"

_SEED_PATH = Path(__file__).with_name("endoflife_seed.json")
_REFRESH_ENV_VAR = "LIFECYCLE_REFRESH_MAX_AGE_DAYS"
_DEFAULT_MAX_AGE_DAYS = 30


# --- Fetching (shared by seed generation and runtime refresh) --------------

def fetch_products(products=ENDOFLIFE_PRODUCTS, timeout: int = 20) -> dict:
    """Fetch the given endoflife.date products and return a dataset dict."""
    collected: dict[str, list] = {}
    for product in products:
        with urllib.request.urlopen(f"{API_BASE}/{product}.json", timeout=timeout) as resp:
            collected[product] = json.load(resp)
    return {
        "updated_at": datetime.now(timezone.utc).date().isoformat(),
        "products": collected,
    }


# --- Freshness / cache location --------------------------------------------

def max_age_days() -> int:
    raw = os.environ.get(_REFRESH_ENV_VAR)
    if raw is None or raw.strip() == "":
        return _DEFAULT_MAX_AGE_DAYS
    try:
        return int(raw)
    except ValueError:
        return _DEFAULT_MAX_AGE_DAYS


def cache_path() -> Path:
    """Local on-disk cache location. Uses an OS cache dir, /tmp as fallback."""
    base = os.environ.get("XDG_CACHE_HOME")
    if base:
        root = Path(base)
    else:
        home = Path.home()
        root = home / "Library" / "Caches" if (home / "Library").exists() else home / ".cache"
    try:
        target = root / "aws-lifecycle-inventory"
        target.mkdir(parents=True, exist_ok=True)
    except OSError:
        target = Path("/tmp/aws-lifecycle-inventory")
        target.mkdir(parents=True, exist_ok=True)
    return target / "endoflife_cache.json"


def _is_stale(updated_at: str, today: date, threshold_days: int) -> bool:
    try:
        last = date.fromisoformat(updated_at)
    except (TypeError, ValueError):
        return True
    return (today - last).days > threshold_days


# --- Provider --------------------------------------------------------------

class EndOfLifeProvider:
    source = SOURCE

    def __init__(self, dataset: dict, stale: bool = False) -> None:
        self._dataset = dataset
        self.stale = stale
        self._index = self._build_index(dataset)

    @staticmethod
    def _build_index(dataset: dict) -> dict:
        """Index: product -> {cycle -> entry}."""
        index: dict[str, dict[str, dict]] = {}
        for product, entries in (dataset.get("products") or {}).items():
            index[product] = {str(e.get("cycle")): e for e in entries if e.get("cycle") is not None}
        return index

    @classmethod
    def load(
        cls,
        today: date | None = None,
        allow_refresh: bool = True,
    ) -> "EndOfLifeProvider":
        """Load the dataset: runtime cache if present, else packaged seed.

        If the loaded dataset is stale and refresh is allowed, re-fetch from
        endoflife.date and rewrite the cache. Refresh is non-fatal: on any error
        the existing dataset is kept and marked stale.
        """
        today = today or datetime.now(timezone.utc).date()
        dataset, from_cache = cls._load_dataset()

        stale = _is_stale(dataset.get("updated_at", ""), today, max_age_days())
        if stale and allow_refresh:
            try:
                refreshed = fetch_products()
                cls._write_cache(refreshed)
                return cls(refreshed, stale=False)
            except Exception:
                # Non-fatal: keep the existing (stale) dataset.
                return cls(dataset, stale=True)
        return cls(dataset, stale=stale)

    @staticmethod
    def _load_dataset() -> tuple[dict, bool]:
        cache = cache_path()
        if cache.exists():
            try:
                return json.loads(cache.read_text()), True
            except (OSError, ValueError):
                pass
        return json.loads(_SEED_PATH.read_text()), False

    @staticmethod
    def _write_cache(dataset: dict) -> None:
        cache_path().write_text(json.dumps(dataset, indent=2))

    def match(self, record: ResourceVersionRecord) -> LifecycleEvidence | None:
        keys = lookup_keys(record)
        if keys is None:
            return None
        product, cycle = keys
        entry = self._index.get(product, {}).get(cycle)
        if entry is None:
            return None

        eol_raw = entry.get("eol")
        eol_date: date | None = None
        # endoflife 'eol' can be a date string, or a bool (true=already EOL / false=not set).
        if isinstance(eol_raw, str):
            try:
                eol_date = date.fromisoformat(eol_raw)
            except ValueError:
                eol_date = None

        link = entry.get("link") or f"https://endoflife.date/{product}"
        return LifecycleEvidence(
            source=self.source,
            evidence_id=link,
            eol_date=eol_date,
            status=None,
            details={
                "endoflife_product": product,
                "cycle": cycle,
                "eol": str(eol_raw),
                "support": str(entry.get("support", "")),
                "source_url": link,
                "dataset_updated_at": self._dataset.get("updated_at", ""),
                "dataset_stale": str(self.stale),
                "lifecycle_source": self.source,
            },
        )
