# BERTopic Tuning GitHub Productization Design

## Objective

Turn the existing semantic-first BERTopic skill into a repository that a new
visitor can understand, install, invoke, trust, and share in under five
minutes. Preserve the current modeling contract and all 190 passing tests.

## Approved scope

The repository will receive one complete productization pass:

- a proof-first README with an exact install path and `$bertopic-tuning`
  invocation;
- a small, executable quickstart built from the existing validators;
- Linux and Windows CI using current official GitHub Actions versions;
- contributor, security, support, conduct, issue, and pull-request files;
- Codex skill UI metadata, icons, and a standalone plugin manifest;
- a custom social-preview image and release-ready changelog;
- repository metadata, Topics, Discussions, a semantic version tag, and a
  GitHub release.

## User journey

The first README screen must answer, in this order:

1. What problem does this solve?
2. What makes it different from metric-only BERTopic tuning?
3. How do I install it?
4. What exact prompt invokes it?
5. What evidence shows that it works?

Deeper assurance-level, semantic-review, champion-chain, and artifact details
remain available below the quickstart instead of occupying the entry screen.

## Architecture decisions

- Keep the repository root as the canonical skill root; do not duplicate the
  skill under a second `skills/` tree.
- Point `.codex-plugin/plugin.json` at the repository root so the same source
  supports direct skill installation and plugin installation.
- Do not change BERTopic modeling behavior in this pass. README and examples
  must describe the tested behavior rather than introduce new promises.
- Use the existing standard-library test suite as the CI contract. No runtime
  dependency installation is needed.
- Use UTF-8 explicitly on every operating system.
- Cross-link Research Project Builder as the upstream research-design
  companion without bundling or duplicating either project.

## Visual direction

Use a dark indigo field with layered semantic clusters, one highlighted
champion path, and restrained cyan/violet accents. The social preview must be
readable at GitHub card size and contain only the project name, the line
"Semantic-first BERTopic tuning", and a short proof cue. The skill icons use
the same cluster-and-path motif without small text.

## Acceptance criteria

- A clean clone passes `python -X utf8 -B -m unittest discover -s scripts/tests`.
- CI runs on Ubuntu and Windows and shows a green badge in the README.
- The README contains exact user-level and repository-level install commands,
  an exact `$bertopic-tuning` prompt, a verified quickstart, and expected
  output.
- The example command runs successfully against committed fixtures.
- Skill metadata and plugin manifests pass their official local validators.
- All community links resolve.
- GitHub displays an accurate description, Topics, Discussions, custom social
  preview, version tag, and release.

## Baseline evidence

On 2026-08-13, the isolated skill-named worktree passed all 190 unit tests in
approximately 11 seconds. The implementation must not reduce that count or
weaken those contracts.
