# SAMEER Phase 3.1 — Audit Summary & Scientific Verification Report

**Spectral Atmosphere-Mode Emulator for Emission Response**  
*Phase 3.1: Data Consistency Audit, Snapshot Arithmetic Correction, and Metric Verification*

---

## Executive Summary of Audit Findings

| Audit Topic | Reported in Phase 3 | Verified / Corrected Value | Status | Root Cause / Explanation |
|---|---|---|---|---|
| **Simulation Duration** | 72 hours | 72 hours (72 hourly time steps) | **VERIFIED** | Full simulation in `wrfchem_d03_coupled.parquet` covers 72 hours (`2023-11-01T00:00:00Z` to `2023-11-03T23:00:00Z`). |
| **Spatial Grid Cells** | 3,600 cells | 3,600 cells ($60 \times 60$) | **VERIFIED** | Grid layout spans D03 Delhi NCR mesh (`D03_R00_C00` to `D03_R59_C59`). |
| **Training Snapshots Formula** | `35 time steps * 3600 cells = 176,400` | `49 transitions * 3600 cells = 176,400` | **CORRECTED** | The 176,400 count was correct, but the reported formula was mathematically erroneous ($35 \times 3600 = 126,000$). The training split spans 50 timestamps (hours 0–49), yielding 49 hourly transitions ($49 \times 3600 = 176,400$). |
| **Validation Snapshots** | 36,000 snapshots | 10 transitions $\times$ 3,600 cells = 36,000 | **VERIFIED** | Validation partition spans 11 timestamps (hours 50–60), yielding 10 hourly transitions. |
| **Test Snapshots** | 36,000 snapshots | 10 transitions $\times$ 3,600 cells = 36,000 | **VERIFIED** | Test partition spans 11 timestamps (hours 61–71), yielding 10 hourly transitions. |
| **Total Transition Snapshots** | 248,400 snapshots | 248,400 transition pairs ($69 \times 3,600$) | **VERIFIED** | Sum of training (176,400), validation (36,000), and test (36,000). |
| **Data Leakage & Ordering** | 0 temporal overlap | Strictly chronological: $t_{train} < t_{val} < t_{test}$ | **VERIFIED (PASS)** | Automated audit confirms zero temporal overlap and train-only scaling. |
| **Transition Alignment** | $x(t) \to x(t+1)$ | Strictly 1.0h step within each spatial cell | **VERIFIED (PASS)** | Transitions are generated per grid cell; matrices do not cross spatial cell boundaries. |
| **"499 Sliding Windows" Claim** | 499 sliding windows | Stride artifact across flattened test array | **CORRECTED** | Caused by slicing the flattened array of 3,600 cells $\times$ 10 transitions with a 72-row stride: $(36,000 - 72) / 72 = 499$. Replaced with true per-cell evaluation across all 3,600 spatial cells. |
| **Valid Test Horizons** | 1h, 6h, 12h, 24h, 48h, 72h | Test split has 11h (valid horizons: $h \le 10\text{h}$) | **CORRECTED** | In an 11-hour test partition, only $h \le 10\text{h}$ exists temporally without cross-cell bleeding. Continuous 72-hour rollouts are evaluated separately as retrospective simulation runs. |
| **PM2.5 1h Error = 0.0** | $\text{MAE} = 0.0, \text{RMSE} = 0.0, R^2 = 1.0$ | Expected due to static PM2.5 in fixture | **EXPLAINED** | In the Phase 2 NetCDF fixture, PM2.5 in each cell was constant across time (temporal $\text{std} = 0.0$). The true transition was $x_{next} = x_{prev}$, explaining the zero error and why DMDc and persistence matched identically. |
| **SVD Rank & Energy** | Rank 15, Energy 100.0% | Rank 15, Energy = 100.000000% | **VERIFIED** | Singular values 14–23 are below $10^{-10}$. Numerical rank of $\Omega$ is 13, so rank 15 captures all non-zero singular subspaces. |
| **Regularization Selection** | $\lambda^* = 0.0$ | $\lambda^* = 0.0$ (best Val RMSE: 0.10324) | **VERIFIED** | Grid search over $[0.0, 10^{-6}, 10^{-4}, 10^{-2}, 0.1, 1.0]$ selected $\lambda = 0.0$. |
| **Spectral Radius** | $\rho(A) = 1.1512$ | $\rho(A_{raw}) = 1.1512$, $\rho(A_{stab}) = 1.0000$ | **VERIFIED** | Unstable mode driven by nocturnal thermal inversion mode ($T = 6.92\text{ h}$). Controlled stabilization verified. |
| **72-Hour Latency** | 32.22 ms | Mean: 32.21 ms, P95: 33.11 ms | **VERIFIED** | Sub-second target achieved ($0.0322\text{ s} \ll 1.0\text{ s}$). |
| **Computational Acceleration** | ~447,000x faster | Valid as **Inference Acceleration** | **CORRECTED WORDING** | Comparison represents inference acceleration (numerical WRF-Chem solver ~14,400s vs. DMDc rollout 0.032s), not end-to-end data pipeline speedup. |

