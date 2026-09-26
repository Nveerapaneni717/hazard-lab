# Security policy

## Reporting a vulnerability

Report privately through **GitHub Security Advisories** on this repository
(Security → Advisories → Report a vulnerability). That keeps the report
confidential until a fix exists.

Please do not open a public issue for a security problem, and please do not
include real credentials or personal data in a report - this project never needs
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
| Version-bounded direct dependencies | `requirements.txt` | an unvetted major release arriving silently |

## Recommended repository settings

These live in GitHub settings, not in the code, so they are yours to enable:

1. **Protect `main` with a ruleset** (Settings → Rules → Rulesets) - require a
   pull request, require status checks, and block force pushes and deletions.
   Rulesets supersede the older branch-protection screen. Require the aggregate
   `ci-complete` check rather than each matrix leg: a required check name that
   stops existing blocks every merge until someone works out why.
2. **Require signed commits.** This needs two things, not one: a signing key
   registered to your GitHub account, and git told to use it -
   `git config --global user.signingkey <key-id>` followed by
   `git config --global commit.gpgsign true`. Setting `commit.gpgsign` on its
   own fails at commit time, because there is no key to sign with.
3. **Enable Dependabot alerts, secret scanning and push protection**
   (Settings → Advanced Security; this page was previously called "Code
   security"). Push protection blocks a commit containing a recognised
   credential before it reaches the remote.
4. **Restrict Actions** to "allow actions created by GitHub and verified
   creators", or an explicit allowlist.
5. **Set workflow permissions to read-only by default** (Settings → Actions →
   Workflow permissions).

## A note on action pinning

The workflows here reference actions by major version tag (`@v4`). Pinning to a
full commit SHA is stricter - a tag can be quietly re-pointed at malicious code,
a SHA cannot - and it is the better end state for anything security-sensitive.

**Dependabot will not make that migration for you.** It follows whichever
reference style a workflow already uses: pin by tag and it proposes a newer tag,
pin by SHA and it proposes a newer SHA with the version in a trailing comment.
Moving from tags to SHAs is a manual, one-time edit of every `uses:` line.

This repository ships tags because they keep a Dependabot diff readable, which
matters for a teaching repository. If you are running this somewhere that prices
supply-chain risk above readability, rewrite the `uses:` lines to SHAs yourself -
Dependabot will keep them current from then on.

## What is deliberately not in this repository

- No `.env`, keys, tokens or credentials of any kind.
- No absolute filesystem paths, machine names or user directories.
- No presentation material - it contained third-party branding.
- No large binaries. Data is fetched from source; a 16 KB public-domain sample
  is bundled so the quickstart runs offline.
