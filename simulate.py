import csv
import heapq
import random
from collections import OrderedDict, defaultdict, deque

from sortedcontainers import SortedDict
from tqdm import tqdm


def get_sequence(filename, t1, t2):
    min_offset = float("inf")
    max_offset = float("-inf")
    sequence = []
    with open(filename, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            timestamp = int(row[0])
            if t1 <= timestamp <= t2:
                offset = int(row[2])
                operation = row[4].strip()
                sequence.append((offset, operation))

                if offset < min_offset:
                    min_offset = offset
                if offset > max_offset:
                    max_offset = offset

    return sequence, int((max_offset - min_offset) / (4096 * 100))


def get_random_sequence(filename, desired_length=10000):
    timestamps = []
    with open(filename, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            timestamp = int(row[0])
            timestamps.append(timestamp)

    # Ensure that the file has enough data
    if len(timestamps) < desired_length:
        raise ValueError(
            f"Not enough data in the file. Need at least {desired_length} rows."
        )

    # Pick a random start index for the sequence
    start_index = random.randint(0, len(timestamps) - desired_length)
    start_time = timestamps[start_index]

    # Set the end time to cover the range that will give us `desired_length` rows
    end_time = timestamps[start_index + desired_length - 1]

    sequence = []
    with open(filename, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            timestamp = int(row[0])
            if start_time <= timestamp <= end_time:
                offset = int(row[2])
                operation = row[4].strip()
                sequence.append((offset, operation))

    return sequence


def get_random_sequences(filename, desired_length=10000, num_times=10):
    timestamps = []
    with open(filename, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            timestamp = int(row[0])
            timestamps.append(timestamp)

    # Ensure that the file has enough data
    if len(timestamps) < desired_length:
        raise ValueError(
            f"Not enough data in the file. Need at least {desired_length} rows."
        )

    sequences = []
    for _ in tqdm(range(num_times), desc="Generating sequences", unit="seq"):
        # Pick a random start index for the sequence
        start_index = random.randint(0, len(timestamps) - desired_length)
        start_time = timestamps[start_index]

        # Set the end time to cover the range that will give us `desired_length` rows
        end_time = timestamps[start_index + desired_length - 1]

        sequence = []
        with open(filename, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                timestamp = int(row[0])
                if start_time <= timestamp <= end_time:
                    offset = int(row[2])
                    operation = row[4].strip()
                    sequence.append((offset, operation))

        sequences.append(sequence)

    return sequences


def sim_lru(sequence, cache_size):
    cache = OrderedDict()
    seen = set()

    # Initialize counters
    total_read_hits = 0
    total_read_misses = 0
    total_write_hits = 0
    total_write_misses = 0
    total_read_requests = 0
    total_write_requests = 0
    total_requests = 0

    for offset, operation in sequence:
        total_requests += 1

        if operation == "Read":
            total_read_requests += 1
        elif operation == "Write":
            total_write_requests += 1

        if offset in cache:
            # Cache hit
            cache.move_to_end(offset)  # Mark as MRU
            if operation == "Read":
                total_read_hits += 1
            elif operation == "Write":
                total_write_hits += 1
        else:
            # Cache miss
            if offset not in seen:
                seen.add(offset)
            if operation == "Read":
                total_read_misses += 1
            elif operation == "Write":
                total_write_misses += 1

            # Evict LRU if cache is full
            if len(cache) >= cache_size:
                cache.popitem(last=False)

            # Add to cache
            cache[offset] = None

    # Calculate totals
    total_cache_hits = total_read_hits + total_write_hits
    total_cache_misses = total_read_misses + total_write_misses

    return (
        total_read_hits,
        total_read_misses,
        total_write_hits,
        total_write_misses,
        total_read_requests,
        total_write_requests,
        total_requests,
        total_cache_hits,
        total_cache_misses,
    )


def sim_nhit(sequence, cache_size, insertion_threshold, trigger_threshold):
    access_count = defaultdict(int)
    cache = {}
    sorted_cache = SortedDict()

    total_read_hits = total_read_misses = total_write_hits = total_write_misses = 0
    total_read_requests = total_write_requests = total_requests = 0

    for offset, operation in sequence:
        total_requests += 1
        if operation.lower() == "read":
            total_read_requests += 1
        elif operation.lower() == "write":
            total_write_requests += 1

        prev_nhit = access_count[offset]

        access_count[offset] += 1
        new_nhit = access_count[offset]

        if offset in cache:
            cache[offset] = new_nhit

            sorted_cache[prev_nhit].remove(offset)
            if not sorted_cache[prev_nhit]:
                del sorted_cache[prev_nhit]

            if new_nhit not in sorted_cache:
                sorted_cache[new_nhit] = deque()
            sorted_cache[new_nhit].append(offset)

            if operation.lower() == "read":
                total_read_hits += 1
            elif operation.lower() == "write":
                total_write_hits += 1

        else:
            if operation.lower() == "read":
                total_read_misses += 1
            elif operation.lower() == "write":
                total_write_misses += 1

            if len(cache) / cache_size >= trigger_threshold:
                if prev_nhit >= insertion_threshold:
                    if len(cache) >= cache_size:
                        min_nhit, blocks = sorted_cache.peekitem(0)
                        evict_offset = blocks.popleft()
                        if not blocks:
                            del sorted_cache[min_nhit]

                        del cache[evict_offset]

                    cache[offset] = new_nhit
                    if new_nhit not in sorted_cache:
                        sorted_cache[new_nhit] = deque()
                    sorted_cache[new_nhit].append(offset)
            else:
                cache[offset] = new_nhit
                if new_nhit not in sorted_cache:
                    sorted_cache[new_nhit] = deque()
                sorted_cache[new_nhit].append(offset)

    total_cache_hits = total_read_hits + total_write_hits
    total_cache_misses = total_read_misses + total_write_misses

    return (
        total_read_hits,
        total_read_misses,
        total_write_hits,
        total_write_misses,
        total_read_requests,
        total_write_requests,
        total_requests,
        total_cache_hits,
        total_cache_misses,
    )


def sim_arc(sequence, cache_size):
    """
    Simulates the ARC (Adaptive Replacement Cache) policy.

    :param sequence: Iterable of tuples (page, operation), where operation is 'Read' or 'Write'.
    :param cache_size: Maximum number of pages the cache can hold.
    :return: Tuple containing detailed cache statistics.
    """
    # Initialize ARC structures
    T1 = OrderedDict()  # Recently used
    T2 = OrderedDict()  # Frequently used
    B1 = OrderedDict()  # Ghost list for T1
    B2 = OrderedDict()  # Ghost list for T2
    p = 0  # Target size for T1

    # Initialize counters
    total_read_hits = 0
    total_read_misses = 0
    total_write_hits = 0
    total_write_misses = 0
    total_read_requests = 0
    total_write_requests = 0
    total_requests = 0

    for page, operation in sequence:
        total_requests += 1

        if operation == "Read":
            total_read_requests += 1
        elif operation == "Write":
            total_write_requests += 1
        else:
            raise ValueError(f"Unknown operation type: {operation}")

        hit = False  # Flag to indicate cache hit

        # Cache Hit: Page is in T1 or T2
        if page in T1:
            T1.pop(page)
            T2[page] = True  # Move to T2 as it's now frequently used
            hit = True
            if operation == "Read":
                total_read_hits += 1
            else:
                total_write_hits += 1
        elif page in T2:
            T2.move_to_end(page)  # Update position to mark as recently used
            hit = True
            if operation == "Read":
                total_read_hits += 1
            else:
                total_write_hits += 1
        # Ghost Hit: Page is in B1 or B2
        elif page in B1:
            # Adjust target size p
            p = min(cache_size, p + max(1, len(B2) // max(1, len(B1))))
            B1.pop(page)
            T2[page] = True  # Move to T2 as it's now frequently used
            # Evict if necessary
            if len(T1) + len(T2) > cache_size:
                if len(T1) > p:
                    old, _ = T1.popitem(last=False)
                    B1[old] = True
                else:
                    old, _ = T2.popitem(last=False)
                    B2[old] = True
            hit = False
            if operation == "Read":
                total_read_misses += 1
            else:
                total_write_misses += 1
        elif page in B2:
            # Adjust target size p
            p = max(0, p - max(1, len(B1) // max(1, len(B2))))
            B2.pop(page)
            T2[page] = True  # Move to T2 as it's now frequently used
            # Evict if necessary
            if len(T1) + len(T2) > cache_size:
                if len(T1) > p:
                    old, _ = T1.popitem(last=False)
                    B1[old] = True
                else:
                    old, _ = T2.popitem(last=False)
                    B2[old] = True
            hit = False
            if operation == "Read":
                total_read_misses += 1
            else:
                total_write_misses += 1
        else:
            # Cache Miss: Page is not in any list
            if len(T1) + len(T2) == cache_size:
                if len(T1) < cache_size:
                    if B2:
                        B2.popitem(last=False)
                        T2.popitem(last=False)
                else:
                    old, _ = T1.popitem(last=False)
                    B1[old] = True
            elif (
                len(T1) + len(T2) < cache_size
                and (len(T1) + len(T2) + len(B1) + len(B2)) >= 2 * cache_size
            ):
                if len(T1) + len(T2) + len(B1) + len(B2) > 2 * cache_size:
                    if B1:
                        B1.popitem(last=False)
                    else:
                        B2.popitem(last=False)

            T1[page] = True  # Add to T1 as it's recently used
            hit = False
            if operation == "Read":
                total_read_misses += 1
            else:
                total_write_misses += 1

        # Ensure total size constraints
        while len(T1) + len(T2) > cache_size:
            if len(T1) > p:
                if T1:
                    old, _ = T1.popitem(last=False)
                    B1[old] = True
            else:
                if T2:
                    old, _ = T2.popitem(last=False)
                    B2[old] = True

        while len(T1) + len(T2) + len(B1) + len(B2) > 2 * cache_size:
            if len(B1) > p:
                if B1:
                    B1.popitem(last=False)
            else:
                if B2:
                    B2.popitem(last=False)

    # Calculate totals
    total_cache_hits = total_read_hits + total_write_hits
    total_cache_misses = total_read_misses + total_write_misses

    return (
        total_read_hits,
        total_read_misses,
        total_write_hits,
        total_write_misses,
        total_read_requests,
        total_write_requests,
        total_requests,
        total_cache_hits,
        total_cache_misses,
    )


def sim_larc(sequence, cache_size):
    """
    Simulates the Lazy Adaptive Replacement Cache (LARC) policy.

    :param sequence: Iterable of tuples (page, operation), where operation is 'Read' or 'Write'.
    :param cache_size: Maximum number of pages the cache can hold.
    :return: Tuple containing detailed cache statistics.
    """
    # Initialize ARC structures
    T1 = OrderedDict()  # Recently used (temporary)
    T2 = OrderedDict()  # Frequently used (permanent)
    B1 = OrderedDict()  # Ghost list for T1
    B2 = OrderedDict()  # Ghost list for T2
    p = 0  # Target size for T1

    # Initialize counters
    total_read_hits = 0
    total_read_misses = 0
    total_write_hits = 0
    total_write_misses = 0
    total_read_requests = 0
    total_write_requests = 0
    total_requests = 0

    for page, operation in sequence:
        total_requests += 1

        if operation == "Read":
            total_read_requests += 1
        elif operation == "Write":
            total_write_requests += 1
        else:
            raise ValueError(f"Unknown operation type: {operation}")

        hit = False  # Flag to indicate cache hit

        # Cache Hit: Page is in T1 or T2
        if page in T1:
            T1.pop(page)
            T2[page] = True  # Move to T2 as it's now frequently used
            hit = True
            if operation == "Read":
                total_read_hits += 1
            else:
                total_write_hits += 1
        elif page in T2:
            T2.move_to_end(page)  # Update position to mark as recently used
            hit = True
            if operation == "Read":
                total_read_hits += 1
            else:
                total_write_hits += 1
        # Ghost Hit: Page is in B1 or B2
        elif page in B1:
            # Adjust target size p
            p = min(cache_size, p + max(1, len(B2) // max(1, len(B1))))
            B1.pop(page)
            T2[page] = True  # Move to T2 as it's now frequently used
            hit = False
            if operation == "Read":
                total_read_misses += 1
            else:
                total_write_misses += 1
        elif page in B2:
            # Adjust target size p
            p = max(0, p - max(1, len(B1) // max(1, len(B2))))
            B2.pop(page)
            T2[page] = True  # Move to T2 as it's now frequently used
            hit = False
            if operation == "Read":
                total_read_misses += 1
            else:
                total_write_misses += 1
        else:
            # Cache Miss: Page is not in any list
            if len(T1) + len(T2) == cache_size:
                if len(T1) >= 1 and (len(T1) > p):
                    evict_page, _ = T1.popitem(last=False)
                    B1[evict_page] = True  # Add to B1
                else:
                    evict_page, _ = T2.popitem(last=False)
                    B2[evict_page] = True  # Add to B2
            elif (
                len(T1) + len(T2) < cache_size
                and (len(T1) + len(T2) + len(B1) + len(B2)) >= 2 * cache_size
            ):
                if len(T1) + len(T2) + len(B1) + len(B2) > 2 * cache_size:
                    if B1:
                        B1.popitem(last=False)
                    else:
                        B2.popitem(last=False)

            # Add the new page to T1
            T1[page] = True
            hit = False
            if operation == "Read":
                total_read_misses += 1
            else:
                total_write_misses += 1

        # Adjust cache if necessary (Deferred Cleanup)
        while len(T1) + len(T2) > cache_size:
            if len(T1) > p:
                evict_page, _ = T1.popitem(last=False)
                B1[evict_page] = True  # Add to B1
            else:
                evict_page, _ = T2.popitem(last=False)
                B2[evict_page] = True  # Add to B2

        while len(B1) + len(B2) > cache_size:
            if B1:
                B1.popitem(last=False)
            else:
                B2.popitem(last=False)

    # Calculate totals
    total_cache_hits = total_read_hits + total_write_hits
    total_cache_misses = total_read_misses + total_write_misses

    return (
        total_read_hits,
        total_read_misses,
        total_write_hits,
        total_write_misses,
        total_read_requests,
        total_write_requests,
        total_requests,
        total_cache_hits,
        total_cache_misses,
    )


def sim_oracle_belady(sequence, cache_size):
    # Initialize cache as a set for O(1) lookups
    cache = set()

    # Priority queue (heap) to store (-next_use, page)
    # Using negative because heapq is a min-heap, and we need max-heap behavior
    heap = []

    # Map to keep track of the current next use of each page in cache
    next_use_map = {}

    # Statistics
    stats = {
        "total_read_hit": 0,
        "total_read_miss": 0,
        "total_write_hit": 0,
        "total_write_miss": 0,
        "total_write_requests": 0,
        "total_read_requests": 0,
        "total_requests": 0,
        "total_cache_hit": 0,
        "total_cache_miss": 0,
    }

    # Preprocess: Map each page to a deque of its future indices
    future_uses = defaultdict(deque)
    for idx, (page, operation) in enumerate(sequence):
        future_uses[page].append(idx)

    for idx, (current_page, operation) in enumerate(sequence):
        stats["total_requests"] += 1

        # Update read/write request counters
        if operation == "Read":
            stats["total_read_requests"] += 1
        elif operation == "Write":
            stats["total_write_requests"] += 1

        # Remove the current index from future uses
        future_uses[current_page].popleft()

        # Determine the next use of the current page
        if future_uses[current_page]:
            next_use = future_uses[current_page][0]
        else:
            next_use = float("inf")

        if current_page in cache:
            # Cache Hit
            stats["total_cache_hit"] += 1
            if operation == "Read":
                stats["total_read_hit"] += 1
            elif operation == "Write":
                stats["total_write_hit"] += 1

            # Update the next use in the heap
            next_use_map[current_page] = next_use
            heapq.heappush(heap, (-next_use, current_page))
        else:
            # Cache Miss
            stats["total_cache_miss"] += 1
            if operation == "Read":
                stats["total_read_miss"] += 1
            elif operation == "Write":
                stats["total_write_miss"] += 1

            if len(cache) < cache_size:
                # If there's space, simply add the page
                cache.add(current_page)
                next_use_map[current_page] = next_use
                heapq.heappush(heap, (-next_use, current_page))
            else:
                # Need to evict the page with the farthest next use
                while heap:
                    farthest_next_use, page_to_evict = heapq.heappop(heap)
                    farthest_next_use = -farthest_next_use
                    # Verify if this is the current next use of the page
                    if next_use_map.get(page_to_evict, -1) == farthest_next_use:
                        break  # Found the correct page to evict
                else:
                    # This should not happen, but in case the heap is empty
                    page_to_evict = None

                if page_to_evict is not None:
                    cache.remove(page_to_evict)
                    del next_use_map[page_to_evict]

                # Add the current page to cache
                cache.add(current_page)
                next_use_map[current_page] = next_use
                heapq.heappush(heap, (-next_use, current_page))

    return (
        stats["total_read_hit"],
        stats["total_read_miss"],
        stats["total_write_hit"],
        stats["total_write_miss"],
        stats["total_read_requests"],
        stats["total_write_requests"],
        stats["total_requests"],
        stats["total_cache_hit"],
        stats["total_cache_miss"],
    )


def sim_nhit_lru(sequence, cache_size, insertion_threshold, trigger_threshold):
    cache = OrderedDict()
    access_count = defaultdict(int)  # Track how many times each block has been accessed

    # Initialize counters
    total_read_hits = 0
    total_read_misses = 0
    total_write_hits = 0
    total_write_misses = 0
    total_read_requests = 0
    total_write_requests = 0
    total_requests = 0

    for offset, operation in sequence:
        total_requests += 1

        if operation == "Read":
            total_read_requests += 1
        elif operation == "Write":
            total_write_requests += 1

        # Increment access count for the block
        access_count[offset] += 1

        if offset in cache:
            # Cache hit
            cache.move_to_end(offset)  # Mark as MRU
            if operation == "Read":
                total_read_hits += 1
            elif operation == "Write":
                total_write_hits += 1
        else:
            # Cache miss
            if operation == "Read":
                total_read_misses += 1
            elif operation == "Write":
                total_write_misses += 1

            if len(cache) / cache_size >= trigger_threshold:
                # Only cache the block if it has been accessed at least N times
                if access_count[offset] >= insertion_threshold:
                    # Evict LRU if cache is full
                    if len(cache) >= cache_size:
                        cache.popitem(last=False)

                    # Add to cache
                    cache[offset] = None
            else:
                cache[offset] = None

    # Calculate totals
    total_cache_hits = total_read_hits + total_write_hits
    total_cache_misses = total_read_misses + total_write_misses

    return (
        total_read_hits,
        total_read_misses,
        total_write_hits,
        total_write_misses,
        total_read_requests,
        total_write_requests,
        total_requests,
        total_cache_hits,
        total_cache_misses,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Simulate cache replacement policies on a block-level storage trace."
    )
    parser.add_argument("--file", required=True, help="Path to the trace CSV.")
    parser.add_argument("--t1", type=float, default=0.0, help="Include requests with timestamp >= t1.")
    parser.add_argument("--t2", type=float, default=float("inf"), help="Include requests with timestamp <= t2.")
    parser.add_argument("--nhit-threshold", type=int, default=5, help="N-Hit admission threshold (default: %(default)s).")
    parser.add_argument("--trigger", type=float, default=0.5, help="N-Hit trigger ratio (default: %(default)s).")
    args = parser.parse_args()

    sequence, cache_size = get_sequence(args.file, args.t1, args.t2)

    print("FILENAME:", args.file)
    print("Cache Size:", cache_size)

    print("LRU Results:", sim_lru(sequence, cache_size))
    print("NHIT Results:", sim_nhit(sequence, cache_size, args.nhit_threshold, args.trigger))
    print("NHIT-LRU Results:", sim_nhit_lru(sequence, cache_size, args.nhit_threshold, args.trigger))
    print("ARC Results:", sim_arc(sequence, cache_size))
    print("LARC Results:", sim_larc(sequence, cache_size))
    print("Belady Results:", sim_oracle_belady(sequence, cache_size))
