# merge_intervals

Implement `merge(intervals)` in `solution.py`.

`intervals` is a list of `[start, end]` pairs (integers, `start <= end`), in any
order. Return a new list of merged, non-overlapping intervals sorted by start.
Intervals that touch at an endpoint count as overlapping and must be merged
(e.g. `[1, 4]` and `[4, 5]` become `[1, 5]`). An empty input returns `[]`.
