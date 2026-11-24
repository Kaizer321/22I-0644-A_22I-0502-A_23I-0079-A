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
Run: 2026-11-24, after commit 2b43a69 (this log). 113 points, all `OK` (no DNF, no FAIL). Numbers from `results/results.csv` and `results/fits.csv`; solution-quality ratios from `results/quality_check.txt`. ✔ = within the stated tolerance, ✘ = outside.

| Exp | Prediction | Measured | |
|---|---|---|---|
| A1 | DP time slope 2.0 ± 0.15 | 2.075 (95% CI 1.94–2.21), R² 0.997 | ✔ |
| A1 | DP at n = 6,400: 23 s ± 30% | 18.35 s (IQR 10.53 s) | ✔ |
| A1 | DP memory at n = 6,400: 170 MB ± 20% | 166.7 MB | ✔ |
| A1 | greedy slope 1.15 ± 0.15; 0.15 s ± 50% at n = 6,400 | 1.14; 0.178 s | ✔ |
| A1 | greedy ≥ 97% of DP value | 99.96–100% | ✔ (very conservative) |
| A2 | time slope vs W 1.0 ± 0.1 | 1.146 (CI 0.97–1.32); ops slope 1.002 | ✘ point estimate |
| A2 | 13 s ± 35% at W = 32,000 | 19.65 s | ✘ |
| A2 | memory 128 MB ± 15% | 132.4 MB | ✔ |
| B1 | Dijkstra slope 1.1 ± 0.1; 0.55 s ± 40% at V = 32,000 | 1.20; 0.343 s | ✔ (both at the edge) |
| B1 | Bellman–Ford rounds 10 ± 2 at V = 32,000; slope 1.15 ± 0.15 | 11; 1.18 | ✔ |
| B1 | **Bellman–Ford / Dijkstra time ratio 2.5 (1.2–5)** | **0.81 — Bellman–Ford was faster** | ✘ |
| B2 | corridor (study 5) maps ratio ≥ 20; generic maps < 6 | study-5 map 17-40: 0.3 (2 rounds); generic maps up to 80.8 (13-43, 525 rounds), 15.4, 8.8 | ✘ |
| C1 | EFF / DP time slopes 1.1 ± 0.1 | 1.146 / 1.104 | ✔ |
| C1 | value-greedy shift slope 1.8 ± 0.3, time slope 1.2 ± 0.15 | 1.685 / 1.197 | ✔ |
| C1 | value greedy 75% ± 10% of DP value | 69.5–70.6% | ✔ |
| D1 | heap slope 1.1 ± 0.1, buckets 1.0 ± 0.1 | 1.178, 1.04 (R² 0.979) | ✔ |
| D1 | sorted-list shift slope 1.9 ± 0.2, time slope 1.3 ± 0.2 | ops 1.918, time 1.249 | ✔ |
| D1 | sorted list faster than heap at every size; heap/list 2.5 ± 1.0 at m = 16,000 | yes at all 8 sizes; 2.32 | ✔ |
| D1 | buckets fastest at every size | yes at all 8 sizes | ✔ |
| D1 | crossover heap < list near m ≈ 400,000 | not testable in range; the ratio fell from 2.73 (m = 1,000) to 1.83 (m = 64,000) | — |
| Campaign (not pre-registered) | 0 failed checks; ≥ 1 skipped trip; 2-48 fewest-roads ≥ 1.5× on some day | 0; 12 skipped trips; 5.33× on Days 1 and 7 | (✔) |
| Campaign (not pre-registered) | 4-47 greedy ≤ 60% of DP on every loading day | 0.571–0.576 on Days 1–4 and 6, **0.702 on Day 5** | (✘) |

**What we got wrong and why.**
1. **Bellman–Ford beat Dijkstra on the synthetic maps (B1).** We counted operations correctly (11 rounds, as predicted) but misjudged their price: Bellman–Ford's 3.5 M edge relaxations are plain loop steps, while Dijkstra's 2.3 M counted operations include Python-level heap sifts with tuple keys. More importantly, our own generator `synthetic_network` attaches node i to a parent with a smaller id, and Bellman–Ford scans nodes in ascending id order, so most tree distances settle in the first pass. B1 therefore measures a map family that is unusually kind to Bellman–Ford — a bias in our instance generator that we did not see before the run.
2. **B2 depends on label order, not on the case study.** We expected study-5 corridors to be the hard maps. Map 17-40 (a corridor whose ids follow the path) converged in 2 rounds; map 13-43, whose ids are unrelated to depth, needed 525 rounds and was 80.8 times slower than Dijkstra. The real driver is how many rounds it takes for distances to propagate in scan order, which is at most the route depth but can be far less when ids follow the routes. Dijkstra's cost does not depend on labels at all, which is why it is the safe choice.
3. **A2's time grew faster than its operations.** Cells grew exactly linearly in W (ops slope 1.002), but time grew with slope 1.15 and the per-cell cost rose from about 0.08 µs (W = 1,000) to 0.154 µs (W = 32,000). The keep-rows grow to 132 MB, so allocation and cache effects, not the algorithm, made the larger tables slower. The same effect explains the large spread of A1 at n = 1,600 and 6,400 (IQR/median 0.43 and 0.57).
4. **Trap 47 on Day 5.** Tripling medicine values changes which crates look best, so the greedy recovered to 70% of the optimum on that day. The trap is defined on base values; day multipliers can weaken it.
5. **D1 crossover.** We cannot test it in range. A simple extrapolation of the two fits would put the crossover above 10⁸ alarms, but that is unreliable: the sorted list's time slope must rise toward 2 once shifts dominate, so the true crossover is lower than the naive fit suggests. We leave it as an open prediction.

**Next round (if any):** shuffle node ids in `synthetic_network` (or add a shuffled family) and rerun B1, so the Bellman–Ford comparison is not flattered by our generator.
