"""Temporal and spatial locality analysis for block-level storage traces.

Trace CSV format (headerless, comma-separated), 8 columns:
    [0] timestamp (ns), [1] unused, [2] offset (bytes), [3] size (bytes),
    [4] operation ("Read" or "Write"), [5..7] unused.
"""

import argparse
import csv
from collections import deque

COL_TIMESTAMP, COL_OFFSET, COL_SIZE, COL_OPERATION = 0, 2, 3, 4


def load_trace(path, n_rows=None):
    """Read a trace, returning parallel lists (timestamps, offsets, sizes, operations)."""
    timestamps, offsets, sizes, operations = [], [], [], []
    with open(path, newline="") as file:
        for i, row in enumerate(csv.reader(file)):
            if n_rows is not None and i >= n_rows:
                break
            timestamps.append(int(row[COL_TIMESTAMP]))
            offsets.append(int(row[COL_OFFSET]))
            sizes.append(int(row[COL_SIZE]))
            operations.append(row[COL_OPERATION].strip())
    return timestamps, offsets, sizes, operations


def split_by_operation(timestamps, offsets, sizes, operations):
    """Split a trace into read / write / total views."""
    def select(kind):
        ts = [t for t, op in zip(timestamps, operations) if op == kind]
        of = [o for o, op in zip(offsets, operations) if op == kind]
        sz = [s for s, op in zip(sizes, operations) if op == kind]
        return ts, of, sz

    return {
        "read": select("Read"),
        "write": select("Write"),
        "total": (timestamps, offsets, sizes),
    }


def temporal_reuse(timestamps, offsets, window_ns):
    """Fraction (%) of accesses whose offset reappears within `window_ns` of its
    previous occurrence (exact-offset reuse between consecutive occurrences)."""
    if not timestamps:
        return 0.0
    last_seen = {}
    count = 0
    for timestamp, offset in zip(timestamps, offsets):
        if offset not in last_seen:
            last_seen[offset] = timestamp
        else:
            if timestamp - last_seen[offset] <= window_ns:
                count += 1
            last_seen[offset] = timestamp
    return 100.0 * count / len(timestamps)


def spatial_locality(offsets, sizes, queue_size, stride_distance):
    """Classify each request against the `queue_size` most recent requests as
    sequential, overlapping, strided, or random; return category percentages."""
    if not offsets:
        return {"sequential": 0.0, "overlapping": 0.0, "strided": 0.0, "random": 0.0}

    sequential = overlapping = strided = random_ = 0
    queue = []

    for address, size in zip(offsets, sizes):
        category = None

        for req_address, req_size in queue:
            if address == req_address + req_size:
                category = "sequential"
                break

        if category is None:
            for req_address, req_size in queue:
                if (req_address <= address <= req_address + req_size) or \
                        (req_address <= address + size <= req_address + req_size) or \
                        (address < req_address and address + size > req_address + req_size):
                    category = "overlapping"
                    break

        if category is None:
            for req_address, req_size in queue:
                if abs(max(address, req_address) - min(address + size, req_address + req_size)) <= stride_distance:
                    category = "strided"
                    break

        if category is None:
            category = "random"

        if category == "sequential":
            sequential += 1
        elif category == "overlapping":
            overlapping += 1
        elif category == "strided":
            strided += 1
        else:
            random_ += 1

        queue.append((address, size))
        if len(queue) > queue_size:
            queue.pop(0)

    total = len(offsets)
    return {
        "sequential": 100.0 * sequential / total,
        "overlapping": 100.0 * overlapping / total,
        "strided": 100.0 * strided / total,
        "random": 100.0 * random_ / total,
    }


def _overlaps(a, b):
    start1, size1 = a
    start2, size2 = b
    return not (start1 + size1 <= start2 or start2 + size2 <= start1)


def temporal_overlap(timestamps, offsets, sizes, window_ns):
    """Fraction of requests whose [offset, offset + size) range overlaps any request
    from the previous `window_ns` nanoseconds (range-overlap sliding window)."""
    rows = sorted(zip(timestamps, offsets, sizes))
    active = deque()
    count = total = 0
    for timestamp, offset, size in rows:
        total += 1
        while active and active[0][0] + window_ns < timestamp:
            active.popleft()
        for _, request in active:
            if _overlaps(request, (offset, size)):
                count += 1
                break
        active.append((timestamp, (offset, size)))
    return count / total if total else 0.0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze temporal and spatial locality of a block-level storage trace."
    )
    parser.add_argument("--file", required=True, help="Path to the trace CSV.")
    parser.add_argument("--n-rows", type=int, default=None, help="Only read the first N rows (sample).")
    parser.add_argument("--split", choices=["read", "write", "total"], default="total",
                        help="Which request subset to analyze (default: %(default)s).")
    parser.add_argument("--queue-size", type=int, default=128,
                        help="Spatial-locality sliding-window size (default: %(default)s).")
    parser.add_argument("--stride-distance", type=int, default=65536,
                        help="Stride distance in bytes (default: %(default)s, i.e. 64 KiB).")
    parser.add_argument("--overlap-window", type=float, default=60.0,
                        help="Temporal-overlap window in seconds (default: %(default)s).")
    args = parser.parse_args()

    timestamps, offsets, sizes, operations = load_trace(args.file, args.n_rows)
    ts, os_, sz = split_by_operation(timestamps, offsets, sizes, operations)[args.split]

    print(f"File: {args.file}  (split={args.split}, n_rows={args.n_rows or len(timestamps)})")
    print()

    print("Temporal locality (exact-offset reuse):")
    for window_seconds in (60, 3600, 43200, 86400):
        pct = temporal_reuse(ts, os_, window_seconds * 1_000_000_000)
        print(f"  {window_seconds:>5}s window: {pct:6.2f}%")
    print()

    ratio = temporal_overlap(ts, os_, sz, args.overlap_window * 1_000_000_000)
    print(f"Temporal locality (range overlap, {args.overlap_window:g}s window): {100 * ratio:.2f}%")
    print()

    spatial = spatial_locality(os_, sz, args.queue_size, args.stride_distance)
    print(f"Spatial locality (queue={args.queue_size}, stride={args.stride_distance}B):")
    for name in ("sequential", "overlapping", "strided", "random"):
        print(f"  {name:>11}: {spatial[name]:6.2f}%")
