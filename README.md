# LIFELINE: Algorithmic Relief-Command Engine

DAA semester project, FAST-NUCES Islamabad (BS Data Science and AI).
Group 69: Muhammad Umar (22I-0644), Haider Ali (22I-0502), Awwab Ahmed (23I-0079), all Section AI-A.

## Status
- Iteration 1 (data and algorithm selection): complete.
- Iteration 2 (implementation and evaluation): implementation, campaign, experiment round 1 (113 points, all OK), and analysis. The current test suite has 53 tests.

## Setup
Python 3.11.6.

    pip install -r requirements.txt

The master dataset (release `master_release_v1`, 2026-11-12) must be in `Master Dataset/archive/` (20 CSV files + `CHECKSUMS.txt`). It is not committed (350 MB, see `.gitignore`); `data/MASTER_VERSION.md` records the release, our sample and every SHA-256.

## One command
    python -m src.main all          # verify checksums, run all tests, the 7-day campaign, the experiments, the analysis

Sub-commands:

    python -m src.main verify                    # SHA-256 of every master file against CHECKSUMS.txt
    python -m src.main test                      # pytest tests -q
    python -m src.main campaign [case_id ...]    # default: 1-06 1-26 2-40 2-48 4-47
    python -m src.main experiments [A1 A2 B1 B2 C1 D1] [--smoke]
    python -m src.main analyse [--smoke]         # fits.csv + plots from results.csv

## Problem definitions (Iteration 2 modules)
Notation: n elements, m events, V locations, E roads, W truck capacity. The directed step u → v costs minutes(u, v) + penalty(v).

