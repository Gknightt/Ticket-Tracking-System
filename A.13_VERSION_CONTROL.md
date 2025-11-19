# A.13 - Version Control and Source Code Repository

Purpose: Document the repository URL, branching and tagging strategies, commit message conventions, and code review guidelines to ensure collaborative and stable development.

**Repository URL**
- **GitHub:** `https://github.com/Gknightt/Ticket-Tracking-System`
- **Current working branch (example):** `enzo/dev_11/12/25`

**Branching Strategy (Git Flow - recommended)**
- **Main branches:**
  - `main` : Production-ready code. Always deployable.
  - `develop` : Integration branch for features; reflects latest delivered development changes.
- **Supporting branches:**
  - `feature/<short-description>` : New features. Branch off `develop`. Merge back to `develop` via pull request.
  - `release/<version>` : Prepare a new release; branch off `develop`. Used to finalize version, run final QA, and bump version. Merge into `main` and `develop`.
  - `hotfix/<short-description>` : Fixes for production. Branch off `main`. Merge back into `main` and `develop`.
  - `support/*` or `chore/*` : Maintenance work, infra changes.

**Branch Naming Guidelines**
- Use lowercase, hyphens as separators. Examples:
  - `feature/add-email-notifications`
  - `hotfix/fix-login-error`
  - `release/1.2.0`

**Branch Protection & Merge Policy**
- Protect `main` and `develop` with required checks: passing CI, lint, unit tests, and at least one review approval.
- Require PRs (pull requests) for merging into `develop` or `main`.
- Use `squash` or `merge` strategy consistently across the repo. Prefer `squash` for small features to keep history linear, or `merge commits` to preserve feature history—decide and document team-wide.

**Tagging & Releases**
- Follow Semantic Versioning: `vMAJOR.MINOR.PATCH` (e.g., `v1.2.0`).
- Create annotated tags for releases: `git tag -a v1.2.0 -m "Release v1.2.0"` and push with `git push origin v1.2.0`.
- Release process: create `release/<version>` branch → finalize changes and changelog → merge into `main` → tag `main` with `vX.Y.Z` → create release notes in GitHub Releases.

**Commit Message Guidelines**
- Follow Conventional Commits for clear history: `<type>(<scope>): <short description>`
  - `feat:` a new feature
  - `fix:` a bug fix
  - `chore:` changes to the build process or auxiliary tooling
  - `docs:` documentation only changes
  - `style:` formatting, missing semi-colons, etc.
  - `refactor:` code change that neither fixes a bug nor adds a feature
  - `perf:` a code change that improves performance
  - `test:` adding missing tests or correcting existing tests
- Body (optional): Explain the motivation and contrast with the previous behavior.
- Footer (optional): Reference issues, e.g., `Closes #123`.

Example commit messages:
```
feat(email): add welcome email for new users

Adds a new template and background worker task to send welcome emails when a user registers.

Closes #456
```

```
fix(auth): correct token expiry check

Fixes incorrect logic that allowed expired tokens to be accepted.
```

**Pull Request & Code Review Guidelines**
- PR Title: concise summary same as commit subject, e.g., `feat: add email templates`.
- PR Description: explain what changed, why, and include screenshots or steps to test. Reference related issues: `Fixes #<issue>`.
- Reviewer assignment: add at least one reviewer from the owning team or `CODEOWNERS` entries.
- Checklist for reviewers (example):
  - [ ] Code compiles / tests pass locally
  - [ ] Unit / integration tests added or updated where applicable
  - [ ] No obvious performance regressions
  - [ ] Security considerations addressed (input validation, auth checks)
  - [ ] Documentation updated if public APIs changed
- Require at least one approving review before merging; two approvals for major changes.

**CI Checks & Required Statuses**
- Ensure CI pipeline runs on PRs: linting, unit tests, static analysis, and any security scanning.
- Do not merge unless all required checks succeed.

**Code Ownership and Reviews**
- Use `CODEOWNERS` file (optional) to auto-request reviewers for specific paths.
- Encourage review feedback to be constructive and focused on correctness, readability, and maintainability.

**Hotfix and Rollback Process**
- For production issues, create a `hotfix/<desc>` branch from `main`, apply fix, run CI, merge to `main` and `develop`, tag release, and deploy.
- If a release needs rollback, create a new commit that reverts the release commit or redeploy the previous tag; follow post-mortem process.

**Recommended Git Commands / Workflows**
- Start a feature:
  - `git checkout develop`
  - `git pull origin develop`
  - `git checkout -b feature/short-description`
- Finish a feature (locally):
  - `git add -A`
  - `git commit -m "feat(scope): short description"`
  - `git push origin feature/short-description`
  - Open a PR to `develop` and request review
- Create a hotfix:
  - `git checkout main`
  - `git pull origin main`
  - `git checkout -b hotfix/fix-desc`

**PR Template (example)**
```
## Summary
- What does this change do?

## Testing
- How to test locally?

## Checklist
- [ ] Tests added
- [ ] Documentation updated

Closes: #<issue>
```

**Enforcement & Automation**
- Protect branches in repository settings.
- Configure required CI checks, codeowners, and merge rules in GitHub/GitLab.
- Optionally enable required signed commits and two-factor auth for the organization.

---
If you'd like, I can also add a short pointer to this file in the project's `ReadMe.md` or create a `CODEOWNERS` and PR template file. Which would you prefer next?
