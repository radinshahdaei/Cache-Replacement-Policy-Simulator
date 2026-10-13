# Storage Trace Analysis

**A trace-driven study of cache replacement policies, storage-trace locality, and reuse distance.**

This project analyzes real block-level storage I/O traces with three complementary tools:

1. **Replacement policies** ([`simulate.py`](simulate.py)) — six cache-management strategies, from LRU to Belady's optimal.
2. **Locality analysis** ([`locality.py`](locality.py)) — temporal and spatial locality of the workload.
3. **Reuse distance** ([`reuse_distance.py`](reuse_distance.py)) — Mattson's stack-distance distribution.

It was developed as an **Operating Systems course project** to investigate how recency, frequency, adaptive replacement, and knowledge of future accesses affect cache hit rates, and to characterize the locality of the underlying workloads. The full course report is [Document.pdf](Document.pdf) (in Persian).

## Algorithms and analyses

### 1. Cache replacement policies

| Policy | Approach |
| --- | --- |
| **LRU (Least Recently Used)** | Evicts the least recently accessed resident block. |
| **N-Hit** | Tracks access frequency and applies an admission threshold; evicts by access count. |
| **N-Hit + LRU** | Frequency-based admission with LRU eviction. |
| **ARC (Adaptive Replacement Cache)** | Dynamically balances recency and frequency with resident and ghost lists. |
| **LARC (Lazy Adaptive Replacement Cache)** | ARC-like structure with deferred maintenance. |
| **Belady's Optimal** | Uses future requests to choose a victim; an **offline** upper bound, not an online policy. |

The cache capacity is `int((max_offset - min_offset) / (4096 * 100))` — a project-specific approximation of 1% of the observed address span in 4 KiB units (84,807 blocks for A42).

### 2. Locality analysis

- **Temporal locality**, two definitions:
  - *Exact-offset reuse* — the fraction of accesses whose offset reappears within a time window of its previous occurrence.
  - *Range overlap* — the fraction of requests whose `[offset, offset + size)` range overlaps any request from the last `T` seconds.
- **Spatial locality** — each request is classified against a sliding window of recent requests as **sequential**, **overlapping**, **strided**, or **random**.

### 3. Reuse distance

The reuse (stack) distance of an access is the number of *distinct* offsets touched since the previous access to the same offset. It is computed in O(n log n) with an order-statistic AVL tree that keeps the most recent occurrence of every offset in MRU-to-LRU order. The distribution directly predicts cache miss rates: a cache of size *C* hits every access whose reuse distance is `< C`.

## Repository structure

```text
storage-trace-analysis/
├── simulate.py           # Trace loader + six replacement-policy simulators
├── locality.py           # Temporal and spatial locality analysis
├── reuse_distance.py     # Reuse (stack) distance histogram
├── A42.zip               # Compressed public trace
├── Document.pdf          # Full course report (Persian)
├── requirements.txt      # Python dependencies
└── README.md
```

## Getting started

Prerequisites: Python 3.9+ and `pip`.

```bash
git clone https://github.com/radinshahdaei/Storage-Trace-Analysis.git
cd Storage-Trace-Analysis
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
unzip A42.zip                                          # Windows: Expand-Archive A42.zip -DestinationPath . -Force
```

## Usage

Run the six replacement policies on the full A42 trace:

```bash
python simulate.py --file A42.csv
```

Analyze locality on a sample:

```bash
python locality.py --file A42.csv --n-rows 100000 --split total --queue-size 128 --stride-distance 65536
```

Compute the reuse-distance histogram on a sample:

```bash
python reuse_distance.py --file A42.csv --n-rows 100000 --plot reuse_distance.png
```

Every tool accepts `--help` for the full option list. The traces are large (≈5 million requests for A42), so pass `--n-rows` to the analysis tools for a quick sample, or restrict the time window with `simulate.py --t1` / `--t2`.

## Trace format

`A42.csv` is a headerless, comma-separated storage trace with eight fields per record:

| Index | Example value | Meaning |
| --- | --- | --- |
| `0` | `1577808000009424896` | Timestamp (ns) |
| `1` | `-1` | Unused |
| `2` | `4609650688` | Block offset — used as the cache key |
| `3` | `4096` | Request size in bytes |
| `4` | `Read` | Operation (`Read` or `Write`) |
| `5`–`7` | `-1` | Unused |

## Results

The original experiment evaluated four traces — `A42.csv`, `A108.csv`, `A129.csv`, and `A669.csv`. Only **A42** is distributed here (as `A42.zip`); the results for the other three are transcribed from the original report.

### Replacement policies

A42 — 5,087,932 requests, cache capacity 84,807 blocks:

