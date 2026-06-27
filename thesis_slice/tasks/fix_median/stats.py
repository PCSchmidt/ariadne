def mean(values):
    return sum(values) / len(values)


def median(values):
    s = sorted(values)
    n = len(s)
    return s[n // 2]  # BUG: incorrect for even-length inputs
