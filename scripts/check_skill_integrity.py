#!/usr/bin/env python3
"""Conservative integrity checks for the CX Agent Studio skill repository.

The checker intentionally does not update product facts. It only surfaces structural,
freshness, and known-broken-link problems that require human review.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
SOURCE_POLICY = ROOT / "references" / "source-policy.md"
README = ROOT / "README.md"


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def check_frontmatter(errors: list[str]) -> None:
    text = SKILL.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(errors, "SKILL.md must start with YAML-style frontmatter delimiter '---'.")
        return

    closing = text.find("\n---\n", 4)
    if closing == -1:
        fail(errors, "SKILL.md frontmatter has no closing '---' delimiter.")
        return

    frontmatter = text[4:closing]
    if not re.search(r"(?m)^name:\s*\S+", frontmatter):
        fail(errors, "SKILL.md frontmatter is missing a non-empty 'name' field.")
    if not re.search(r"(?m)^description:\s*(?:>|\S+)", frontmatter):
        fail(errors, "SKILL.md frontmatter is missing a non-empty 'description' field.")


def check_routed_references(errors: list[str]) -> None:
    text = SKILL.read_text(encoding="utf-8")
    routed = sorted(set(re.findall(r"references/[A-Za-z0-9._/-]+\.md", text)))
    if not routed:
        fail(errors, "SKILL.md does not route to any references/*.md files.")
        return

    for relative in routed:
        path = ROOT / relative
        if not path.is_file():
            fail(errors, f"Routed reference does not exist: {relative}")


def extract_audit_dates() -> list[date]:
    dates: list[date] = []
    pattern = re.compile(r"(?:audited|reviewed) on \*\*(\d{4}-\d{2}-\d{2})\*\*", re.IGNORECASE)
    for path in (SOURCE_POLICY, README):
        text = path.read_text(encoding="utf-8")
        for value in pattern.findall(text):
            dates.append(date.fromisoformat(value))
    return dates


def check_freshness(errors: list[str], max_age_days: int) -> None:
    dates = extract_audit_dates()
    if not dates:
        fail(errors, "No audit/review date found in README.md or references/source-policy.md.")
        return

    unique_dates = sorted(set(dates))
    if len(unique_dates) != 1:
        fail(errors, f"Audit/review dates disagree across repository docs: {unique_dates}")
        return

    audit_date = unique_dates[0]
    age_days = (date.today() - audit_date).days
    if age_days < 0:
        fail(errors, f"Audit date {audit_date} is in the future.")
    elif age_days > max_age_days:
        fail(
            errors,
            f"Audit snapshot is {age_days} days old (limit: {max_age_days}). "
            "Review current CX Agent Studio docs/release notes and update the snapshot deliberately.",
        )


def iter_markdown_files() -> list[Path]:
    files = [README, SKILL]
    files.extend(sorted((ROOT / "references").glob("*.md")))
    return [path for path in files if path.is_file()]


def collect_official_doc_links() -> list[str]:
    links: set[str] = set()
    pattern = re.compile(r"https://docs\.cloud\.google\.com/[A-Za-z0-9_./?=&%:+~-]+")
    for path in iter_markdown_files():
        for match in pattern.findall(path.read_text(encoding="utf-8")):
            links.add(match.rstrip(".,;:"))
    return sorted(links)


def probe_link(url: str, timeout: float = 15.0) -> tuple[str, str | None]:
    headers = {"User-Agent": "google-cx-agent-studio-skill-integrity-check/1.0"}
    request = urllib.request.Request(url, headers=headers, method="HEAD")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return "ok", str(response.status)
    except urllib.error.HTTPError as exc:
        if exc.code == 405:
            request = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return "ok", str(response.status)
            except urllib.error.HTTPError as get_exc:
                exc = get_exc
            except urllib.error.URLError as get_exc:
                return "warn", str(get_exc.reason)

        if exc.code in (404, 410):
            return "broken", str(exc.code)
        if exc.code == 429 or exc.code >= 500 or exc.code in (401, 403):
            return "warn", str(exc.code)
        return "broken", str(exc.code)
    except urllib.error.URLError as exc:
        return "warn", str(exc.reason)
    except TimeoutError:
        return "warn", "timeout"


def check_links(errors: list[str], warnings: list[str]) -> None:
    for url in collect_official_doc_links():
        status, detail = probe_link(url)
        if status == "broken":
            fail(errors, f"Official documentation link is broken ({detail}): {url}")
        elif status == "warn":
            warnings.append(f"Could not prove link health ({detail}): {url}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-audit-age-days", type=int, default=120)
    parser.add_argument("--check-links", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    check_frontmatter(errors)
    check_routed_references(errors)
    check_freshness(errors, args.max_audit_age_days)
    if args.check_links:
        check_links(errors, warnings)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        return 1

    print("Skill integrity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