| Policy | Cache hits | Cache misses | Hit rate |
| --- | ---: | ---: | ---: |
| LRU | 2,924,075 | 2,163,857 | 57.47% |
| **N-Hit** | **3,548,563** | **1,539,369** | **69.74%** |
| N-Hit + LRU | 2,966,954 | 2,120,978 | 58.31% |
| ARC | 3,330,441 | 1,757,491 | 65.46% |
| LARC | 2,948,341 | 2,139,591 | 57.95% |
| **Belady's Optimal (offline)** | **4,431,755** | **656,177** | **87.10%** |

Across all four traces (hit rate %):

| Policy | A42 | A108 | A129 | A669 |
| --- | ---: | ---: | ---: | ---: |
| LRU | 57.47% | 25.03% | 62.73% | 96.70% |
| N-Hit | 69.74% | 32.94% | 58.84% | 96.16% |
| N-Hit + LRU | 58.31% | 23.61% | 61.73% | 96.58% |
| ARC | 65.46% | 28.53% | 63.51% | 96.64% |
| LARC | 57.95% | 34.03% | 64.17% | 96.91% |
| Belady's Optimal (offline) | 87.10% | 47.29% | 75.91% | 97.95% |

The relative ranking changes with the workload: N-Hit leads the online policies on A42, LARC leads on A108/A129/A669, and Belady's Optimal is the best on all four, as expected.

### Locality

Spatial locality (fraction of requests per category, stride distance 64 KiB):

| Trace | Queue size | Sequential | Overlapping | Strided | Random |
| --- | ---: | ---: | ---: | ---: | ---: |
| A42 | 64 | 76.67% | 6.01% | 6.49% | 10.83% |
| A42 | 128 | 77.43% | 7.30% | 6.17% | 9.10% |
| A108 | 64 | 88.66% | 2.39% | 3.06% | 5.89% |
| A108 | 128 | 89.33% | 2.88% | 2.94% | 4.85% |
| A129 | 64 | 83.39% | 6.66% | 1.76% | 8.19% |
| A129 | 128 | 84.75% | 7.33% | 1.45% | 6.48% |
| A669 | 64 | 77.46% | 2.07% | 5.57% | 14.90% |
| A669 | 128 | 78.09% | 4.95% | 5.50% | 11.46% |

Temporal locality is low at short windows — only ~7% of requests reuse an offset within a 1-minute window — and rises with the window size, plateauing after roughly an hour.

### Reuse distance

Average, minimum, and maximum reuse distance (in distinct offsets) plus the histogram, per trace (power-of-two buckets; the `0` bucket was always empty):

| Bucket | A42 | A108 | A129 | A669 |
| --- | ---: | ---: | ---: | ---: |
| avg | 65,486 | 324,007 | 235,256 | 7,292 |
| min | 0 | 0 | 0 | 0 |
| max | 154,114 | 1,656,075 | 2,973,720 | 178,209 |
| 1 | 1,127 | 17,841 | 33,570 | 513 |
| 2 | 246 | 15,282 | 31,859 | 131 |
| 4 | 651 | 15,506 | 53,711 | 239 |
| 8 | 79,261 | 20,316 | 48,780 | 8,262 |
| 16 | 138,003 | 105,602 | 180,865 | 14,346 |
| 32 | 70,701 | 214,345 | 559,419 | 21,776 |
| 64 | 60,607 | 499,300 | 714,568 | 29,490 |
| 128 | 104,420 | 501,887 | 656,727 | 160,389 |
| 256 | 160,848 | 567,200 | 533,946 | 188,223 |
| 512 | 80,518 | 261,887 | 307,094 | 129,981 |
| 1K | 66,372 | 227,522 | 258,043 | 479,616 |
| 2K | 68,399 | 336,993 | 282,024 | 3,690,084 |
| 4K | 54,804 | 240,031 | 461,484 | 13,824,218 |
| 8K | 45,991 | 347,200 | 485,149 | 5,948,409 |
| 16K | 46,548 | 306,742 | 417,581 | 1,371,647 |
| 32K | 181,995 | 494,339 | 2,760,648 | 196,362 |
| 64K | 1,013,753 | 447,099 | 752,516 | 315,843 |
| 128K | 2,746,811 | 658,565 | 939,909 | 284,963 |
| 256K | 12,529 | 1,612,585 | 1,632,888 | 401,310 |
| 512K | 0 | 9,176,992 | 1,839,626 | 0 |
| >512K | 0 | 2,479,554 | 1,762,889 | 0 |

A108 and A129 have heavy long-distance reuse tails (millions of accesses in the 512K and >512K buckets); A42 and A669 have none beyond 256K. A669 is the most cache-friendly workload (avg reuse distance 7,292, large mass at 2K–8K); A108 is the least (avg 324,007).

## Reproducibility

Only A42 is downloadable from this repository. The values for A108, A129, and A669 document the original experiments; reproducing those runs requires the corresponding trace files, which are not included. The reuse-distance results above were produced by the original C++ implementation; the Python `reuse_distance.py` computes identical distances and is intended for samples and education — use `--n-rows` to keep it quick on large traces.
