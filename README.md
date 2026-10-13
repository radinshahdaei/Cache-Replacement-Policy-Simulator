# Storage Trace Analysis

Tools for analyzing block-level storage I/O traces.

- **`simulate.py`** — cache replacement policies (LRU, N-Hit, N-Hit + LRU, ARC, LARC, Belady's optimal).
- **`locality.py`** — temporal and spatial locality.
- **`reuse_distance.py`** — reuse (stack) distance histogram.

## Usage

```bash
python simulate.py --file trace.csv
python locality.py --file trace.csv --n-rows 100000
python reuse_distance.py --file trace.csv --n-rows 100000 --plot reuse_distance.png
```

Each script accepts `--help` for the full option list. Use `--n-rows` (or `simulate.py --t1` / `--t2`) to sample large traces.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Input format

Headerless CSV with eight columns: `timestamp, unused, offset, size, operation, unused, unused, unused`. The `offset` (column 2) is the cache key; `operation` (column 4) is `Read` or `Write`.

## Documentation

- [replacement-policies.pdf](docs/replacement-policies.pdf) — cache replacement policies
- [locality-a1.pdf](docs/locality-a1.pdf), [locality-a2.pdf](docs/locality-a2.pdf), [locality-a3.pdf](docs/locality-a3.pdf) — locality
- [reuse-distance.pdf](docs/reuse-distance.pdf) — reuse distance
