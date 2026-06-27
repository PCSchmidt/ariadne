# fix_median (bug fix)

`stats.py` provides `mean(values)` and `median(values)`. There is a bug: the
median is wrong for even-length inputs. Fix `stats.py` so both functions are
correct for all non-empty inputs.

- `mean` returns a float average.
- `median` returns the middle value for odd-length inputs, and the average of
  the two middle values for even-length inputs. Input may be unsorted.

Fix the existing code; do not change the function names or signatures.
