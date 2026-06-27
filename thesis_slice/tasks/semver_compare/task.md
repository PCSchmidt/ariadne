# semver_compare

Implement `compare(a, b)` in `solution.py`, returning `-1`, `0`, or `1` for
whether semantic version `a` is lower than, equal to, or higher than `b`.

Follow the Semantic Versioning precedence rules:

- A version is `MAJOR.MINOR.PATCH`, optionally followed by a `-prerelease` part
  and/or a `+build` metadata part.
- Compare `MAJOR`, `MINOR`, `PATCH` numerically, in that order.
- **Build metadata (`+...`) is ignored** for precedence.
- A version **with** a prerelease has *lower* precedence than the same version
  without one (e.g. `1.0.0-alpha` < `1.0.0`).
- Prerelease identifiers are dot-separated and compared left to right:
  - identifiers consisting only of digits are compared numerically;
  - numeric identifiers always have *lower* precedence than non-numeric ones;
  - non-numeric identifiers are compared by ASCII order;
  - if all preceding identifiers are equal, the version with *more* identifiers
    has higher precedence.
