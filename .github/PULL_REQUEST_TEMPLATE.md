<!--
  Thanks for the PR! Keep this short — one or two sentences per section
  is enough. Delete sections that don't apply.
-->

## Summary

<!-- What this change does and why. Link the issue it fixes if any. -->

## Notes for the reviewer

<!--
  Anything reviewers should know before reading the diff:
  - Output changes? Regenerated tests/golden/ via `uv run python tests/capture_golden.py`?
  - New node type? Mention which Mintlify component it maps to.
  - Behaviour change vs bugfix?
-->

## Checks

- [ ] `uv run pytest` passes locally
- [ ] `uv run ruff format --check .` and `uv run ruff check .` are clean
- [ ] `uv run mypy sphinx_mintlify_output` is clean
- [ ] Golden corpus refreshed if rendered output changed
