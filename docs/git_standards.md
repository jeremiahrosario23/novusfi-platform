# NovusFi Engineering: Git Standards & Workflow Guide

This document outlines the strict version control standards for the NovusFi platform. To maintain a clean, readable, and highly traceable repository, all engineers must adhere to this three-tier workflow: **Branching, Committing, and Merging.**

---

## 1. Branch Naming Conventions
Branch names must be highly descriptive, predictable, and strictly formatted using **kebab-case** (lowercase words separated by hyphens). Do not use spaces, underscores, or camelCase.

**Standard Format:** `type/brief-description` or `type/TICKET-ID-description`

### The Complete List of Branch Types:
These prefixes follow the universal Conventional Commits standard used across the industry.

* **`feat/`** – **Features:** New pipelines, models, or major additions. *(e.g., `feat/add-exchange-rate-api`)*
* **`fix/`** – **Bug Fixes:** Repairing broken code, failing DAGs, or data drift. *(e.g., `fix/gold-row-count-anomaly`)*
* **`refactor/`** – **Refactoring:** Rewriting code to improve readability or structure without changing its output behavior. *(e.g., `refactor/notebooks-to-scripts`)*
* **`chore/`** – **Maintenance:** Routine tasks, renaming folders, updating dependencies, or tweaking configurations. *(e.g., `chore/rename-medallion-folders`)*
* **`docs/`** – **Documentation:** Updating READMEs, architecture diagrams, or code comments. *(e.g., `docs/update-architecture-diagram`)*
* **`test/`** – **Testing:** Adding missing tests or correcting existing ones (e.g., dbt tests, pytest). *(e.g., `test/add-silver-null-checks`)*
* **`perf/`** – **Performance:** Code changes explicitly targeting performance/compute improvements. *(e.g., `perf/optimize-pyspark-joins`)*
* **`ci/`** – **Continuous Integration:** Changes to CI configuration files and scripts (GitHub Actions, Databricks Workflows). *(e.g., `ci/add-dbt-prod-job`)*
* **`build/`** – **Build System:** Changes that affect the build system or external dependencies. *(e.g., `build/upgrade-dbt-databricks-version`)*
* **`revert/`** – **Reversions:** Reverting a previous commit. *(e.g., `revert/drop-faulty-gold-table`)*

---

## 2. Commit Messages & The Imperative Present Rule
Commit messages describe exactly what will happen to the codebase if the commit is merged. They must follow the Conventional Commits format.

**The Golden Rule:** A commit message should perfectly complete this sentence: *"If applied, this commit will __________"*

**Standard Format:** `<type>(<scope>): <imperative summary>`

* **Type:** The exact same prefixes used for branches (`feat`, `fix`, `chore`, etc.).
* **Scope (Optional but recommended):** The specific folder, layer, or pipeline being modified. There is no rigid global dictionary for scopes; use what accurately describes your blast radius. Examples: `(repo)`, `(src)`, `(api)`, `(bronze)`, `(dbt)`.
* **Imperative Summary:** Start with an action verb. **NEVER** use past tense (e.g., *Added*) or continuous tense (e.g., *Adding*).

### Examples of Good vs. Bad Commits:
* ❌ (Incorrect tense) `Added parameterization to the bronze script` 
* ❌ (Vague) `Fixing some stuff in the api`
* ✅ `feat(bronze): add catalog parameterization`
* ✅ `fix(api): resolve timeout error during extraction`
* ✅ `feat(src): initialize core pipeline folders`

---

## 3. Pull Requests (PR) / Merge Requests (MR)
A Pull Request description is your pitch to the Senior Engineer or reviewer explaining *why* the code is safe to merge. It must be easily scannable.

* **PR Title:** Should strictly follow the Conventional Commit format (e.g., `refactor(repo): initiate monorepo novusfi-platform`).
* **Tense:** PR descriptions should use clear past tense or present perfect (e.g., *"Restructured folders"*, *"Replaced hardcoded variables"*) because you are describing work you have already completed on your branch.
* **Visual Proof:** Always attach a screenshot of a successful DAG run, a green `dbt debug` log, or a SQL query proving the code works.

### The Standard PR Template
*Copy and paste this markdown template into every Pull Request description:*

```text
## Summary
<!-- One to two sentences summarizing the overarching goal of this PR. -->

## What Changed
- <!-- Bullet point detailing a specific technical change -->
- <!-- Bullet point detailing another specific technical change -->
- <!-- Bullet point on configuration updates, if any -->

## Verification & Testing
- <!-- How did you verify this? (e.g., "Ran dbt run locally against dev_finance catalog and all checks passed.") -->
- <!-- Attach screenshot of successful Databricks/dbt execution below -->
```

---

## 4. The Enterprise Merge Strategy
When closing the PR and merging the feature branch into `main`, we avoid dumping messy, incremental commits into the main history.

### Squash and Merge
Always use the **Squash and Merge** feature in GitHub/GitLab. This takes all the tiny commits made on your feature branch (e.g., *"fix typo"*, *"forgot comma"*) and compresses them into one single, pristine commit on the `main` branch.

### Finalizing the Merge Commit
When you finalize the Squash and Merge, configure the text box as follows:

1. **The Title:** Use the Conventional Commits format, but append the PR number at the very end in parentheses.
   * *Example:* `refactor(repo): initiate monorepo novusfi-platform (#3)`
2. **The Extended Description:** **Delete the auto-generated list of messy commit titles.** GitHub will try to list every commit you made; erase them. Replace them entirely with the clean bullet points from your **"What Changed"** section of the PR template.

This ensures the `main` branch history remains a clean, readable, high-level ledger of every major change without redundant clutter.

---

## 5. Post-Merge Cleanup
Once a PR is successfully merged, **always delete the feature branch.** This practice keeps the repository clean, prevents "stale branch" confusion, and aligns perfectly with Trunk-Based Development, where `main` is the only persistent branch.

--- 

Stay hungry, stay foolish 🦆
