#!/usr/bin/env python3
"""Deterministic repository security checks for a public agent-skill repository.

The PR mode is designed to run from a trusted base branch under pull_request_target.
It downloads the pull request head as data through the GitHub API and never executes
code from the pull request.
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
from typing import Iterable

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

INVISIBLE_OR_BIDI = {
    "\u200b",
    "\u200c",
    "\u200d",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2060",
    "\u2061",
    "\u2062",
    "\u2063",
    "\u2064",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
    "\ufeff",
}

URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)
ACTION_USE_RE = re.compile(r"(?m)^\s*-?\s*uses:\s*([^\s#]+)")
FULL_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
ROUTED_REFERENCE_RE = re.compile(r"references/[A-Za-z0-9._/-]+\.md")
AUDIT_DATE_RE = re.compile(
    r"(?:audited|reviewed) on \*\*(\d{4}-\d{2}-\d{2})\*\*", re.IGNORECASE
)

ALLOWED_AGENT_DOC_HOSTS = {
    "docs.cloud.google.com",
    "cloud.google.com",
    "docs.github.com",
    "github.com",
    "example.com",
}

DANGEROUS_HTML_RE = re.compile(
    r"<(?:script|iframe|object|embed|svg|img|style|details|summary)\b", re.IGNORECASE
)
DANGEROUS_SCHEME_RE = re.compile(
    r"(?:javascript:|data:\s*text/html|file://|ftp://)", re.IGNORECASE
)
UNTRUSTED_EVENT_RE = re.compile(
    r"(?m)^\s{2}(?:issues|issue_comment|pull_request_review_comment|discussion|discussion_comment|repository_dispatch|workflow_run):"
)


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def is_allowed_path(path: str) -> bool:
    if path in ROOT_FILES:
        return True
    if path == ".github/CODEOWNERS":
        return True
    if path in {
        ".github/dependabot.yml",
        ".github/copilot-instructions.md",
        ".github/pull_request_template.md",
    }:
        return True
    if path.startswith(".github/workflows/"):
        name = path.removeprefix(".github/workflows/")
        return "/" not in name and name.endswith((".yml", ".yaml"))
    if path.startswith(".github/ISSUE_TEMPLATE/"):
        name = path.removeprefix(".github/ISSUE_TEMPLATE/")
        return "/" not in name and name.endswith((".yml", ".yaml", ".md"))
    if path.startswith("references/"):
        name = path.removeprefix("references/")
        return "/" not in name and name.endswith(".md")
    if path.startswith("scripts/"):
        name = path.removeprefix("scripts/")
        return "/" not in name and name.endswith(".py")
    return False


def normalize_path(path: str) -> str | None:
    if not path or path.startswith("/") or "\\" in path:
        return None
    pure = PurePosixPath(path)
    if any(part in {"", ".", ".."} for part in pure.parts):
        return None
    normalized = pure.as_posix()
    return normalized if normalized == path else None


def is_agent_instruction_doc(path: str) -> bool:
    return (
        path in {"SKILL.md", "AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"}
        or path.startswith("references/")
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


def allowed_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    if host in ALLOWED_AGENT_DOC_HOSTS:
        return True
    return host.endswith(".example.com")


def scan_text(path: str, text: str, errors: list[str]) -> None:
    for idx, ch in enumerate(text):
        if ch in INVISIBLE_OR_BIDI:
            error(errors, f"{path}: forbidden invisible/bidi Unicode U+{ord(ch):04X} at character {idx}")
            break
        codepoint = ord(ch)
        if codepoint < 32 and ch not in "\n\r\t":
            error(errors, f"{path}: forbidden control character U+{codepoint:04X}")
            break

    for number, line in enumerate(text.splitlines(), start=1):
        if len(line) > MAX_TEXT_LINE:
            error(errors, f"{path}:{number}: line exceeds {MAX_TEXT_LINE} characters")
            break

    if path.endswith(".md") and DANGEROUS_SCHEME_RE.search(text):
        error(errors, f"{path}: dangerous URL scheme is not allowed")

    if is_agent_instruction_doc(path):
        visible = strip_fenced_code(text)
        if "<!--" in visible or "-->" in visible:
            error(errors, f"{path}: HTML comments are forbidden in agent-consumed documentation")
        if DANGEROUS_HTML_RE.search(visible):
            error(errors, f"{path}: hidden/active HTML is forbidden in agent-consumed documentation")
        if re.search(r"!\s*\[[^\]]*\]\s*\(", visible):
            error(errors, f"{path}: remote/embedded Markdown images are forbidden in agent-consumed documentation")

        for match in URL_RE.findall(text):
            candidate = match.rstrip(".,;:!?)]}")
            parsed = urllib.parse.urlparse(candidate)
            if not parsed.hostname or not allowed_host(parsed.hostname):
                error(errors, f"{path}: external URL host is not allowlisted: {candidate}")


def extract_permissions_block(text: str) -> list[str] | None:
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line == "permissions:":
            start = idx + 1
            break
        if line.startswith("permissions:") and line != "permissions:":
            return [line]
    if start is None:
        return None
    block: list[str] = []
    for line in lines[start:]:
        if line and not line.startswith((" ", "\t")) and not line.lstrip().startswith("#"):
            break
        block.append(line)
    return block


def run_blocks(text: str) -> Iterable[str]:
    lines = text.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        match = re.match(r"^(\s*)run:\s*(.*)$", line)
        if not match:
            idx += 1
            continue
        indent = len(match.group(1))
        inline = match.group(2)
        if inline and inline not in {"|", ">", "|-", ">-"}:
            yield inline
            idx += 1
            continue
        block: list[str] = []
        idx += 1
        while idx < len(lines):
            current = lines[idx]
            if current.strip() and len(current) - len(current.lstrip()) <= indent:
                break
            block.append(current)
            idx += 1
        yield "\n".join(block)


def scan_workflow(path: str, text: str, errors: list[str]) -> None:
    permissions = extract_permissions_block(text)
    if permissions is None:
        error(errors, f"{path}: workflow must declare explicit top-level permissions")
    else:
        joined = "\n".join(permissions)
        if re.search(r"(?m)^\s*[A-Za-z0-9_-]+:\s*write\s*$", joined):
            error(errors, f"{path}: write-capable GITHUB_TOKEN permissions are forbidden")
    if re.search(r"(?m)^permissions:\s*write-all\s*$", text):
        error(errors, f"{path}: write-all permissions are forbidden")

    if "${{ secrets." in text or "secrets[" in text:
        error(errors, f"{path}: repository/environment secrets are forbidden in workflows")
    if re.search(r"(?m)^\s*runs-on:\s*.*self-hosted", text):
        error(errors, f"{path}: self-hosted runners are forbidden for this public repository")
    if "workflow_run:" in text:
        error(errors, f"{path}: workflow_run trigger is forbidden")
    if "pull_request_target:" in text and path != ".github/workflows/pr-security.yml":
        error(errors, f"{path}: pull_request_target is reserved for the deterministic PR security gate")
    if UNTRUSTED_EVENT_RE.search(text):
        error(errors, f"{path}: untrusted-content event trigger is forbidden")

    uses = ACTION_USE_RE.findall(text)
    for use in uses:
        if use.startswith("./") or use.startswith("docker://"):
            error(errors, f"{path}: local/Docker actions are forbidden: {use}")
            continue
        if "@" not in use:
            error(errors, f"{path}: malformed action reference: {use}")
            continue
        action, ref = use.rsplit("@", 1)
        if not FULL_SHA_RE.fullmatch(ref):
            error(errors, f"{path}: action must be pinned to a full commit SHA: {use}")
        if action == "actions/checkout":
            if text.count("persist-credentials: false") < text.count("actions/checkout@"):
                error(errors, f"{path}: every actions/checkout use must set persist-credentials: false")

    forbidden_shell = re.compile(
        r"(?:curl\b|wget\b|pip\s+install\b|python\s+-m\s+pip\s+install\b|npm\s+install\b|\bnpx\b|apt(?:-get)?\s+install\b|brew\s+install\b)",
        re.IGNORECASE,
    )
    for block in run_blocks(text):
        if "${{" in block:
            error(errors, f"{path}: GitHub expression interpolation inside run blocks is forbidden; pass values through env")
        if forbidden_shell.search(block):
            error(errors, f"{path}: network/package-install command in run block is forbidden")


def check_skill_structure(files: dict[str, str], errors: list[str], max_age_days: int) -> None:
    skill = files.get("SKILL.md", "")
    if not skill.startswith("---\n") or "\n---\n" not in skill[4:]:
        error(errors, "SKILL.md: missing valid frontmatter delimiters")
    else:
        closing = skill.find("\n---\n", 4)
        frontmatter = skill[4:closing]
        if not re.search(r"(?m)^name:\s*\S+", frontmatter):
            error(errors, "SKILL.md: frontmatter is missing name")
        if not re.search(r"(?m)^description:\s*(?:>|\S+)", frontmatter):
            error(errors, "SKILL.md: frontmatter is missing description")

    routed = set(ROUTED_REFERENCE_RE.findall(skill))
    if not routed:
        error(errors, "SKILL.md: no routed references found")
    for path in sorted(routed):
        if path not in files:
            error(errors, f"SKILL.md: routed reference does not exist: {path}")

    dates: list[date] = []
    for path in ("README.md", "references/source-policy.md"):
        for value in AUDIT_DATE_RE.findall(files.get(path, "")):
            try:
                dates.append(date.fromisoformat(value))
            except ValueError:
                error(errors, f"{path}: invalid audit date {value}")
    unique_dates = sorted(set(dates))
    if not unique_dates:
        error(errors, "audit/review date not found in README.md or references/source-policy.md")
    elif len(unique_dates) != 1:
        error(errors, f"audit/review dates disagree: {unique_dates}")
    else:
        age = (date.today() - unique_dates[0]).days
        if age < 0:
            error(errors, f"audit date {unique_dates[0]} is in the future")
        elif age > max_age_days:
            error(errors, f"audit snapshot is {age} days old (limit {max_age_days}); human review required")


def scan_file_set(entries: list[tuple[str, str, int, bytes]], max_age_days: int) -> list[str]:
    errors: list[str] = []
    files: dict[str, str] = {}

    seen_paths = {path for path, _, _, _ in entries}
    for required in sorted(REQUIRED_FILES):
        if required not in seen_paths:
            error(errors, f"required security/integrity file is missing: {required}")

    for path, mode, size, raw in entries:
        if normalize_path(path) is None:
            error(errors, f"invalid repository path: {path!r}")
            continue
        if not is_allowed_path(path):
            error(errors, f"file type/path is not allowlisted for this text-only skill repository: {path}")
        if mode in {"120000", "160000"}:
            error(errors, f"symlinks/submodules are forbidden: {path} (mode {mode})")
        if mode.endswith("755") or mode.endswith("775") or mode.endswith("777"):
            error(errors, f"executable files are forbidden: {path} (mode {mode})")
        if size > MAX_FILE_SIZE:
            error(errors, f"file exceeds {MAX_FILE_SIZE} bytes: {path} ({size})")
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            error(errors, f"non-UTF-8/binary content is forbidden: {path}")
            continue
        files[path] = text
        scan_text(path, text, errors)
        if path.startswith(".github/workflows/"):
            scan_workflow(path, text, errors)

    codeowners = files.get(".github/CODEOWNERS", "")
    if "/.github/" not in codeowners or "/SKILL.md" not in codeowners or "/AGENTS.md" not in codeowners:
        error(errors, ".github/CODEOWNERS must explicitly protect .github, SKILL.md, and AGENTS.md")

    check_skill_structure(files, errors, max_age_days)
    return errors


def local_entries(root: Path) -> list[tuple[str, str, int, bytes]]:
    entries: list[tuple[str, str, int, bytes]] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts:
            continue
        if path.is_dir():
            continue
        rel = path.relative_to(root).as_posix()
        st = path.lstat()
        if stat.S_ISLNK(st.st_mode):
            entries.append((rel, "120000", st.st_size, b""))
            continue
        mode = "100755" if st.st_mode & stat.S_IXUSR else "100644"
        entries.append((rel, mode, st.st_size, path.read_bytes()))
    return entries


def api_json(url: str, token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "google-cx-agent-studio-skill-pr-security/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def remote_pr_entries(repository: str, pr_number: int, token: str) -> list[tuple[str, str, int, bytes]]:
    base = f"https://api.github.com/repos/{repository}"
    pr = api_json(f"{base}/pulls/{pr_number}", token)
    head_sha = pr["head"]["sha"]
    tree = api_json(f"{base}/git/trees/{head_sha}?recursive=1", token)
    if tree.get("truncated"):
        raise RuntimeError("GitHub tree response was truncated; refusing to scan incomplete PR head")

    entries: list[tuple[str, str, int, bytes]] = []
    for item in tree.get("tree", []):
        if item.get("type") == "tree":
            continue
        path = item["path"]
        mode = item.get("mode", "")
        size = int(item.get("size") or 0)
        if item.get("type") != "blob":
            entries.append((path, mode, size, b""))
            continue
        if size > MAX_FILE_SIZE:
            entries.append((path, mode, size, b""))
            continue
        blob = api_json(f"{base}/git/blobs/{item['sha']}", token)
        if blob.get("encoding") != "base64":
            raise RuntimeError(f"Unexpected blob encoding for {path}: {blob.get('encoding')}")
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

    try:
        if args.pr_number is not None:
            repository = args.repository or os.environ.get("GITHUB_REPOSITORY")
            token = os.environ.get("GITHUB_TOKEN")
            if not repository or not token:
                print("ERROR: PR mode requires GITHUB_REPOSITORY and GITHUB_TOKEN", file=sys.stderr)
                return 2
            entries = remote_pr_entries(repository, args.pr_number, token)
        else:
            entries = local_entries(Path(args.root).resolve())
    except (OSError, RuntimeError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        print(f"ERROR: security scanner could not build a complete repository view: {exc}", file=sys.stderr)
        return 2

    errors = scan_file_set(entries, args.max_audit_age_days)
    for item in errors:
        print(f"ERROR: {item}", file=sys.stderr)
    if errors:
        return 1
    print("Repository security checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
