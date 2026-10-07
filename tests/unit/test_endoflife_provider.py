"""Tests for the EndOfLife lifecycle provider (Change endoflife, tasks 1.1-3.4)."""

from __future__ import annotations

import json
from datetime import date

import pytest

from aws_lifecycle_inventory.lifecycle.providers import endoflife as eol_mod
from aws_lifecycle_inventory.lifecycle.providers.endoflife import (
    EndOfLifeProvider,
    _SEED_PATH,
    max_age_days,
)
from aws_lifecycle_inventory.lifecycle.providers.endoflife_data import lookup_keys
from aws_lifecycle_inventory.models import ResourceVersionRecord

REGION = "us-east-1"
ACCOUNT_ID = "123456789012"


def _lambda(name="python", version="3.10"):
    return ResourceVersionRecord(
        account_id=ACCOUNT_ID, region=REGION,
        resource_type="AWS::Lambda::Function", resource_id="fn",
        software_name=name, version=version,
    )


def _eks(version="1.30"):
    return ResourceVersionRecord(
        account_id=ACCOUNT_ID, region=REGION,
        resource_type="AWS::EKS::Cluster", resource_id="c",
        software_name="kubernetes", version=version,
    )


def _rds(engine="postgres", version="15.4"):
    return ResourceVersionRecord(
        account_id=ACCOUNT_ID, region=REGION,
        resource_type="AWS::RDS::DBInstance", resource_id="db",
        software_name=engine, version=version,
    )


@pytest.fixture(autouse=True)
def _isolate_cache(tmp_path, monkeypatch):
    """Point the cache at a temp dir so tests never touch the real cache."""
    cache_file = tmp_path / "endoflife_cache.json"
    monkeypatch.setattr(eol_mod, "cache_path", lambda: cache_file)
    return cache_file


# --- task 1.1: seed loads --------------------------------------------------

def test_seed_loads_expected_products():
    data = json.loads(_SEED_PATH.read_text())
    assert "updated_at" in data
    products = data["products"]
    for p in ("aws-lambda", "amazon-eks", "amazon-rds-postgresql"):
        assert p in products and len(products[p]) > 0


# --- task 1.2: mapping table -----------------------------------------------

def test_lookup_keys_lambda():
    assert lookup_keys(_lambda("python", "3.10")) == ("aws-lambda", "python3.10")


def test_lookup_keys_rds_postgres_major():
    assert lookup_keys(_rds("postgres", "15.4")) == ("amazon-rds-postgresql", "15")


def test_lookup_keys_eks_minor():
    assert lookup_keys(_eks("1.30")) == ("amazon-eks", "1.30")


def test_lookup_keys_unmapped_returns_none():
    rec = ResourceVersionRecord(
        account_id=ACCOUNT_ID, region=REGION,
        resource_type="AWS::Glue::Job", resource_id="g",
        software_name="glue", version="4.0",
    )
    assert lookup_keys(rec) is None


# --- task 1.3: cache-present vs cache-absent --------------------------------

def test_loads_from_seed_when_no_cache():
    provider = EndOfLifeProvider.load(allow_refresh=False)
    assert provider.match(_lambda("python", "3.10")) is not None


def test_loads_from_cache_when_present(_isolate_cache):
    _isolate_cache.write_text(json.dumps({
        "updated_at": date.today().isoformat(),
        "products": {"aws-lambda": [{"cycle": "python3.10", "eol": "2099-01-01",
                                     "link": "http://cache"}]},
    }))
    provider = EndOfLifeProvider.load(allow_refresh=False)
    ev = provider.match(_lambda("python", "3.10"))
    assert ev.evidence_id == "http://cache"  # came from cache, not seed


# --- task 2.1: match returns evidence with source link ---------------------

def test_match_returns_evidence_with_source_link():
    provider = EndOfLifeProvider.load(allow_refresh=False)
    ev = provider.match(_lambda("python", "3.10"))
    assert ev.source == "ENDOFLIFE"
    assert ev.evidence_id.startswith("http")
    assert ev.eol_date is not None
    assert ev.details["source_url"].startswith("http")


