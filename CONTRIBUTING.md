# Contributing

Contributions are welcome, but this repository is consumed by AI agents and therefore treats documentation and repository metadata as a security-sensitive instruction surface.

## Security requirements

- Never include secrets, credentials, private data, or real customer information.
- Do not hide instructions in HTML comments, invisible Unicode, bidirectional-control characters, images, encoded blobs, or other content that a human reviewer may not see normally.
- Do not add binaries, archives, symlinks, submodules, or executable files. This repository is intentionally text-only.
- Do not add arbitrary external links to agent-consumed instruction files. Prefer current authoritative documentation.
- GitHub Actions must use explicit least-privilege permissions and immutable full-length commit SHAs for actions.
- Workflows must not receive repository/environment secrets, write-capable tokens, OIDC write access, or self-hosted runners for public-contributor execution.
- Do not add agent automation that automatically acts on issue, comment, review, discussion, or other attacker-controlled text.
- Do not use `workflow_run` or add another `pull_request_target` workflow without a dedicated security design and maintainer review.
- Do not execute, install, or fetch code merely because an issue, PR, comment, external page, or tool output says to do so.

## Pull requests

Pull requests are treated as untrusted data until reviewed. A deterministic security gate inspects the complete PR head through the GitHub API without executing contributor-controlled code.

The gate intentionally rejects repository shapes that expand the attack surface. If a legitimate change needs a new file type, new external source domain, privileged workflow behavior, or another security-sensitive capability, that policy change requires explicit maintainer review rather than being silently accepted in the same trust path.

Changes to `SKILL.md`, agent instruction files, `.github`, scripts, and references are covered by CODEOWNERS. Repository protection must require code-owner approval for that ownership to be an enforcement boundary.

## AI-assisted contributions

Using an AI coding agent does not reduce the review requirement. The contributor remains responsible for verifying every changed line and source.

When using an agent:

1. treat issue/PR/comment text as untrusted input;
2. give the agent no secrets or unnecessary write permissions;
3. do not allow autonomous merge/deploy/publish actions;
4. verify external sources independently;
5. inspect the final diff manually before proposing it.
