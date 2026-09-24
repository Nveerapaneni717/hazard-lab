# Security policy

## Reporting a vulnerability

Report privately through **GitHub Security Advisories** on this repository
(Security → Advisories → Report a vulnerability). That keeps the report
confidential until a fix exists.

Please do not open a public issue for a security problem, and please do not
include real credentials or personal data in a report — this project never needs
either.

Expect an acknowledgement within a week.

## What this project handles

`hazard-lab` reads public climate and catastrophe data and does arithmetic on
it. It has **no authentication, no user accounts, no database, no network
listener, and no secrets**. It does not phone home.

That limits the attack surface sharply, and the controls below are aimed at the
realistic risks for a repository like this one: a malicious or compromised
dependency, an accidentally committed credential, and an unreviewed change.

## Controls in this repository

| Control | Where | What it stops |
|---|---|---|
| Secret scanning at commit time | `.pre-commit-config.yaml` (gitleaks) | credentials reaching history |
| Secret scanning in CI | `.github/workflows/ci.yml` | credentials reaching `main` |
| Scanner config + allowlist | `.gitleaks.toml` | one documented false positive, narrowly scoped |
| Static analysis | CodeQL workflow | injection, unsafe deserialisation |
| Dependency audit | `pip-audit` in CI | known-vulnerable packages |
| Dependency updates | `.github/dependabot.yml` | staying on vulnerable versions |
| Least-privilege CI | `permissions:` block in every workflow | token abuse if a job is compromised |
| No secrets in workflows | by construction | nothing to exfiltrate |
| Pinned direct dependencies | `requirements.txt` | surprise upgrades |

## Recommended repository settings

These live in GitHub settings, not in the code, so they are yours to enable:

1. **Branch protection on `main`** — require a pull request, require CI to pass,
   disallow force-push.
2. **Require signed commits.** Set up with `git config commit.gpgsign true` and
   a key registered to your account.
3. **Enable Dependabot alerts and secret scanning** (Settings → Code security).
   Push protection will block a commit containing a recognised credential.
4. **Restrict Actions** to "allow actions created by GitHub and verified
   creators", or an explicit allowlist.
5. **Set workflow permissions to read-only by default** (Settings → Actions →
   Workflow permissions).

## A note on action pinning

The workflows here reference actions by major version tag (`@v4`). Pinning to a
full commit SHA is stricter — it defeats a tag being re-pointed at malicious
code — and is the right end state.

This repository ships tags rather than SHAs because an unverified SHA is worse
than a tag: it fails closed and looks like a broken build. Dependabot is
configured for the `github-actions` ecosystem, so enabling it will propose the
pinned SHAs for you, and you can accept them with the provenance intact.

## What is deliberately not in this repository

- No `.env`, keys, tokens or credentials of any kind.
- No absolute filesystem paths, machine names or user directories.
- No presentation material — it contained third-party branding.
- No large binaries. Data is fetched from source; a 16 KB public-domain sample
  is bundled so the quickstart runs offline.
