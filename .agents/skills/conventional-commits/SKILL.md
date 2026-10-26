---
name: conventional-commits
description: Guide and specification for creating git commit messages adhering strictly to the Conventional Commits v1.0.0 specification. Use whenever writing git commit messages, creating commits, squashing branches, or reviewing commit history.
---

# Conventional Commits v1.0.0 Skill

This skill guides AI agents in authoring, reviewing, and validating git commit messages that strictly adhere to the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) specification.

---

## 1. Commit Message Structure

Every commit message must follow this exact structural format:

```text
<type>[optional scope][optional !]: <description>

[optional body]

[optional footer(s)]
```

### Components

1. **Header** (Mandatory, single line):
   - **`type`** (Mandatory): Communicates the intent of the change.
   - **`scope`** (Optional): A noun enclosed in parentheses describing the section of the codebase affected (e.g. `(ui)`, `(audio)`, `(api)`).
   - **`!`** (Optional): Indicates a breaking change when placed immediately before the colon `:`.
   - **`: `** (Mandatory): Colon followed by a single space.
   - **`description`** (Mandatory): A concise summary of the code changes.
2. **Body** (Optional):
   - Must begin one blank line after the description.
   - May consist of multiple newline-separated paragraphs.
   - Explains the context, *why* the change was made, and contrast with previous behavior.
3. **Footer(s)** (Optional):
   - Must begin one blank line after the body (or one blank line after the header if no body exists).
   - Follows git trailer convention: `<token>: <value>` or `<token> #<value>`.
   - Token must use `-` instead of spaces (e.g., `Reviewed-by`, `Refs`, `Fixes`), with the sole exception of `BREAKING CHANGE`.

---

## 2. Commit Types

Use the appropriate type based on the nature of the change:

| Type | When to Use | SemVer Correlation |
| :--- | :--- | :--- |
| **`feat`** | Introduces a new user-facing feature or API capability | **MINOR** |
| **`fix`** | Patches a bug or unintended behavior | **PATCH** |
| **`perf`** | Improves performance (speed, memory, layout, execution time) | **PATCH** |
| **`refactor`** | Code change that neither fixes a bug nor adds a feature | None / **PATCH** |
| **`style`** | Formatting, whitespace, linting rules (no functional code changes) | None |
| **`docs`** | Documentation changes only (README, docstrings, docs/) | None |
| **`test`** | Adding, correcting, or refactoring tests | None |
| **`build`** | Changes affecting build system, packaging, Docker, or dependencies | None / **PATCH** |
| **`ci`** | Changes to CI/CD configuration and scripts (.github/workflows) | None |
| **`chore`** | Maintenance, repository housekeeping, release scripts, vendor updates | None |
| **`revert`** | Reverts a previous commit | Depends |

---

## 3. Breaking Changes

A breaking change must be clearly indicated in one of two ways (or both):

### Option A: The `!` Modifier in Header
Add `!` immediately before the colon:
```text
feat(api)!: change sounds response format to paginated cursor
```

### Option B: The `BREAKING CHANGE` Footer
Include a footer starting with `BREAKING CHANGE:` or `BREAKING-CHANGE:` followed by a space and description:
```text
feat(api): update sounds response structure

BREAKING CHANGE: The `sounds` array in `/api/sounds` has been replaced with a `{ items, next_cursor }` object.
```

---

## 4. Writing Style Guidelines

1. **Imperative Mood**: Use the imperative, present tense in the description:
   - ✅ `add infinite scrolling for sound cards`
   - ❌ `added infinite scrolling` / `adds infinite scrolling`
2. **Casing**:
   - `type` and `scope` must be lowercase.
   - Start `description` with a lowercase letter.
3. **No Trailing Punctuation**: Do not end the description line with a period (`.`).
4. **Length**: Keep the subject/header line to $\le 72$ characters.
5. **Atomic Commits**: Ensure commits represent a single logical unit of change.

---

## 5. Agent Execution Workflow

When preparing to commit changes, follow these steps:

### Step 1: Review Staged Diffs
Run `git status` and `git diff --cached` to verify what is being committed:
```bash
git diff --cached --stat
```

### Step 2: Determine Scope and Intent
Ask:
- Does this add a feature (`feat`), fix a bug (`fix`), optimize performance (`perf`), or reformat code (`style`)?
- Which module or area was affected (e.g. `(audio)`, `(frontend)`, `(api)`, `(deps)`)?
- Does it break backwards compatibility? If yes, use `!` or `BREAKING CHANGE:`.

### Step 3: Format the Message
Construct the commit message adhering strictly to the v1.0.0 specification.

### Step 4: Commit
Execute the commit with `-m` or multi-line quotes:
```bash
git commit -m "feat(ui): add progressive batch loading for sound cards"
```

For commits with a body:
```bash
git commit -m "perf(rendering): decouple audio progress updates from alpine reactivity" -m "Audio timeupdate events now update the DOM directly via data attributes instead of triggering Alpine proxy re-evaluation across all sound cards."
```

---

## 6. Real-World Examples

### Simple Feature
```text
feat(audio): add loop playback mode for individual sounds
```

### Feature with Scope and Body
```text
feat(search): add debounced query filtering

Debounces input by 150ms to prevent main thread lag when typing
in libraries with thousands of sound files.
```

### Bug Fix with Issue Reference
```text
fix(player): prevent audio overlap when solo mode is enabled

Closes #42
```

### Performance Optimization with Body
```text
perf(render): implement progressive batching and content-visibility

Reduces initial DOM nodes from 158k to ~2k cards by rendering in
batches and deferring layout calculations for off-screen cards.
```

### Breaking Change
```text
refactor(config)!: rename SOUNDS_PATH environment variable to SOUNDS_DIR

BREAKING CHANGE: `SOUNDS_PATH` is no longer supported in .env or docker-compose.
Use `SOUNDS_DIR` instead.
```
