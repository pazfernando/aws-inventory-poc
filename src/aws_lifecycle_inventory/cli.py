"""Command-line entrypoint for the AWS Resource Lifecycle Inventory Tool.

Authentication uses the standard boto3 credential chain. ``--profile`` and
``--region`` are optional; when omitted boto3 resolves credentials and region
from the environment, shared config, SSO, or an instance/container role. Only
read-only AWS APIs are invoked.
"""

from __future__ import annotations

import argparse
import sys

import boto3

from aws_lifecycle_inventory.inventory.direct_api import default_collectors
from aws_lifecycle_inventory.lifecycle import assess_records
from aws_lifecycle_inventory.orchestration import (
    MultiRegionScanResult,
    ScanResult,
    run_scan_multi_region,
)
from aws_lifecycle_inventory.output.csv_writer import write_csv
from aws_lifecycle_inventory.usage import assess_usage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aws-lifecycle-inventory",
        description=(
            "Read-only discovery of version-bearing AWS resources, written to CSV."
        ),
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="AWS named profile to use. Defaults to the boto3 credential chain.",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="AWS region to scan. Defaults to the session's configured region.",
    )
    parser.add_argument(
        "--regions",
        default=None,
        help=(
            "Comma-separated AWS regions to scan (e.g. us-east-1,eu-west-1). "
            "Overrides --region; defaults to the session's configured region."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        default="inventory.csv",
        help="Path to the CSV output file (default: inventory.csv).",
    )
    parser.add_argument(
        "--usage",
        action="store_true",
        help=(
            "Also assess resource usage from CloudWatch (opt-in). Off by default "
            "to keep scans cheap. Requires cloudwatch:GetMetricData."
        ),
    )
    parser.add_argument(
        "--usage-window-days",
        type=int,
        default=30,
        help="Observation window for usage assessment in days (default: 30).",
    )
    return parser


def _build_session(profile: str | None, region: str | None) -> boto3.Session:
    return boto3.Session(profile_name=profile, region_name=region)


def _parse_regions(raw: str | None) -> list[str]:
    """Split a comma-separated region list, dropping blanks."""
    if not raw:
        return []
    return [region.strip() for region in raw.split(",") if region.strip()]


def run(args: argparse.Namespace) -> MultiRegionScanResult:
    session = _build_session(args.profile, args.region)
    regions = _parse_regions(args.regions)
    if not regions:
        region = args.region or session.region_name
        if not region:
            raise SystemExit(
                "No region specified and none found in the AWS session. "
                "Pass --regions (or --region) or configure a default region."
            )
        regions = [region]
    # Discovery and lifecycle assessment are separate, composable steps: scan
    # produces records, then the reusable assessment service annotates them.
    result = run_scan_multi_region(default_collectors(), session, regions)
    result.records = assess_records(result.records, session=session)
    # Usage assessment is an opt-in composable step (off by default).
    if getattr(args, "usage", False):
        result.records = assess_usage(
            result.records,
            session=session,
            window_days=args.usage_window_days,
        )
    write_csv(result.records, args.output)
    return result


def _print_summary(result: ScanResult | MultiRegionScanResult, output: str) -> None:
    print(f"Wrote {len(result.records)} record(s) to {output}")
    for status in result.collector_statuses:
        state = "ok" if status.ok else f"FAILED ({status.error_code})"
        detail = f" - {status.error_message}" if not status.ok else ""
        where = f" [{status.region}]" if status.region else ""
        print(
            f"  collector {status.name}{where}: {state} "
            f"[{status.record_count} record(s)]{detail}"
        )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(args)
    _print_summary(result, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