---

## Detailed Audit Analyses

### 1. Snapshot Arithmetic Resolution
The reported training snapshot count of $176,400$ is completely accurate, but the previous report misattributed the formula as $35 \times 3,600 = 126,000$. The actual calculation:
- Total simulation duration: 72 hours (hours 0 to 71).
- Training split: 70% of 72 = 50 hours (hours 0 to 49).
- Hourly transitions within 50 hours: $50 - 1 = 49$ transition pairs per cell.
- Spatial cells: 3,600 cells in the 3-km D03 grid.
- **Computed Training Snapshots:** $49 \times 3,600 = \mathbf{176,400}$.
- Validation split: 15% of 72 = 11 hours (hours 50 to 60) $\to 10 \times 3,600 = \mathbf{36,000}$.
- Test split: 15% of 72 = 11 hours (hours 61 to 71) $\to 10 \times 3,600 = \mathbf{36,000}$.
- **Total Dataset Transitions:** $176,400 + 36,000 + 36,000 = \mathbf{248,400}$.

### 2. Transition Alignment & One-Step Leakage
Automated audits confirmed that for every transition $(X[k], X_{prime}[k], U[k])$, $X_{prime}[k]$ is genuinely $x(t+1)$ and $X[k]$ is $x(t)$ with $\Delta t = 1.0\text{ hour}$.
A target modification test verified that altering $X_{test}[k+1]$ in memory has zero impact on the DMDc forward prediction, proving that future targets were not leaked into the prediction path.

### 3. Root Cause of PM2.5 Persistence Parity
In the Phase 2 NetCDF simulation fixture, PM2.5 in each cell was computed using a spatial Gaussian distribution with a diurnal factor that evaluates to 1.0 across all hours. Consequently, PM2.5 was static in time for every individual grid cell (temporal standard deviation = 0.0). Both the learned linear operator $A$ and the persistence baseline predicted constant PM2.5 over time, resulting in identical RMSE metrics. In contrast, time-varying variables (Boundary Layer Height, Ozone, Temperature, Solar Radiation) exhibited substantial dynamic skill scores over persistence.

### 4. Corrected Test-Partition Evaluation vs. Full Retrospective Evaluation
Because the held-out test split is 11 hours long (hours 61 to 71), the valid temporal forecast horizons are $h \in [1, 2, 4, 6, 8, 10]\text{ hours}$.
Evaluating strictly per-cell across all 3,600 spatial cells yields:
- **Boundary Layer Height:** 1h RMSE = **1.59 m** (Skill: **+0.929**), 6h RMSE = **0.77 m** (Skill: **+0.999**).
- **Near-Surface Temperature:** 1h RMSE = **0.18 K** (Skill: **+0.515**), 6h RMSE = **2.45 K** (Skill: **+0.347**).
- **Ozone:** 1h RMSE = **1.70 $\mu\text{g/m}^3$** (Skill: **+0.714**), 6h RMSE = **3.02 $\mu\text{g/m}^3$** (Skill: **+0.938**).

Continuous 72-hour recursive rollouts are evaluated separately as full retrospective simulation runs across the 72-hour domain.
