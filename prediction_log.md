# Prediction log

Rules (rulebook 6.3, R-05): each entry is written and **committed before** its experiment round runs; after the run we record what we got wrong and why. Hardware for every round: AMD Ryzen 7 7445HS, 15.2 GB RAM, Windows 11, Python 3.11.6, single process, single thread. Data: master_release_v1 (sample s = 69) and pooled/synthetic instances as defined in the README.

**Disclosure.** Before this log was written, the module acceptance checks printed one smoke timing each (single run, no warm-up): knapsack DP 3,000 items × capacity 19,568 → 7.81 s and 58,675,315 cells; Dijkstra / Bellman–Ford on a 4,000-node synthetic map → 0.055 s / 0.083 s (8 rounds); scheduling on 32,000 pooled windows → EFF 0.118 s, DP 0.179 s, value greedy 0.208 s; alarm queues on 64,000 pooled alarms → heap 1.18 s, sorted list 0.59 s (147.7 M shifts), buckets 0.13 s. Predictions below that touch those points are marked *(seen)* and are judged only on the other sizes and on the fitted slopes. A smoke test of the experiment runner (one timed run, the **two smallest sizes** of every experiment, `results/smoke/`) was also seen before this log was finalised, e.g. A2 at W = 1,000 took 0.33 s for 3.96·10⁶ cells (≈ 0.083 µs per cell); those two smallest sizes are not used to judge any prediction.

---

## Round 1 — 2026-11-24, before any experiment run

### A1 — knapsack DP vs ratio greedy, vary n (W = ⌊0.4 · total weight⌋)
- **Expected winner:** greedy is faster at every size; DP is exact.
- **Prediction:** DP cells = Σ(W − wᵢ + 1) exactly (deterministic, tolerance 0). W grows linearly with n, so DP time ∝ n²: log-log slope **2.0 ± 0.15**. Using the smoke rate (7.81 s / 5.87·10⁷ cells ≈ 0.133 µs per cell *(seen)*), the n = 6,400 point (≈ 1.7·10⁸ cells) takes **23 s ± 30%**. Greedy slope **1.15 ± 0.15** (n log n merge sort with Fraction keys), n = 6,400 in **0.15 s ± 50%**. Greedy reaches **≥ 97%** of the DP value on pooled data (random weights leave little slack), except trap-47-like inputs.
- **Memory:** DP keep-rows dominate: n · (W + 1) bytes → at n = 6,400 about **170 MB ± 20%**.
- **Reasoning:** pseudo-polynomial DP with W tied to n; the per-cell cost is three list comprehensions, so it is constant.

### A2 — knapsack DP, vary W at n = 4,000 (total weight 39,649, so every W ≤ 32,000 still binds)
- **Prediction:** time slope vs W **1.0 ± 0.1**; cells ≈ 4,000 · W; time at W = 32,000 (≈ 1.28·10⁸ cells) ≈ **13 s ± 35%** (per-cell cost between the two smoke rates, 0.083–0.133 µs); keep-row memory ≈ 4,000 · 32,001 bytes ≈ **128 MB ± 15%**.
- **Reasoning:** n fixed, cells ∝ W; the per-cell cost should not depend on W.

### B1 — Dijkstra vs Bellman–Ford vs BFS, synthetic maps E = ⌊2.5 V⌋, V = 500 … 32,000
- **Expected winner:** BFS fastest (no costs), then Dijkstra, then Bellman–Ford.
- **Prediction:** Dijkstra slope **1.1 ± 0.1**; V = 32,000 in **0.55 s ± 40%**. Bellman–Ford with early exit needs only about (shortest-path depth + 1) rounds; on random sparse graphs that depth grows like log V, so rounds go from ≈ 8 (V = 4,000 *(seen)*) to **10 ± 2** at V = 32,000 and its slope is **1.15 ± 0.15** — NOT quadratic. **Bellman–Ford / Dijkstra time ratio at V = 32,000: 2.5 (accept 1.2–5).** The proposal's "orders of magnitude" applies to the worst case O(VE), which random maps do not reach.
- **Reasoning:** early exit makes Bellman–Ford O(rounds · E); random graphs have small depth.

### B2 — Dijkstra vs Bellman–Ford on real L/X sample maps
- **Prediction:** on study-5 corridor maps (a path with short chords, depth ≈ V/3) Bellman–Ford needs hundreds of rounds: **ratio ≥ 20** for V ≥ 500; on generic maps the ratio stays **< 6**. This is the data property that should flip B1's conclusion.

### C1 — EFF (count), weighted DP (value), value greedy, pooled windows n = 250 … 32,000
- **Expected winner:** EFF fastest, value greedy slowest (sort + list inserts).
- **Prediction:** EFF and DP time slopes **1.1 ± 0.1** (merge sort dominates; DP adds n binary searches). Value greedy: the kept list spans all pooled days, so its *shift count* grows about quadratically (slope **1.8 ± 0.3**; 1.04 M shifts at 32,000 *(seen)*), but shifts are C `memmove`, so its *time* slope stays **1.2 ± 0.15**. Times at n = 32,000 *(seen)* — judged on the slopes only. **Value greedy reaches 75% ± 10% of the DP value** on pooled data (dense overlaps).

### D1 — heap vs sorted list vs bucket queue, pooled alarms m = 500 … 64,000
- **Expected winner (theory):** heap over sorted list at large m. **Expected winner (measurement):** bucket queue at every size; **sorted list faster than heap at every tested size**, because its O(q) shifts are a C `memmove` while the heap's O(log q) sifts are Python-level.
- **Prediction:** heap time slope **1.1 ± 0.1**; buckets **1.0 ± 0.1**; sorted-list *shift count* slope **≈ 1.9 ± 0.2** (backlog q grows linearly with m when arrivals exceed 1 per tick) while its *time* slope is only **1.3 ± 0.2** up to 64,000. Heap/list time ratio at m = 64,000 *(seen ≈ 2.0)*; at m = 16,000 **2.5 ± 1.0**. Extrapolated crossover (heap faster than list): **m ≈ 400,000 ± factor 2** — outside the tested range, stated as a prediction only.
- **Reasoning:** constant factors of interpreted Python vs C dominate until the quadratic term wins.

### Campaign (5 cases)
- **Status of this entry:** written before we saw any campaign output, but the campaign's development acceptance run produced `results/campaign_*` before this log could be committed, and we have seen that output since. This entry is therefore **not** a pre-registered prediction; it is kept unchanged as written, and its outcome is reported below without credit.
- **Prediction:** 0 failed constraint checks; on `4-47` (trap 47) the greedy load is **≤ 60%** of the DP load on every loading day where the trap crates are reachable; on `2-48` (trap 48) the fewest-roads route costs **≥ 1.5×** Dijkstra's on at least one day; at least one skipped trip on Day 6 or 7 across the five cases.

## After Round 1 — what we got wrong and why
(to be filled after the run, with the numbers from `results/results.csv`)
