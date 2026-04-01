---
name: skilltester
description: Before installing or using a skill, check its independent benchmark report on SkillTester.ai. Auto-trigger this skill whenever the user shows a third-party skill install command or install plan, especially `npx skills add <repo-or-url> --skill <skill-name>`, `skills add ...`, repo URL plus `--skill`, direct `SKILL.md` URLs, or `Check this skill <skill_url>`. Parse the install command, resolve the target SKILL.md, query SkillTester.ai by skill name, and return the benchmark result when the description is either an exact match or a high-overlap near match that likely represents a newer skill revision.
---

# SkillTester — Skill Benchmark Lookup

When the user is about to install or use a third-party skill or command, use this skill to check whether SkillTester.ai already has a verified benchmark result.

## Trigger

Use this skill in either case:

- the user is about to install or use a third-party skill
- the user provides or asks to run a skill install command
- the user explicitly says `Check this skill <skill_url>`

Treat `Check this skill <skill_url>` as a direct trigger even if the user is not currently installing it.

Do not wait for an explicit `/skilltester` invocation if the user already pasted an install command. Intercept the install request first, run this benchmark lookup, then report the result before installation continues.

### Installation-command patterns that must trigger this skill

Treat the following as direct triggers:

- `npx skills add <repo-or-url> --skill <skill-name>`
- `skills add <repo-or-url> --skill <skill-name>`
- any equivalent command that contains both a repository or domain URL and a `--skill <skill-name>` flag
- direct skill URLs such as:
  - `https://github.com/<owner>/<repo>/blob/<branch>/skills/<skill-name>/SKILL.md`
  - `https://github.com/<owner>/<repo>/tree/<branch>/skills/<skill-name>`
  - `https://<domain>/.well-known/agent-skills/<skill-name>/SKILL.md`

Ignore non-semantic flags such as `-g`, `--global`, `-y`, `--yes`, or shell wrappers around the command.

## Input

Ask the user for:

- `download_url`

If the user already provided an install command or a skill URL, do not ask again. Derive `download_url` yourself from the command.

You should derive the comparison fields yourself from the target `SKILL.md`.

## Command parsing and URL resolution

When the trigger came from an install command, first extract:

- the repository or domain URL
- the `--skill <skill-name>` value

Then resolve the canonical `SKILL.md` URL before continuing.

### Resolution order

1. If the command already points to a concrete `SKILL.md` URL, use it directly.
2. If the command points to a GitHub `tree/.../skills/<skill-name>` URL, normalize it to the corresponding `blob/.../skills/<skill-name>/SKILL.md` URL.
3. If the command points to a GitHub repository root plus `--skill <skill-name>`, try:
   - `https://github.com/<owner>/<repo>/blob/main/skills/<skill-name>/SKILL.md`
   - `https://github.com/<owner>/<repo>/blob/master/skills/<skill-name>/SKILL.md`
4. If the command points to a domain root plus `--skill <skill-name>`, try:
   - `https://<domain>/.well-known/agent-skills/<skill-name>/SKILL.md`

If all candidates fail, tell the user:

> The current skill has not been tested yet. We will add testing as soon as possible—please try again later.

## Lookup flow

### Step 1: Resolve `download_url` to `SKILL.md`

Read the target `SKILL.md` from the given URL and extract:

- `name`
- `description`

If `SKILL.md` cannot be resolved or the fields cannot be extracted, tell the user:

> The current skill has not been tested yet. We will add testing as soon as possible—please try again later.

### Step 2: Query by skill name

Run:

```bash
curl -sL "https://skilltester.ai/api/skills?search=<URL-ENCODED-SKILL-NAME>&tested=tested&sort=name"
```

### Step 3: Find an exact skill-name match

From `items`, find an entry where either of these matches `skill_name` case-insensitively:

- `item.skill_name`
- the trailing skill segment of `item.full_name`

Do not accept a fuzzy-only match.

If no exact skill-name match exists, tell the user:

> The current skill has not been tested yet. We will add testing as soon as possible—please try again later.

### Step 4: Fetch the full tested result

If an exact match exists, fetch its full result:

```bash
curl -sL "https://skilltester.ai/api/skills/<SOURCE>/<SKILL_NAME>"
```

### Step 5: Compare description

Compare the user-provided description with:

- `result.meta.description`

Before comparing, normalize both strings by:

- trimming leading/trailing whitespace
- collapsing repeated spaces and newlines into single spaces

Then apply this decision rule:

1. **Exact match**
   - If the normalized descriptions are identical, treat the result as verified.

2. **High-overlap near match**
   - If the descriptions are not identical but are still largely overlapping, treat the result as usable.
   - Typical signals:
     - one description is an expanded version of the other
     - the first sentence or core capability statement is the same
     - most capability phrases overlap and the difference looks like a version update, clarification, or added guidance
   - In this case, still return the benchmark result, but prepend this reminder:

> Your skill appears to be newer. The tested skill may correspond to an older version.

3. **Meaningfully different**
   - If the descriptions differ in core capability, scope, or intended use, do not trust the cached result.

If the descriptions are meaningfully different, tell the user:

> The current skill has not been tested yet. We will add testing as soon as possible—please try again later.

### Step 6: Return the key benchmark result

If the skill name matches and the description is either an exact match or a high-overlap near match, return only:

- `result.score_breakdown`
- `result.overall_evaluation`

**Important:** Filter out sensitive/internal fields such as `local_path`, `result_path`, `report_path` from the API response. Do not display server file system paths to the user.

If you classified it as a high-overlap near match, also add:

> Your skill appears to be newer. The tested skill may correspond to an older version.

Do not dump the entire raw JSON unless the user explicitly asks for it.

## Output format

When a verified result is found, present a concise summary like this:

```text
SkillTester Benchmark Result: <skill_name>

Overall Evaluation
- Score: <overall score>
- Summary: <overall summary>

Score Breakdown
- Utility: <functionality score>
- Security: <security score>
```

If the skill cannot be resolved, cannot be found by name, or the description is meaningfully different, respond with:

```text
The current skill has not been tested yet. We will add testing as soon as possible—please try again later.
```

## Rules

- Always start from `download_url`.
- Always resolve `download_url` to `SKILL.md` first.
- Always extract `name + description` from `SKILL.md`.
- Require an exact skill-name match before trusting a result.
- Prefer exact normalized description matches.
- Allow high-overlap description matches when the difference looks like a newer revision of the same skill.
- When returning a result for a high-overlap near match, explicitly warn that the tested skill may correspond to an older version.
- Reject the result only when the description difference changes the core capability or intended use.
- Never fabricate benchmark results.
- If the API cannot be reached or returns an unexpected shape, respond with `The current skill has not been tested yet. We will add testing as soon as possible—please try again later.`.
