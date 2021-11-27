import operator


def bisect_right(a, x, lo=0, hi=None, *, key=None):
    """Return the index where to insert item x in list a, assuming a is sorted.
    The return value i is such that all e in a[:i] have e <= x, and all e in
    a[i:] have e > x.  So if x already appears in the list, a.insert(i, x) will
    insert just after the rightmost x already there.
    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() and in heapq.
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            if x < a[mid]:
                hi = mid
            else:
                lo = mid + 1
    else:
        while lo < hi:
            mid = (lo + hi) // 2
            if x < key(a[mid]):
                hi = mid
            else:
                lo = mid + 1
    return lo


def sort_by(t, *arrays, f=None):
    si = sorted(range(len(t)), key=lambda i: t[i])
    all_sorted = [
        (t[i], ) + tuple(arr[i] for arr in arrays)
        for i in si
        if f is None or f(t[i], *tuple(arr[i] for arr in arrays))
    ]
    if len(all_sorted) == 0:
        return tuple([] for _ in range(len(arrays) + 1))
    return tuple(zip(*all_sorted))


def apply_crit(value, crit_proba):
    return (1 + crit_proba * 0.5) * value


def argopt(iterable, cmp=operator.lt, key=None):
    if key is None:
        key = lambda v: v
    opt, opt_idx = None, 0
    for i, v in enumerate(iterable):
        if opt is None or cmp(opt, key(v)):
            opt, opt_idx = key(v), i
    return opt_idx, opt


def argmax(iterable):
    return argopt(iterable)


def argmin(iterable):
    return argopt(iterable, cmp=operator.gt)
