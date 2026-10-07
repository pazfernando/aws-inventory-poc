"""Shared helpers for direct-API collectors."""

from __future__ import annotations


def split_lambda_runtime(runtime: str) -> tuple[str, str]:
    """Split a Lambda runtime identifier into (software_name, version).

    Examples:
        python3.12  -> ("python", "3.12")
        nodejs20.x  -> ("nodejs", "20.x")
        java21      -> ("java", "21")
        dotnet8     -> ("dotnet", "8")
        go1.x       -> ("go", "1.x")
        provided.al2023 -> ("provided", "al2023")

    Never invents a version: if no numeric portion is present the version is "".
    """
    if not runtime:
        return "", ""
    for index, char in enumerate(runtime):
        if char.isdigit():
            return runtime[:index], runtime[index:]
    # No digits at all (e.g. "ruby"): name only, version stays empty.
    return runtime, ""