def test_match_unmapped_returns_none():
    provider = EndOfLifeProvider.load(allow_refresh=False)
    assert provider.match(_lambda("python", "99.99")) is None


# --- task 3.1: configurable threshold --------------------------------------

def test_default_threshold(monkeypatch):
    monkeypatch.delenv("LIFECYCLE_REFRESH_MAX_AGE_DAYS", raising=False)
    assert max_age_days() == 30


def test_overridden_threshold(monkeypatch):
    monkeypatch.setenv("LIFECYCLE_REFRESH_MAX_AGE_DAYS", "7")
    assert max_age_days() == 7


def test_invalid_threshold_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("LIFECYCLE_REFRESH_MAX_AGE_DAYS", "not-a-number")
    assert max_age_days() == 30


# --- task 3.2: refresh when stale, not when fresh --------------------------

def test_refresh_fetches_when_stale(monkeypatch, _isolate_cache):
    _isolate_cache.write_text(json.dumps({
        "updated_at": "2000-01-01",  # ancient -> stale
        "products": {"aws-lambda": [{"cycle": "python3.10", "eol": "2020-01-01",
                                     "link": "http://old"}]},
    }))
    calls = {"n": 0}

    def _fake_fetch(*a, **k):
        calls["n"] += 1
        return {"updated_at": date.today().isoformat(),
                "products": {"aws-lambda": [{"cycle": "python3.10",
                                             "eol": "2099-01-01", "link": "http://new"}]}}

    monkeypatch.setattr(eol_mod, "fetch_products", _fake_fetch)
    provider = EndOfLifeProvider.load(allow_refresh=True)
    assert calls["n"] == 1
    assert provider.stale is False
    # cache rewritten with new data
    assert provider.match(_lambda("python", "3.10")).evidence_id == "http://new"


def test_no_fetch_when_fresh(monkeypatch, _isolate_cache):
    _isolate_cache.write_text(json.dumps({
        "updated_at": date.today().isoformat(),  # fresh
        "products": {"aws-lambda": [{"cycle": "python3.10", "eol": "2099-01-01",
                                     "link": "http://fresh"}]},
    }))
    calls = {"n": 0}
    monkeypatch.setattr(eol_mod, "fetch_products",
                        lambda *a, **k: calls.__setitem__("n", calls["n"] + 1) or {})
    EndOfLifeProvider.load(allow_refresh=True)
    assert calls["n"] == 0


# --- task 3.3: refresh is non-fatal ----------------------------------------

def test_refresh_failure_keeps_stale_data(monkeypatch, _isolate_cache):
    _isolate_cache.write_text(json.dumps({
        "updated_at": "2000-01-01",
        "products": {"aws-lambda": [{"cycle": "python3.10", "eol": "2099-01-01",
                                     "link": "http://stale"}]},
    }))

    def _boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(eol_mod, "fetch_products", _boom)
    provider = EndOfLifeProvider.load(allow_refresh=True)
    # Kept the stale dataset, marked stale, still serves evidence.
    assert provider.stale is True
    assert provider.match(_lambda("python", "3.10")).evidence_id == "http://stale"


# --- task 3.4: cache written locally ---------------------------------------

def test_cache_written_locally_after_refresh(monkeypatch, _isolate_cache):
    monkeypatch.setattr(eol_mod, "fetch_products", lambda *a, **k: {
        "updated_at": date.today().isoformat(),
        "products": {"aws-lambda": [{"cycle": "python3.10", "eol": "2099-01-01",
                                     "link": "http://written"}]},
    })
    # No cache yet -> seed is ancient? Seed is fresh; force refresh via ancient cache.
    _isolate_cache.write_text(json.dumps({"updated_at": "2000-01-01", "products": {}}))
    EndOfLifeProvider.load(allow_refresh=True)
    assert _isolate_cache.exists()
    written = json.loads(_isolate_cache.read_text())
    assert written["products"]["aws-lambda"][0]["link"] == "http://written"
