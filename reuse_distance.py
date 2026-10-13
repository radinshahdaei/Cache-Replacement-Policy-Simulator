"""Reuse (stack) distance analysis for block-level storage traces.

The reuse distance of an access is the number of *distinct* offsets touched since
the previous access to the same offset (Mattson's stack distance). It is computed
with an order-statistic AVL tree that keeps the most recent occurrence of every
offset in MRU-to-LRU order, so a node's rank is its stack distance.

Trace CSV format (headerless, comma-separated), 8 columns:
    [0] timestamp, [1] unused, [2] offset (cache key), [3] size, [4] Read/Write, ...
Only the offset column ([2]) is used here.
"""

import argparse
import csv

MAX_BUCKET = 256 * 1024


class _Node:
    __slots__ = ("key", "left", "right", "parent", "height", "size")

    def __init__(self, key):
        self.key = key
        self.left = self.right = self.parent = None
        self.height = 1
        self.size = 1


def _height(node):
    return node.height if node is not None else 0


def _size(node):
    return node.size if node is not None else 0


class OrderStatisticTree:
    """AVL tree augmented with subtree sizes.

    Nodes are inserted at the leftmost position, so an in-order traversal yields
    the most-recently-used-first order. A node's rank is therefore the number of
    nodes more recent than it — exactly its stack distance.
    """

    def __init__(self):
        self.root = None
        self._map = {}

    def __contains__(self, key):
        return key in self._map

    def _update(self, node):
        node.height = 1 + max(_height(node.left), _height(node.right))
        node.size = 1 + _size(node.left) + _size(node.right)

    def _balance_factor(self, node):
        return _height(node.left) - _height(node.right)

    def _rotate_left(self, x):
        y = x.right
        x.right = y.left
        if y.left is not None:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y
        self._update(x)
        self._update(y)
        return y

    def _rotate_right(self, x):
        y = x.left
        x.left = y.right
        if y.right is not None:
            y.right.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x is x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        y.right = x
        x.parent = y
        self._update(x)
        self._update(y)
        return y

    def _rebalance(self, node):
        while node is not None:
            self._update(node)
            balance = self._balance_factor(node)
            if balance > 1:
                if self._balance_factor(node.left) < 0:
                    self._rotate_left(node.left)
                node = self._rotate_right(node)
            elif balance < -1:
                if self._balance_factor(node.right) > 0:
                    self._rotate_right(node.right)
                node = self._rotate_left(node)
            node = node.parent

    def insert(self, key):
        """Insert `key` as the new leftmost (most recently used) node."""
        node = _Node(key)
        self._map[key] = node
        if self.root is None:
            self.root = node
            return
        current = self.root
        while current.left is not None:
            current = current.left
        current.left = node
        node.parent = current
        self._rebalance(current)

    def delete(self, key):
        node = self._map.pop(key)
        self._delete_node(node)

    def _delete_node(self, node):
        if node.left is None and node.right is None:
            parent = node.parent
            self._unlink(node)
        elif node.left is None:
            parent = node.parent
            self._replace(node, node.right)
        elif node.right is None:
            parent = node.parent
            self._replace(node, node.left)
        else:
            successor = node.right
            while successor.left is not None:
                successor = successor.left
            node.key = successor.key
            self._map[successor.key] = node
            self._delete_node(successor)
            return
        self._rebalance(parent)

    def _unlink(self, node):
        if node.parent is None:
            self.root = None
        elif node is node.parent.left:
            node.parent.left = None
        else:
            node.parent.right = None

    def _replace(self, node, child):
        child.parent = node.parent
        if node.parent is None:
            self.root = child
        elif node is node.parent.left:
            node.parent.left = child
        else:
            node.parent.right = child

    def rank(self, key):
        """0-based in-order position of `key` (= number of more-recent nodes)."""
        node = self._map[key]
        rank = _size(node.left)
        while node.parent is not None:
            if node is node.parent.right:
                rank += _size(node.parent.left) + 1
            node = node.parent
        return rank


def _bucket_label(value):
    if value < 1024:
        return str(value)
    return f"{value // 1024}K"


def _buckets():
    buckets = {"0": 0}
    value = 1
    while value <= MAX_BUCKET:
        buckets[_bucket_label(value)] = 0
        value *= 2
    buckets[f">{_bucket_label(MAX_BUCKET)}"] = 0
    return buckets


def _label_for_distance(distance):
    """Smallest power of two >= distance (0 maps to "0")."""
    if distance <= 0:
        return "0"
    value = 1
    while value < distance:
        value *= 2
    if value > MAX_BUCKET:
        return f">{_bucket_label(MAX_BUCKET)}"
    return _bucket_label(value)


def compute_reuse_distance(path, n_rows=None):
    """Compute the reuse-distance histogram of the trace at `path`.

    Returns a dict with keys "avg", "min", "max", "reuse_events", and "buckets"
    (a power-of-two histogram of reuse distances).
    """
    tree = OrderStatisticTree()
    last_occurrence = {}
    buckets = _buckets()

    total = sum_dist = 0
    min_dist = float("inf")
    max_dist = -1

    with open(path, newline="") as file:
        for i, row in enumerate(csv.reader(file)):
            if n_rows is not None and i >= n_rows:
                break
            offset = int(row[2])
            if offset in last_occurrence:
                distance = tree.rank(last_occurrence[offset])
                total += 1
                sum_dist += distance
                min_dist = min(min_dist, distance)
                max_dist = max(max_dist, distance)
                buckets[_label_for_distance(distance)] += 1
                tree.delete(last_occurrence[offset])
            last_occurrence[offset] = i
            tree.insert(i)

    return {
        "avg": sum_dist / total if total else 0,
        "min": min_dist if total else None,
        "max": max_dist,
        "reuse_events": total,
        "buckets": buckets,
    }


def _print_results(path, results):
    print(f"File: {path}")
    print(f"Reuse events: {results['reuse_events']:,}")
    print(f"Avg reuse distance: {results['avg']:,.2f}")
    min_str = f"{results['min']:,}" if results["min"] is not None else "n/a"
    print(f"Min / max reuse distance: {min_str} / {results['max']:,}")
    print("Histogram (bucket = smallest power of two >= distance):")
    for label, count in results["buckets"].items():
        print(f"  {label:>6}  {count:,}")


def _plot(results, output):
    import matplotlib.pyplot as plt

    labels = list(results["buckets"].keys())
    values = [results["buckets"][label] for label in labels]

    plt.figure(figsize=(12, 6))
    plt.bar(labels, values)
    plt.xlabel("Reuse distance (bucket)")
    plt.ylabel("Count")
    plt.title("Reuse distance histogram")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute the reuse (stack) distance histogram of a storage trace."
    )
    parser.add_argument("--file", required=True, help="Path to the trace CSV.")
    parser.add_argument("--n-rows", type=int, default=None, help="Only read the first N rows (sample).")
    parser.add_argument("--plot", default=None, help="Save a histogram plot to this PNG path.")
    args = parser.parse_args()

    results = compute_reuse_distance(args.file, args.n_rows)
    _print_results(args.file, results)
    if args.plot:
        _plot(results, args.plot)
        print(f"\nPlot saved to {args.plot}")
