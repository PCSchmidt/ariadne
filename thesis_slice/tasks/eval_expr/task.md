# eval_expr

Implement `evaluate(expr)` in `solution.py`.

Evaluate an arithmetic expression given as a string and return the result as a
**float**.

- Supported: non-negative integer and decimal literals, binary `+ - * /`, unary
  minus, and parentheses.
- Standard precedence: parentheses, then unary minus, then `*` and `/`, then
  `+` and `-`. Operators of equal precedence are left-associative.
- `/` is floating-point division.
- Whitespace is insignificant.

Examples of intent (not the test values): `"2+3*4"` -> `14.0`,
`"(1+2)*-3"` -> `-9.0`, `"10/4"` -> `2.5`.
