# Issue tracker: GitHub

Issues and PRDs for this repository live as GitHub issues. Use the `gh` CLI for all operations and infer the repository from `git remote -v`.

## Conventions

- Create, read, comment on, label, and close issues with the corresponding `gh issue` commands.
- Fetch an issue's full body, comments, and labels before acting on it.
- Pull requests are not a triage or feature-request surface.
- When a skill says to publish to the issue tracker, create a GitHub issue.
- When a skill says to fetch a ticket, read the GitHub issue and its comments.

## Blocking relationships

Use GitHub's native issue dependencies as the canonical, UI-visible representation of blocking edges. Add blockers through the issue dependencies API using the blocker's numeric database ID, not its issue number or node ID.

If native dependencies are unavailable, add a `Blocked by: #<number>` line to the dependent issue body. A ticket is ready only when every blocking issue is closed.
