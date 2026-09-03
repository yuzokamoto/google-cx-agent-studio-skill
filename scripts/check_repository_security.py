#!/usr/bin/env python3
"""Deterministic security policy for this public agent-skill repository.

PR mode runs from the trusted base branch. It fetches the PR head through the
GitHub API and scans it as inert data; it never checks out or executes PR code.

This repository intentionally uses a narrow policy. Expanding file types,
workflows, Actions, shell commands, or external content sources requires a
maintainer-reviewed policy change rather than silent acceptance.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

MAX_FILES = 100
MAX_FILE_SIZE = 256 * 1024
MAX_TEXT_LINE = 4000

REQUIRED_FILES = {
    "README.md",
    "SKILL.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".github/CODEOWNERS",
    ".github/copilot-instructions.md",
    ".github/dependabot.yml",
    ".github/workflows/skill-integrity.yml",
    ".github/workflows/pr-security.yml",
    "scripts/check_skill_integrity.py",
    "scripts/check_repository_security.py",
    "references/source-policy.md",
}

ROOT_FILES = {
    "LICENSE",
    "README.md",
    "SKILL.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".gitignore",
    ".gitattributes",
}

ALLOWED_WORKFLOWS = {
    ".github/workflows/skill-integrity.yml",
    ".github/workflows/pr-security.yml",
}

EXPECTED_EVENTS = {
    ".github/workflows/skill-integrity.yml": {"push", "schedule", "workflow_dispatch"},
    ".github/workflows/pr-security.yml": {"pull_request_target"},
}

ALLOWED_ACTIONS = {"actions/checkout"}

ALLOWED_RUN_COMMANDS = {
    "python3 scripts/check_repository_security.py --max-audit-age-days 120",
    "python3 scripts/check_skill_integrity.py --max-audit-age-days 120",
    "python3 scripts/check_skill_integrity.py --max-audit-age-days 120 --check-links",
    'python3 scripts/check_repository_security.py --pr-number "$PR_NUMBER" --repository "$GITHUB_REPOSITORY" --max-audit-age-days 120',
}

OWNER_ONLY_PREFIXES = (".github/", "scripts/")
OWNER_ONLY_FILES = {"AGENTS.md", "CLAUDE.md", "SECURITY.md", "CONTRIBUTING.md"}

INVISIBLE_OR_BIDI = {
    "\u200b", "\u200c", "\u200d",
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
    "\u2060", "\u2061", "\u2062", "\u2063", "\u2064",
    "\u2066", "\u2067", "\u2068", "\u2069", "\ufeff",
}

ALLOWED_MARKDOWN_HOSTS = {
    "docs.cloud.google.com",
    "cloud.google.com",
    "docs.github.com",
    "github.com",
    "example.com",
}

PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)
ACTION_USE_RE = re.compile(r"(?m)^\s*-?\s*uses:\s*([^\s#]+)")
FULL_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
ROUTED_REFERENCE_RE = re.compile(r"references/[A-Za-z0-9._/-]+\.md")
AUDIT_DATE_RE = re.compile(
    r"(?:audited|reviewed) on \*\*(\d{4}-\d{2}-\d{2})\*\*", re.IGNORECASE
)
DANGEROUS_HTML_RE = re.compile(
    r"<(?:script|iframe|object|embed|svg|img|style|details|summary)\b", re.IGNORECASE
)
DANGEROUS_SCHEME_RE = re.compile(
    r"(?:javascript:|data:\s*text/html|file://|ftp://)", re.IGNORECASE
)
BASE64_BLOB_RE = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{256,}={0,2}(?![A-Za-z0-9+/])")

Entry = tuple[str, str, int, bytes]


def add(errors: list[str], message: str) -> None:
    errors.append(message)


def allowed_path(path: str) -> bool:
    if path in ROOT_FILES:
        return True
    if path in {
        ".github/CODEOWNERS",
        ".github/dependabot.yml",
        ".github/copilot-instructions.md",
        ".github/pull_request_template.md",
    }:
        return True
    if path in ALLOWED_WORKFLOWS:
        return True
    if path.startswith(".github/ISSUE_TEMPLATE/"):
        name = path.removeprefix(".github/ISSUE_TEMPLATE/")
        return "/" not in name and name.endswith((".md", ".yml", ".yaml"))
    if path.startswith("references/"):
        name = path.removeprefix("references/")
        return "/" not in name and name.endswith(".md")
    if path.startswith("scripts/"):
        name = path.removeprefix("scripts/")
        return "/" not in name and name.endswith(".py")
    return False


def valid_path(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path or not PATH_RE.fullmatch(path):
        return False
    pure = PurePosixPath(path)
    return (
        all(part not in {"", ".", ".."} for part in pure.parts)
        and pure.as_posix() == path
    )


def strip_fenced_code(text: str) -> str:
    output: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if fence is None and (stripped.startswith("```") or stripped.startswith("~~~")):
            fence = stripped[:3]
            output.append("\n")
            continue
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            output.append("\n")
            continue
        output.append(line)
    return "".join(output)


def host_allowed(host: str) -> bool:
    host = host.lower().rstrip(".")
    return host in ALLOWED_MARKDOWN_HOSTS or host.endswith(".example.com")


def scan_text(path: str, text: str, errors: list[str]) -> None:
    for index, ch in enumerate(text):
        codepoint = ord(ch)
        if ch in INVISIBLE_OR_BIDI:
            add(errors, f"{path}: forbidden invisible/bidi Unicode U+{codepoint:04X} at character {index}")
            break
        if codepoint < 32 and ch not in "\n\r\t":
            add(errors, f"{path}: forbidden control character U+{codepoint:04X}")
            break

    for number, line in enumerate(text.splitlines(), start=1):
        if len(line) > MAX_TEXT_LINE:
            add(errors, f"{path}:{number}: line exceeds {MAX_TEXT_LINE} characters")
            break

    if not path.endswith(".md"):
        return

    if DANGEROUS_SCHEME_RE.search(text):
        add(errors, f"{path}: dangerous URL scheme is forbidden")
    if BASE64_BLOB_RE.search(text):
        add(errors, f"{path}: long encoded/base64-like blobs are forbidden in Markdown")

    visible = strip_fenced_code(text)
    if "<!--" in visible or "-->" in visible:
        add(errors, f"{path}: HTML comments are forbidden in Markdown")
    if DANGEROUS_HTML_RE.search(visible):
        add(errors, f"{path}: hidden/active HTML is forbidden in Markdown")
    if re.search(r"!\s*\[[^\]]*\]\s*\(", visible):
        add(errors, f"{path}: Markdown images are forbidden in this text-only repository")

    for raw_url in URL_RE.findall(text):
        candidate = raw_url.rstrip(".,;:!?)]}")
        host = urllib.parse.urlparse(candidate).hostname
        if not host or not host_allowed(host):
            add(errors, f"{path}: external URL host is not allowlisted: {candidate}")


def top_level_block(text: str, key: str) -> list[str] | None:
    lines = text.splitlines()
    marker = f"{key}:"
    start: int | None = None
    for index, line in enumerate(lines):
        if line == marker:
            start = index + 1
            break
        if line.startswith(marker) and line != marker:
            return [line]
    if start is None:
        return None

    block: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith((" ", "\t")) and not line.lstrip().startswith("#"):
            break
        block.append(line)
    return block


def event_keys(text: str) -> set[str]:
    block = top_level_block(text, "on")
    if block is None:
        return set()
    joined = "\n".join(block)
    return set(re.findall(r"(?m)^  ([A-Za-z0-9_]+):\s*$", joined))


def indented_mapping(text: str, key: str, indent: int) -> list[str]:
    lines = text.splitlines()
    marker = " " * indent + f"{key}:"
    for index, line in enumerate(lines):
        if line != marker:
            continue
        values: list[str] = []
        for current in lines[index + 1 :]:
            if current.strip() and len(current) - len(current.lstrip()) <= indent:
                break
            if current.strip():
                values.append(current.strip())
        return values
    return []


def run_blocks(text: str) -> Iterable[str]:
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)(?:-\s*)?run:\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        indent = len(match.group(1))
        inline = match.group(2)
        if inline and inline not in {"|", ">", "|-", ">-"}:
            yield inline.strip()
            index += 1
            continue
        block: list[str] = []
        index += 1
        while index < len(lines):
            current = lines[index]
            if current.strip() and len(current) - len(current.lstrip()) <= indent:
                break
            if current.strip():
                block.append(current.strip())
            index += 1
        yield "\n".join(block)


def scan_workflow(path: str, text: str, errors: list[str]) -> None:
    if path not in ALLOWED_WORKFLOWS:
        add(errors, f"{path}: workflow file is not allowlisted")
        return

    if re.search(r"(?m)^\s+(?:container|services|defaults|working-directory):", text):
        add(errors, f"{path}: container/services/defaults/working-directory are forbidden")
    if re.search(r"(?m)^\s+continue-on-error:\s*true\s*$", text, re.IGNORECASE):
        add(errors, f"{path}: continue-on-error is forbidden")
    if re.search(r"(?m)^\s+shell:\s*", text):
        add(errors, f"{path}: custom shell configuration is forbidden")

    permission_keys = re.findall(r"(?m)^\s*permissions:\s*", text)
    if len(permission_keys) != 1 or not text.startswith("name:"):
        add(errors, f"{path}: exactly one top-level permissions mapping is required")
    permissions = top_level_block(text, "permissions")
    if permissions is None or (permissions and permissions[0].startswith("permissions:")):
        add(errors, f"{path}: permissions must be an explicit top-level mapping")
    if re.search(r"(?m)^\s*[A-Za-z0-9_-]+:\s*write\s*$", text):
        add(errors, f"{path}: write-capable GITHUB_TOKEN permission is forbidden")
    if re.search(r"(?m)^\s*permissions:\s*(?:write-all|read-all)\s*$", text):
        add(errors, f"{path}: scalar read-all/write-all permissions are forbidden")

    if "${{ secrets." in text or "secrets[" in text:
        add(errors, f"{path}: repository/environment secrets are forbidden")
    if re.search(r"(?m)^\s*runs-on:\s*.*self-hosted", text):
        add(errors, f"{path}: self-hosted runners are forbidden")

    observed_events = event_keys(text)
    expected_events = EXPECTED_EVENTS[path]
    if observed_events != expected_events:
        add(errors, f"{path}: workflow events must be exactly {sorted(expected_events)}; got {sorted(observed_events)}")

    if path == ".github/workflows/skill-integrity.yml":
        if "  push:\n    branches:\n      - main\n" not in text:
            add(errors, f"{path}: push must target main only")
        if re.search(r"(?m)^      - (?!main\s*$).+$", "\n".join(top_level_block(text, "on") or [])):
            add(errors, f"{path}: unexpected branch/type list item in workflow events")
        if re.search(r"(?m)^\s+env:\s*$", text):
            add(errors, f"{path}: environment mappings are forbidden")
        allowed_if = "if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'"
        if_lines = [line.strip() for line in text.splitlines() if line.lstrip().startswith("if:")]
        if if_lines != [allowed_if]:
            add(errors, f"{path}: conditional steps must match the approved scheduled-link-check condition")

    if path == ".github/workflows/pr-security.yml":
        required_ref = 'ref: ${{ github.event.pull_request.base.sha }}'
        if required_ref not in text:
            add(errors, f"{path}: checkout must explicitly target the trusted base SHA")
        if "allow-unsafe-pr-checkout: true" in text:
            add(errors, f"{path}: unsafe PR checkout is forbidden")
        env_values = indented_mapping(text, "env", 8)
        expected_env = {
            "GITHUB_TOKEN: ${{ github.token }}",
            "GITHUB_REPOSITORY: ${{ github.repository }}",
            "PR_NUMBER: ${{ github.event.pull_request.number }}",
        }
        if set(env_values) != expected_env or len(env_values) != len(expected_env):
            add(errors, f"{path}: security-step environment must contain only the approved read-only PR metadata")
        if any(line.lstrip().startswith("if:") for line in text.splitlines()):
            add(errors, f"{path}: conditional skipping is forbidden")

    checkout_count = 0
    for use in ACTION_USE_RE.findall(text):
        normalized = use.strip("\"'")
        if normalized.startswith("./") or normalized.startswith("docker://"):
            add(errors, f"{path}: local/Docker actions are forbidden: {normalized}")
            continue
        if "@" not in normalized:
            add(errors, f"{path}: malformed action reference: {normalized}")
            continue
        action, ref = normalized.rsplit("@", 1)
        if action not in ALLOWED_ACTIONS:
            add(errors, f"{path}: action is not allowlisted: {action}")
        if not FULL_SHA_RE.fullmatch(ref):
            add(errors, f"{path}: action must be pinned to a full commit SHA: {normalized}")
        if action == "actions/checkout":
            checkout_count += 1

    if checkout_count != 1:
        add(errors, f"{path}: exactly one actions/checkout step is required")

    with_values = indented_mapping(text, "with", 8)
    if path == ".github/workflows/skill-integrity.yml":
        expected_with = {"persist-credentials: false"}
    else:
        expected_with = {
            'ref: ${{ github.event.pull_request.base.sha }}',
            "persist-credentials: false",
        }
    if set(with_values) != expected_with or len(with_values) != len(expected_with):
        add(errors, f"{path}: checkout options differ from the approved minimal configuration")

    for block in run_blocks(text):
        if "\n" in block:
            add(errors, f"{path}: multiline run blocks are forbidden")
            continue
        if block not in ALLOWED_RUN_COMMANDS:
            add(errors, f"{path}: workflow run command is not in the exact command allowlist: {block!r}")


def check_skill_structure(files: dict[str, str], errors: list[str], max_age_days: int) -> None:
    skill = files.get("SKILL.md", "")
    if not skill.startswith("---\n") or "\n---\n" not in skill[4:]:
        add(errors, "SKILL.md: invalid or missing frontmatter delimiters")
    else:
        closing = skill.find("\n---\n", 4)
        frontmatter = skill[4:closing]
        if not re.search(r"(?m)^name:\s*\S+", frontmatter):
            add(errors, "SKILL.md: frontmatter is missing name")
        if not re.search(r"(?m)^description:\s*(?:>|\S+)", frontmatter):
            add(errors, "SKILL.md: frontmatter is missing description")

    routed = set(ROUTED_REFERENCE_RE.findall(skill))
    if not routed:
        add(errors, "SKILL.md: no routed references found")
    for path in sorted(routed):
        if path not in files:
            add(errors, f"SKILL.md: routed reference is missing: {path}")

    dates: list[date] = []
    for path in ("README.md", "references/source-policy.md"):
        for value in AUDIT_DATE_RE.findall(files.get(path, "")):
            try:
                dates.append(date.fromisoformat(value))
            except ValueError:
                add(errors, f"{path}: invalid audit date {value}")
    unique_dates = sorted(set(dates))
    if not unique_dates:
        add(errors, "audit/review date not found")
    elif len(unique_dates) != 1:
        add(errors, f"audit/review dates disagree: {unique_dates}")
    else:
        age = (date.today() - unique_dates[0]).days
        if age < 0:
            add(errors, f"audit date {unique_dates[0]} is in the future")
        elif age > max_age_days:
            add(errors, f"audit snapshot is {age} days old (limit {max_age_days}); human review required")


def scan_entries(entries: list[Entry], max_age_days: int) -> list[str]:
    errors: list[str] = []
    files: dict[str, str] = {}

    if len(entries) > MAX_FILES:
        add(errors, f"repository contains {len(entries)} files; limit is {MAX_FILES}")

    paths = {path for path, _, _, _ in entries}
    for required in sorted(REQUIRED_FILES):
        if required not in paths:
            add(errors, f"required security/integrity file is missing: {required}")

    for path, mode, size, raw in entries:
        if not valid_path(path):
            add(errors, f"invalid repository path: {path!r}")
            continue
        if not allowed_path(path):
            add(errors, f"file path/type is not allowlisted for this text-only repository: {path}")
        if mode in {"120000", "160000"}:
            add(errors, f"symlinks/submodules are forbidden: {path} (mode {mode})")
        if mode == "100755":
            add(errors, f"executable files are forbidden: {path}")
        if size > MAX_FILE_SIZE:
            add(errors, f"file exceeds {MAX_FILE_SIZE} bytes: {path} ({size})")
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            add(errors, f"non-UTF-8/binary content is forbidden: {path}")
            continue
        files[path] = text
        scan_text(path, text, errors)
        if path.startswith(".github/workflows/"):
            scan_workflow(path, text, errors)

    owners = files.get(".github/CODEOWNERS", "")
    if not all(marker in owners for marker in ("/.github/", "/SKILL.md", "/AGENTS.md", "/scripts/")):
        add(errors, ".github/CODEOWNERS must explicitly protect .github, SKILL.md, AGENTS.md, and scripts")

    check_skill_structure(files, errors, max_age_days)
    return errors


def local_entries(root: Path) -> list[Entry]:
    entries: list[Entry] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        st = path.lstat()
        rel = path.relative_to(root).as_posix()
        if stat.S_ISLNK(st.st_mode):
            entries.append((rel, "120000", st.st_size, b""))
            continue
        if stat.S_ISDIR(st.st_mode):
            continue
        mode = "100755" if st.st_mode & stat.S_IXUSR else "100644"
        entries.append((rel, mode, st.st_size, path.read_bytes()))
    return entries


def api_json(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "google-cx-agent-studio-skill-pr-security/1.1",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def pr_provenance_errors(repository: str, pr_number: int, token: str) -> list[str]:
    errors: list[str] = []
    base = f"https://api.github.com/repos/{repository}"
    pr = api_json(f"{base}/pulls/{pr_number}", token)
    author = pr["user"]["login"]
    owner = repository.split("/", 1)[0]
    if author == owner:
        return errors

    changed = api_json(f"{base}/pulls/{pr_number}/files?per_page=100", token)
    for item in changed:
        path = item["filename"]
        protected = path in OWNER_ONLY_FILES or path.startswith(OWNER_ONLY_PREFIXES)
        dependabot_action_update = author == "dependabot[bot]" and path in ALLOWED_WORKFLOWS
        if protected and not dependabot_action_update:
            add(errors, f"external PR author {author!r} may not modify owner-only security path: {path}")
    return errors


def remote_pr_entries(repository: str, pr_number: int, token: str) -> list[Entry]:
    base = f"https://api.github.com/repos/{repository}"
    pr = api_json(f"{base}/pulls/{pr_number}", token)
    head_sha = pr["head"]["sha"]
    tree = api_json(f"{base}/git/trees/{head_sha}?recursive=1", token)
    if tree.get("truncated"):
        raise RuntimeError("GitHub tree response was truncated; refusing incomplete scan")

    entries: list[Entry] = []
    for item in tree.get("tree", []):
        if item.get("type") == "tree":
            continue
        path = item["path"]
        mode = item.get("mode", "")
        size = int(item.get("size") or 0)
        if item.get("type") != "blob" or size > MAX_FILE_SIZE:
            entries.append((path, mode, size, b""))
            continue
        blob = api_json(f"{base}/git/blobs/{item['sha']}", token)
        if blob.get("encoding") != "base64":
            raise RuntimeError(f"unexpected blob encoding for {path}: {blob.get('encoding')}")
        raw = base64.b64decode(blob.get("content", ""), validate=False)
        entries.append((path, mode, size or len(raw), raw))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--repository")
    parser.add_argument("--max-audit-age-days", type=int, default=120)
    args = parser.parse_args()

    pre_errors: list[str] = []
    try:
        if args.pr_number is not None:
            repository = args.repository or os.environ.get("GITHUB_REPOSITORY")
            token = os.environ.get("GITHUB_TOKEN")
            if not repository or not token:
                print("ERROR: PR mode requires GITHUB_REPOSITORY and GITHUB_TOKEN", file=sys.stderr)
                return 2
            pre_errors = pr_provenance_errors(repository, args.pr_number, token)
            entries = remote_pr_entries(repository, args.pr_number, token)
        else:
            entries = local_entries(Path(args.root).resolve())
    except (OSError, RuntimeError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        print(f"ERROR: security scanner could not build a complete repository view: {exc}", file=sys.stderr)
        return 2

    errors = pre_errors + scan_entries(entries, args.max_audit_age_days)
    for item in errors:
        print(f"ERROR: {item}", file=sys.stderr)
    if errors:
        return 1
    print("Repository security checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
