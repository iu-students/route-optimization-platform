# ADR-006: Hosted Documentation via GitHub Pages

**Status:** Accepted

**Quality requirements addressed:** QR-005

## Context

Assignment 5 requires a browsable hosted documentation site that exposes the maintained documentation (architecture, process, quality, testing) as readable pages. The team needed a hosting approach that is free, automatically deploys from the repository, and requires no additional infrastructure.

Options considered:
- GitHub Pages with a static site generator 
- GitLab Pages
- Manual deployment to a cloud storage bucket 
- Hosting the Flask API's own documentation route

## Decision

Use GitHub Pages with the repository's built-in deployment from the `docs/` directory. The site is served at `https://iu-students.github.io/route-optimization-platform/`. Markdown files in `docs/` are rendered directly by GitHub Pages with automatic table-of-contents navigation.

## Rationale

- GitHub Pages is free, public, and deploys automatically on every push to the default branch - no separate CI job or deployment script needed.
- The `docs/` directory source maps directly to the rendered site path, keeping the hosted documentation structure identical to the repository structure.

## Consequences

### Positive

- Documentation stays version-controlled in the repository - the hosted site always reflects `main`.
- No additional deployment infrastructure or credentials needed.
- The site URL is stable and predictable from the repository name.

### Negative

- GitHub Pages renders Markdown with a default theme - custom branding or layout changes require Jekyll configuration.
- Diagrams embedded as SVG or PNG in Markdown render inline, but PlantUML source files are not automatically rendered - the team must commit pre-rendered SVG outputs or use a PlantUML GitHub Action.
- Private repositories require a paid GitHub plan for Pages; the repository must remain public for free hosting.

### Tradeoffs

- MkDocs with the `mkdocs-material` theme was considered for richer navigation and search, but was rejected because it requires a separate CI deployment workflow and adds a build step that could fail independently of the main CI pipeline.

## Links

- [QR-005: Hosted documentation availability](../../quality-requirements.md#qr-005-hosted-documentation-availability)
- [docs/](../../)
