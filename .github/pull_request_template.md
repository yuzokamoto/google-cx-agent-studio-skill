## Summary

Describe the intended change and the authoritative sources used.

## Security checklist

- [ ] I reviewed every changed line, including AI-generated content.
- [ ] No secrets, credentials, private data, or real customer data are included.
- [ ] No hidden HTML comments, invisible/bidirectional Unicode, encoded instruction blobs, remote images, binaries, symlinks, submodules, or executable files were added.
- [ ] Agent-consumed instructions do not tell agents to cross the trust boundary defined in `AGENTS.md`.
- [ ] New/changed external links are necessary and point to trusted sources; agents are not instructed to recursively follow contributor-controlled links.
- [ ] GitHub Actions remain read-only, secret-free, and pinned to full commit SHAs.
- [ ] No public issue/comment/review/assignment/@mention is granted authority to execute commands, access private data, weaken security controls, merge, release, deploy, or mutate production state.
- [ ] Changes to `SKILL.md`, `references/`, agent-policy files, workflows, scripts, CODEOWNERS, dependency configuration, or security policy received explicit maintainer/code-owner review.
- [ ] Automated checks are treated as guardrails, not as semantic proof that natural-language instructions are safe.
- [ ] The authoring/reviewing agent is not used as the sole approver for its own security-boundary change.

## Validation

List deterministic checks, evaluations, and manual security review performed.