| Module | Input | Output and objective | Primary | Baseline(s) |
|---|---|---|---|---|
| **A** Relief inventory | n crates (id, weight 1–20, value after the day's multiplier), capacity W | indivisible crates of total weight ≤ W with maximum total value | 0/1 knapsack DP, O(nW) | value/weight greedy (exact fractions), O(n log n) |
| **B** Route planning | V, E, source 0, today's blocked roads | a cheapest route and its cost or "no route"; the reachable set; the fewest-roads route (neighbours in ascending id) | Dijkstra with our binary heap, O((V+E) log V); BFS for reachability and fewest roads | Bellman–Ford with early exit, O(VE); "fewest-roads route used as the route" |
| **C** Rescue scheduling | n windows (start < finish, value); on day d a window is unavailable when (id + d) mod 5 = 0 | pairwise compatible windows (touching allowed): most windows / most value | earliest-finish-first (count), weighted interval DP with binary search (value), O(n log n) | highest-value-first greedy |
| **D** Emergency queue | m alarms (tick, priority 1–10, id) | release order, one per tick, most urgent first (priority desc, tick asc, id asc) | our binary heap, O(m log m) | sorted list with insertion (O(m²) shifts); bucket queue (10 FIFOs) |

All four modules play in the campaign. A and C give the "fast rule + exact method" pair; B is the network module.

## Retained or changed since the proposal (Iteration 1)
All four modules (A, B, C, D) and every primary/baseline algorithm of `proposal.pdf` are **retained**. One addition: the bucket queue, listed in the proposal as a candidate "which we will test", is implemented and measured as a second baseline for D. No problem definition changed. Master dataset version used: `master_release_v1`.

## Code layout
| Path | Contents |
|---|---|
| `src/loader.py` | checksum check, master CSV reader (one pass per table), our sample, pooling, synthetic maps |
| `src/validation.py` | validation layer: `InvalidInput(case_id, rule, detail)` raised before any algorithm runs |
| `src/heap.py`, `src/sorting.py` | our binary heap and merge sort (with operation counters), shared by the modules |
| `src/inventory.py`, `src/routes.py`, `src/scheduling.py`, `src/alarms.py` | modules A, B, C, D |
| `src/campaign.py` | seven-day campaign coordinator |
| `src/experiments.py`, `src/analysis.py` | timing/ops/memory runner → `results/results.csv`; fits and plots |
| `tests/` | unit, reference, invariant, integration and fault-injection tests (verification code is kept here, apart from `src/`) |
| `results/` | `results.csv`, `fits.csv`, `plots/`, `campaign_*.txt`, `campaign_summary.csv`, `fault_injection.txt`, `environment.txt` |
| `prediction_log.md` | predictions committed before each experiment round, and what we got wrong |
| `generator/`, `validator/`, `cases.xlsx`, `config.py`, `validation_report.txt`, `approach_note.pdf`, `proposal.pdf` | Iteration 1 |

## Library use (rulebook G-08)
The evaluated algorithms use only plain Python lists, dicts, `collections.deque` as a FIFO, `fractions.Fraction` (exact value/weight keys) and our own `src/heap.py` and `src/sorting.py`. They do **not** use `heapq`, `bisect`, `sorted`/`list.sort` or any library routine that performs the algorithm. Other libraries and where they are used: `csv`, `hashlib` (loading and checksums), `random` (synthetic maps, test data; seeded), `time`, `statistics`, `tracemalloc`, `multiprocessing` (measurement and the 5-minute timeout), `numpy` (least-squares fits in `analysis.py` only), `matplotlib` (plots), `pytest` (tests; tests may use `sorted`, `min` etc. as independent references).

## Seeds
- Our master sample: s = 69 → in each tier the cases at positions 6, 13, 20, … in master file order (S 204, M 208, L 62, X 41 cases).
- Synthetic maps (experiment B1): `random.Random("69-synth-<V>")`.
- Random test instances: `random.Random(69)`.
- Pooled instances are deterministic (consecutive sample cases in order, ids renumbered from 1; windows shifted by 1440·i; alarm ticks shifted past the previous case).

## Operation counts (what `ops` means in results.csv)
Each algorithm increments named counters; the `ops` column is the sum of the non-preprocessing counters, and the `note` column lists every counter. Preprocessing (sorting adjacency lists in `build_adj`, the sort inside `weighted_dp`) is counted separately with the prefix `pre_`.
| Family | Counters |
|---|---|
| Ordering (merge sort, used by A's greedy and C) | `cmp` key comparisons; `move` elements written into the merge buffer |
| Queues (D; Dijkstra's heap) | `cmp` key comparisons; `move` element writes during sift-up/sift-down (the heap uses the "hole" technique, so one write per level, not 2 per swap); `pq` push/pop operations; `shift` list elements moved by `list.insert` (sorted list); `probe` binary-search probes; `bucket` bucket appends, pops and inspections |
| Routes (B) | `nodes` visited/settled; `edges` examined; `relax` relaxations attempted (= edges examined); `rounds` Bellman–Ford rounds |
| Tabulation (A's DP, C's DP) | `items` items examined; `cells` DP table cells computed (A: Σ(W − wᵢ + 1); C: n); `probe` binary-search probes |

## Experiments: method
Hardware and software: AMD Ryzen 7 7445HS, 15.2 GB RAM, Windows 11, Python 3.11.6 (`results/environment.txt`). Each measured point runs in a fresh child process: one counted run that is discarded as the warm-up, then 5 timed runs (`time.perf_counter`, single thread, data loading and instance building excluded); we report the median and the interquartile range. Memory: a separate child runs the algorithm once under `tracemalloc` (started after the instance exists), so `mem_bytes` is the peak beyond the input. A run that exceeds 300 s is recorded as `DNF`, larger sizes of that algorithm are skipped, and the missing point is predicted from the fit. Growth: least squares on log–log axes, slope with 95% confidence interval, R², and the relative error of predicting the largest size from the others (`results/fits.csv`).

| Exp | Data | Sizes |
|---|---|---|
| A1 | pooled crates (M+L sample), W = ⌊0.4 · total weight⌋ | n = 100 … 6,400 |
| A2 | 4,000 pooled crates (total weight 39,649) | W = 1,000 … 32,000 |
| B1 | synthetic connected maps, E = ⌊2.5 V⌋ | V = 500 … 32,000 |
| B2 | 12 real L-sample maps spread over V | V as given |
| C1 | pooled windows | n = 250 … 32,000 |
| D1 | pooled alarms | m = 500 … 64,000 |

## Campaign rules as implemented
Days, events, destinations and closures follow rulebook 6.4. "Wave i" is the i-th wave of the case in increasing `wave_no` order, (i mod number of waves) — 1,862 master cases number their waves from 1, not 0. Clash Q-1: Day 2 road minutes are **rounded up**, ⌈1.5·m⌉, while crate values use floor(base · multiplier) (the multipliers 2 and 3 are integers, so values are exact). Added alarms (Day 2 priority 9, Day 5 priority 10) arrive at tick 0 with id = max id + 1. A destination that is unreachable skips the trip (no route, no loading) — never an error; windows and alarms are processed every day. Every day prints the constraints checked (route uses open roads and re-sums; load ≤ capacity; windows compatible and available; Bellman–Ford = Dijkstra; the three queues give the same order; alarm order valid).

## Tests
`python -m pytest tests -q` — 53 tests: unit and boundary tests per module, brute force on random small inputs, the 204 tier-S claims of our sample (cargo, window count, window value), Dijkstra = Bellman–Ford = Floyd–Warshall on random maps, trap 47 (greedy ≤ 60% of DP) and trap 48 (fewest-roads ≥ 1.5 × cheapest) on our X sample, invariants, the campaign end to end, fault injection, and benchmark exit status.
**Fault injection** (`results/fault_injection.txt`): four deliberate bugs are injected from `tests/faults.py` (production code untouched) and the suite must fail on each — touching windows treated as incompatible, the alarm key ignoring the tick, `build_adj` ignoring blocked roads, and a knapsack that reuses items. All four are caught. Lesson: the tick tie-rule fault was **not** caught by the original alarm tests, because their alarm ids always increased with tick; a test with ids out of tick order was added.

## Recommendation (Problem N)
*For the lead designer of the relief command.* Evidence: experiment round 1 (`results/results.csv`, `results/fits.csv`, `results/plots/`), solution quality (`results/quality_check.txt`) and the campaign (`results/campaign_summary.csv`). Hardware as above.

**A — Relief inventory: ship the 0/1 knapsack DP.**
- *Evidence:* A1 — exact on all 204 tier-S claims; 18.35 s and 166.7 MB at n = 6,400 crates (W = 25,465); time slope 2.08 (95% CI 1.94–2.21) as predicted for W ∝ n. The ratio greedy is 100× faster (0.178 s) and within 0.04% of the optimum on pooled random crates, but on the trap case 4-47 it loaded only 113 of 198 value units (57%) on five of six loading days.
- *Assumption:* n·W stays moderate (weights are small integers, W ≤ 14n).
- *Wrong when:* the truck capacity or the crate count grows so that the n·(W+1)-byte keep table no longer fits in memory or the run exceeds the planning window. *Measure:* n·(W+1) bytes against free memory, and the DP's wall time per day (A2 shows time growing faster than linearly in W, slope 1.15, because of memory effects). Past that point, switch to the greedy and accept the risk on adversarial loads.

**B — Route planning: ship Dijkstra with a binary heap** (BFS for reachability).
- *Evidence:* B1 — 0.343 s at V = 32,000 (slope 1.20); B2 — on real maps Bellman–Ford ranged from 0.3× to **80.8×** Dijkstra's time (map 13-43, 525 rounds) while Dijkstra's cost does not depend on how locations are numbered. On the trap case 2-48 the fewest-roads route cost 64 against Dijkstra's 12 (5.3×), and 368 against 216 on Day 2 of 1-26.
- *Assumption:* every step cost is non-negative (minutes ≥ 1, penalties ≥ 0).
- *Wrong when:* negative costs appear (e.g. a "bonus" for passing a depot), where Dijkstra is incorrect; or when the same map is queried many times with ids that follow the routes, where Bellman–Ford can be faster (B1: 0.81×). *Measure:* the minimum step cost at load time (the validation layer), and Bellman–Ford's round count on the map.

**C — Rescue scheduling: ship earliest-finish-first for the count and the weighted interval DP for the value.**
- *Evidence:* C1 — 0.108 s and 0.163 s at n = 32,000 windows (slopes 1.15 and 1.10); exact on all 204 tier-S claims. The highest-value-first greedy reached only 69.5–70.6% of the optimal value on pooled windows and 20–30% on the dense windows of 4-47 (e.g. 415 vs 2,019 on Day 1).
- *Assumption:* one crew, so chosen windows must not overlap.
- *Wrong when:* several crews work in parallel or windows need travel time between them; the problem becomes machine scheduling. *Measure:* the number of crews available per day, and gaps required between consecutive windows.

**D — Emergency queue: ship the bucket queue (ten FIFO queues).**
- *Evidence:* D1 — fastest at all eight sizes: 0.059 s at m = 64,000 against 0.258 s (sorted list) and 0.472 s (binary heap); all three give identical release orders (checked in every run and every campaign day). Theory said the heap beats the sorted list; measurement says the opposite in this range (heap/list 2.73 → 1.83 from m = 1,000 to 64,000), because the list's shifts are fast C memory moves.
- *Assumption:* priorities are integers from 1 to 10 and arrival ticks are nondecreasing. Within a tick, the bucket queue restores ID order when needed before dispatching alarms.
- *Wrong when:* priorities become fine-grained (e.g. a continuous urgency score), or ID reordering makes preprocessing expensive enough to erase the bucket queue's timing advantage. *Measure:* check the priority range and benchmark representative batches with same-tick ID inversions against the heap.

**Failure modes of the whole engine that worry us most (ranked).**
1. **Destinations cut off by closures.** 12 of 35 campaign trips were skipped because no route existed; the corridor case 2-40 lost 6 of 7 days. No routing algorithm can deliver to a cut-off shelter; the engine reports it, but relief does not arrive. *Watch:* the share of skipped trips per week.
2. **Alarm backlog.** With one release per tick and 1.2–1.8 arrivals per tick, the queue grows without limit: on 2-40, 2-48 and 4-47 the mean wait was 371–379 ticks and the longest wait about 2,000–3,000 ticks, although priority ≥ 9 alarms waited at most 3 ticks. A faster queue does not help; only more response capacity does. *Watch:* the peak queue length (735–758 on those cases).
3. **Exact methods that do not scale.** The knapsack DP needs n·(W+1) bytes and grew to 18 s at 6,400 crates with large run-to-run spread (IQR/median 0.57); Bellman–Ford, if ever used, can be 80× slower on badly numbered maps. *Watch:* DP memory and time per day against the planning window.

## Known limitations
- The knapsack DP stores one keep-row per item: n · (W + 1) bytes (166.7 MB measured at n = 6,400, W = 25,465).
- Experiment B1 used synthetic maps whose node ids increase along the spanning tree (`loader.synthetic_network`), which favours Bellman–Ford's ascending-id scan; B1 therefore flatters Bellman–Ford. B2 on real maps does not have this bias. A shuffled-id B1 is the first follow-up (see `prediction_log.md`).
- Timing is pure Python: constant factors (C-level list shifts vs Python-level heap sifts) decide D1 and B1 within the tested range; asymptotic winners can differ at sizes we did not test.
- A1 at n = 1,600 and 6,400 has a large timing spread (IQR/median 0.43 and 0.57), most likely memory allocation; medians are reported.
- The campaign processes the full alarm stream every day with one release per tick, as the rulebook states; the waits above follow from that rule.
- 1,862 master cases number waves from 1; the engine interprets "wave i" as the i-th wave in `wave_no` order (tested on case 3-00). If the course staff meant the literal `wave_no`, Days 2–5 change for those cases.
