# Fork development guide

This guide is for `madhakish/legion-data`. Upstream architecture remains in [CLAUDE.md](../CLAUDE.md); this file is the canonical fork-local validation and automation guidance. Use the checked-out source and [lib/legion/data/version.rb](../lib/legion/data/version.rb) for current behavior/version, rather than historical example counts.

Agent entrypoints: [AGENTS.md](../AGENTS.md) and the [review-legion-migrations skill](../.agents/skills/review-legion-migrations/SKILL.md).

## Change routing

- The shared schema is `lib/legion/data/migrations/`; `Migration.migrate` calls Sequel's migrator. Local SQLite state has its own migration registration and timestamp semantics. Do not apply the integer-sequence helper to local extension migrations.
- Existing migration IDs are history. Add the next ID, do not renumber or rewrite already-deployed files; review rollback and forward compatibility separately.
- Check adapter guards for PostgreSQL-only types, vector indexes and constraints. SQLite success does not establish PostgreSQL or MySQL compatibility.
- `spec/spec_helper.rb` calls `Legion::Settings.load` and `Legion::Data.setup`. Setup connects and may migrate; even loading the spec helper is not read-only.
- Keep shared and local database paths separate. Use synthetic rows for tenant isolation, audit-chain integrity, retention and encryption tests.

## Safe validation

Do not run the Ruby suite against existing settings or database files. Provision disposable settings, databases and filesystem roots first; the static helper below neither requires Ruby nor reads SQL/database content.

Python 3.9+ is sufficient for the read-only helper; it uses only the standard library:

```sh
python3 scripts/audit_migrations.py
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The audit reports duplicate IDs, malformed filenames and sequence gaps, and suggests the next ID only for a valid sequence. It checks shared migration filenames only; it cannot prove SQL validity, reversibility or deployed database state.

With Ruby >= 3.4 and dependencies provisioned in an approved disposable environment, inspect the spec helper, run the targeted specs, then `bundle exec rspec` and non-mutating `bundle exec rubocop`. Run `bundle check` before installing missing gems. Dependency installation may fetch packages and execute build hooks. If Ruby, dependencies or isolation are absent, report the blocked command; do not label static checks as passing RSpec. Autocorrection (`rubocop -A`) is an explicit code change, not a prerequisite to reading or reviewing this fork.

## GitHub Actions recommendations (not activated)

Gate duplicate/gapped migration IDs first, then disposable SQLite and PostgreSQL adapter tests. Use job-local database credentials and ephemeral storage; never expose the personal host database. Add targeted specs for new migrations; test PostgreSQL-only branches separately.

The checked-in workflows do not verify an available self-hosted runner. Direct jobs in this family use `ubuntu-latest`; reusable jobs call `LegionIO/.github` workflows at mutable `@main`. The inspected upstream workflows use `${{ inputs.runner || 'ubuntu-latest' }}` and these callers do not supply `runner`, so they inherit GitHub-hosted defaults at the reviewed snapshot. Before implementing the requested self-hosted policy, inspect the reusable workflows and the registered runner inventory; choose only verified labels. Do not guess OS/architecture labels or silently fall back to GitHub-hosted runners.

Because this is a public repository, never run unreviewed pull-request code on a personal persistent runner. Prefer an isolated ephemeral runner with no host mounts, production network access or reusable credentials. If only the personal runner exists, keep proposed validation disabled until that isolation is established. A trusted manual dispatch must validate an exact maintainer-reviewed commit; do not use `pull_request_target` to check out and execute a PR head. Minimize token permissions, pin reviewed actions/reusable workflows to immutable SHAs, set timeouts/concurrency, and separate test artifacts from secrets. Release, publishing and infrastructure changes need their own approval. No workflow files are changed by this development overlay.
