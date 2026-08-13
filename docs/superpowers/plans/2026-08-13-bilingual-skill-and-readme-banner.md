# BERTopic Tuning Bilingual Skill and README Banner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the existing BERTopic banner in both GitHub README languages and ship a complete Simplified Chinese skill companion in release `v1.0.1`.

**Architecture:** Keep root `SKILL.md` as the sole Codex runtime entry. Add frontmatter-free Chinese human documentation, package it through the existing Git-index whitelist, and verify image/link/package behavior without changing BERTopic modeling semantics.

**Tech stack:** Markdown, JSON, Python standard library/unittest, deterministic Git-index plugin builder, GitHub Actions and Releases.

## Global constraints

- Preserve every command, path, filename, enum, JSON field, and assurance-level identifier verbatim in the Chinese skill.
- Do not add YAML frontmatter to `SKILL.zh-CN.md`.
- Reuse `assets/social-preview.png`; do not regenerate brand assets.
- Release version is exactly `1.0.1` / tag `v1.0.1`.
- Run all work in `F:\Skill\Codex\.worktrees\bertopic-bilingual-docs`.

---

### Task 1: Add failing bilingual package and README contracts

**Files:**
- Modify: `scripts/tests/test_plugin_packaging.py`

**Interfaces:**
- Consumes: the current whitelist builder, repository READMEs, and manifest.
- Produces: regression coverage for a visible local banner, two language entrypoints, packaged Chinese skill bytes, resolved local links, and version `1.0.1`.

- [ ] Add `urllib.parse.unquote` and a small local-Markdown-target resolver that parses real README/skill links.
- [ ] Add a test requiring `README.zh-CN.md`, `SKILL.zh-CN.md`, language cross-links, and a resolved `assets/social-preview.png` image in both READMEs.
- [ ] Extend the real-package test to require byte-identical `skills/bertopic-tuning/SKILL.zh-CN.md` and zero broken local links.
- [ ] Change the manifest/changelog release assertions to `1.0.1` while retaining the `1.0.0` history assertion.
- [ ] Run `python -X utf8 -B -m unittest scripts.tests.test_plugin_packaging -v` and confirm failures are caused only by the missing Chinese files/banner/package/version.

### Task 2: Add bilingual documents and package projection

**Files:**
- Create: `README.zh-CN.md`
- Create: `SKILL.zh-CN.md`
- Modify: `README.md`
- Modify: `.codex-plugin/package-policy.json`
- Modify: `.codex-plugin/plugin.json`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: canonical `README.md`, `SKILL.md`, existing brand asset, package policy schema.
- Produces: two navigable README pages, a complete Chinese skill companion, and an indexed package destination `skills/bertopic-tuning/SKILL.zh-CN.md`.

- [ ] Add README language/skill links and the local banner immediately after badges.
- [ ] Translate the complete README into Simplified Chinese with all commands and proof values unchanged.
- [ ] Translate the complete skill body into Simplified Chinese, prepend the canonical-English notice, and omit frontmatter.
- [ ] Add exactly one whitelist mapping from root `SKILL.zh-CN.md` to `skills/bertopic-tuning/SKILL.zh-CN.md`.
- [ ] Set manifest version `1.0.1` and add the dated changelog entry plus release comparison link.
- [ ] Stage all intended files because the builder reads Git-index blobs.
- [ ] Run the focused test again and confirm it passes.

### Task 3: Verify, publish, and release

**Files:**
- Verify: all tracked repository files and built artifacts.

**Interfaces:**
- Consumes: the staged/committed bilingual release candidate.
- Produces: merged `main`, tag `v1.0.1`, and deterministic release ZIP.

- [ ] Run `python -X utf8 -B -m unittest discover -s scripts/tests -v`.
- [ ] Compile all Python scripts and run the official root skill validator.
- [ ] Build two fresh plugin directories and ZIPs with `--codex-home`, compare byte/tree hashes, and validate the unpacked skill/plugin.
- [ ] Check UTF-8, Markdown links, banner dimensions, `git diff --check`, and clean status.
- [ ] Commit, push, open a PR, wait for both GitHub Actions jobs, merge into `main`, and verify the remote tree.
- [ ] Create tag/release `v1.0.1`, upload the deterministic ZIP, and verify the README banner and release URLs over HTTPS.
