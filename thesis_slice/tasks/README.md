# Eval task set (gate 0)

Each task is a folder the harness copies into a temp dir per attempt, then runs
`pytest`. **Done == pytest exits 0.**

## Task folder layout

```
tasks/<name>/
  task.md            # natural-language instruction shown to the model
  meta.yaml          # allowed_edit: [files the model may write]; difficulty: <tag>
  <source files>     # stubs / buggy code the model fixes (listed in allowed_edit)
  test_*.py          # the hidden tests; NOT in allowed_edit, NOT shown to the model
```

## Rules that keep the experiment honest

- **Tests are hidden from generation.** Never list a test's expected values in
  `task.md`. The model only sees `task.md` + the editable sources, plus the raw
  pytest failure output on retries. This prevents hardcoding.
- **Test files must NOT be in `allowed_edit`** — the sandbox rejects edits to
  anything outside the allow-list, but keep tests out of it regardless.
- **Vary difficulty** (`trivial`, `easy`, `medium`, `hard`) and include at least
  one multi-file and one bug-fix (not greenfield) task.

## Status

Shipped here as runnable examples: `two_sum` (trivial), `roman_to_int` (easy).
**Gate 0 needs 8 tasks** — add 6 more before trusting the verdict. Two examples
is enough to smoke-test the harness, not to decide the thesis.
