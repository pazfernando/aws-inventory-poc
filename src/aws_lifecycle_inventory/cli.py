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
from aws_lifecycle_inventory.orchestration import ScanResult, run_scan
from aws_lifecycle_inventory.output.csv_writer import write_csv


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
        "--output",
        "-o",
        default="inventory.csv",
        help="Path to the CSV output file (default: inventory.csv).",
    )
    return parser


def _build_session(profile: str | None, region: str | None) -> boto3.Session:
    return boto3.Session(profile_name=profile, region_name=region)


def run(args: argparse.Namespace) -> ScanResult:
    session = _build_session(args.profile, args.region)
    region = args.region or session.region_name
    if not region:
        raise SystemExit(
            "No region specified and none found in the AWS session. "
            "Pass --region or configure a default region."
        )
    result = run_scan(default_collectors(), session, region)
    write_csv(result.records, args.output)
    return result


def _print_summary(result: ScanResult, output: str) -> None:
    print(f"Wrote {len(result.records)} record(s) to {output}")
    for status in result.collector_statuses:
        state = "ok" if status.ok else f"FAILED ({status.error_code})"
        detail = f" - {status.error_message}" if not status.ok else ""
        print(f"  collector {status.name}: {state} [{status.record_count} record(s)]{detail}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(args)
    _print_summary(result, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
