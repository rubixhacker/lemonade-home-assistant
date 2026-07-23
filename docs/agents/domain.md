# Domain Docs

This is a single-context repository.

## Before exploring

- Read the root `CONTEXT.md` glossary.
- Read relevant decisions under `docs/adr/`.
- If either location is absent, proceed without creating placeholder documentation.

## Use the glossary vocabulary

Use the canonical terms from `CONTEXT.md` in ticket titles, acceptance criteria, tests, and implementation descriptions. Avoid synonyms that the glossary explicitly rejects.

If a required concept is missing, reconsider whether new terminology is necessary or resolve it through domain modeling before adding it.

## Respect architectural decisions

Surface any conflict with an existing ADR explicitly instead of silently overriding it.
