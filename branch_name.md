## 🌳 Standard Branch Naming Conventions

We use a standard naming convention based on semantic prefixes to ensure clarity, maintain the integrity of our codebase, and facilitate automation (CI/CD). All branch names must use **kebab-case** (`-`).

**Format: `[prefix]/[description-in-kebab-case]`**

### 1. Base and Persistent Branches

These branches are the core of our version control system.

| Branch Name   | Purpose                                                                                                                                   | Stability     |
| :------------ | :---------------------------------------------------------------------------------------------------------------------------------------- | :------------ |
| **`main`**    | **Production Code.** Contains the stable, production-ready code. All releases are tagged from this branch.                                | Highly Stable |
| **`develop`** | **Integration Branch.** Contains the latest completed features and fixes, ready for final integration testing before merging into `main`. | Semi-Stable   |

### 2. Working and Feature Branches

These are the primary prefixes for daily development work:

| Prefix          | Scope of Work                  | Impact                                                                                              | Example Branch Name                |
| :-------------- | :----------------------------- | :-------------------------------------------------------------------------------------------------- | :--------------------------------- |
| **`feat/`**     | **New Feature**                | Adds a new capability or significant behavioral change to the system.                               | `feat/implement-oauth-login`       |
| **`fix/`**      | **Bug or Error Correction**    | Resolves an unintended behavior or a general software error (often triggers a patch release).       | `fix/resolve-validation-error`     |
| **`hotfix/`**   | **Urgent Production Fix**      | Critical, immediate fix for a production issue. Created and merged directly from/to `main`.         | `hotfix/critical-payment-failure`  |
| **`refactor/`** | **Refactoring**                | Code structure improvements (readability, performance) without changing external functionality.     | `refactor/simplify-checkout-class` |
| **`chore/`**    | **Maintenance**                | Non-source code changes (e.g., dependency updates, CI/CD configuration, build scripts).             | `chore/update-node-version`        |
| **`docs/`**     | **Documentation**              | Changes only to documentation files (e.g., README, internal guides, manuals).                       | `docs/add-deployment-instructions` |
| **`test/`**     | **Testing or Experimentation** | Adding new tests or highly experimental code (may not be merged).                                   | `test/add-new-unit-tests-suite`    |
| **`style/`**    | **Style/UI Modification**      | Purely aesthetic changes (CSS, layout, colors, typography) that do not affect the functional logic. | `style/align-logo-center`          |
