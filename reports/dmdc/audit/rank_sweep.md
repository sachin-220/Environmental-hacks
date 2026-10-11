# SAMEER Phase 3.2 — Mathematical Rank Sweep & SVD Conditioning Report

**Spectral Atmosphere-Mode Emulator for Emission Response**  
*Phase 3.2: Mathematical Rank Verification & Forecast-Horizon Claim Correction*

---

## 1. Augmented Matrix Singular Values ($\Omega = [X; U] \in \mathbb{R}^{23 \times 176400}$)

The augmented state-control snapshot matrix $\Omega$ consists of $n = 15$ state variables and $m = 8$ control variables stacked across $N = 176,400$ training transitions.

```text
Dimension: 23 x 176,400
Total Energy: sum(sigma^2) = 2.116800e+06
Machine Precision (eps): 2.220446e-16
NumPy Tolerance: sigma_1 * max(23, 176400) * eps = 4.646532e-08
```

| Index | Singular Value ($\sigma_i$) | Energy Fraction ($\sigma_i^2 / \Sigma$) | Cumulative Energy % | Condition Number ($\sigma_1 / \sigma_i$) | Numerical Validity ($\sigma_i > \tau$) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | $1.186288 \times 10^3$ | $6.648145 \times 10^{-1}$ | 66.4814% | $1.00 \times 10^0$ | **YES (PHYSICAL)** |
| **2** | $7.275326 \times 10^2$ | $2.500490 \times 10^{-1}$ | 91.4863% | $1.63 \times 10^0$ | **YES (PHYSICAL)** |
| **3** | $3.711824 \times 10^2$ | $6.508709 \times 10^{-2}$ | 97.9951% | $3.20 \times 10^0$ | **YES (PHYSICAL)** |
| **4** | $1.696263 \times 10^2$ | $1.359272 \times 10^{-2}$ | 99.3543% | $6.99 \times 10^0$ | **YES (PHYSICAL)** |
| **5** | $9.101210 \times 10^1$ | $3.913078 \times 10^{-3}$ | 99.7456% | $1.30 \times 10^1$ | **YES (PHYSICAL)** |
| **6** | $5.268459 \times 10^1$ | $1.311255 \times 10^{-3}$ | 99.8768% | $2.25 \times 10^1$ | **YES (PHYSICAL)** |
| **7** | $4.186150 \times 10^1$ | $8.287848 \times 10^{-4}$ | 99.9595% | $2.83 \times 10^1$ | **YES (PHYSICAL)** |
| **8** | $2.409146 \times 10^1$ | $2.741872 \times 10^{-4}$ | 99.9870% | $4.92 \times 10^1$ | **YES (PHYSICAL)** |
| **9** | $1.456640 \times 10^1$ | $1.002409 \times 10^{-4}$ | 99.9970% | $8.14 \times 10^1$ | **YES (PHYSICAL)** |
| **10** | $7.938648 \times 10^0$ | $2.977233 \times 10^{-5}$ | 99.9999% | $1.49 \times 10^2$ | **YES (PHYSICAL)** |
| **11** | $7.977375 \times 10^{-1}$ | $3.006450 \times 10^{-7}$ | 100.0000% | $1.49 \times 10^3$ | **YES (PHYSICAL)** |
| **12** | $4.183769 \times 10^{-1}$ | $8.269046 \times 10^{-8}$ | **100.0000%** | **$2.84 \times 10^3$** | **YES (OPTIMAL CUTOFF)** |
| **13** | $2.142751 \times 10^{-13}$ | $2.169018 \times 10^{-32}$ | 100.0000% | $5.54 \times 10^{15}$ | **NO (NUMERICAL NOISE)** |
| **14** | $1.601384 \times 10^{-14}$ | $1.211467 \times 10^{-34}$ | 100.0000% | $7.41 \times 10^{16}$ | **NO (NUMERICAL NOISE)** |
| **15** | $5.166061 \times 10^{-15}$ | $1.260780 \times 10^{-35}$ | 100.0000% | $2.30 \times 10^{17}$ | **NO (NUMERICAL NOISE)** |
| **16** | $8.661594 \times 10^{-16}$ | $3.544181 \times 10^{-37}$ | 100.0000% | $1.37 \times 10^{18}$ | **NO (NUMERICAL NOISE)** |
| **17** | $3.614196 \times 10^{-32}$ | $6.170827 \times 10^{-70}$ | 100.0000% | $3.28 \times 10^{34}$ | **NO (NUMERICAL NOISE)** |
| **18–23** | $0.000000 \times 10^0$ | $0.000000 \times 10^0$ | 100.0000% | $\infty$ | **NO (EXACT ZERO)** |

> [!IMPORTANT]
> **The 12-Order Cliff Drop:**  
> A sharp mathematical cliff drop occurs between $\sigma_{12} = 0.4184$ and $\sigma_{13} = 2.14 \times 10^{-13}$ (a reduction factor exceeding $10^{12}$). The standard numerical rank threshold $\tau = \sigma_1 \times \max(M, N) \times \epsilon \approx 4.65 \times 10^{-8}$ clearly identifies that **the true numerical rank is 12**.

---

## 2. Validation Rank Sweep (Tikhonov $\lambda = 0.0$)

Below are the empirical validation metrics evaluated on the held-out validation partition ($36,000$ snapshots, hours 50–60):

| Rank $r$ | Validation RMSE | Test RMSE | Retained Energy % | Spectral Radius $\rho(A)$ | Retained Condition Number | Status / Validity |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 0.531670 | 0.540813 | 66.4814% | 0.8794 | $1.00 \times 10^0$ | Severely underfit |
| 2 | 0.287511 | 0.304080 | 91.4863% | 1.0000 | $1.63 \times 10^0$ | Underfit |
| 3 | 0.233789 | 0.168044 | 97.9951% | 1.0000 | $3.20 \times 10^0$ | Underfit |
| 4 | 0.233865 | 0.160280 | 99.3543% | 1.0000 | $6.99 \times 10^0$ | Underfit |
| 5 | 0.172073 | 0.156577 | 99.7456% | 1.0000 | $1.30 \times 10^1$ | Underfit |
| 6 | 0.161374 | 0.151021 | 99.8768% | 1.0000 | $2.25 \times 10^1$ | Underfit |
| 7 | 0.159459 | 0.148672 | 99.9595% | 1.0000 | $2.83 \times 10^1$ | Underfit |
| 8 | 0.107929 | 0.084415 | 99.9870% | 1.0996 | $4.92 \times 10^1$ | Transitioning |
| 9 | 0.107017 | 0.084343 | 99.9970% | 1.1293 | $8.14 \times 10^1$ | Near-optimal |
| 10 | 0.103239 | 0.075607 | 99.9999% | 1.1512 | $1.49 \times 10^2$ | Optimal basin |
| 11 | 0.103238 | 0.075606 | 100.0000% | 1.1512 | $1.49 \times 10^3$ | Optimal basin |
| **12** | **0.103237** | **0.075605** | **100.0000%** | **1.1512** | **$2.84 \times 10^3$** | **GLOBAL MINIMUM (OPTIMAL)** |
| 13 | 0.103398 | 0.075523 | 100.0000% | 1.1512 | $5.54 \times 10^{15}$ | Inverts $10^{-13}$ noise |
| 14 | 0.103399 | 0.075523 | 100.0000% | 1.1512 | $7.41 \times 10^{16}$ | Inverts $10^{-14}$ noise |
| 15 | 0.103398 | 0.075523 | 100.0000% | 1.1512 | $2.30 \times 10^{17}$ | Inverts $10^{-15}$ noise |
| 16–23 | 0.103394 | 0.075526 | 100.0000% | 1.1511 | $\ge 1.37 \times 10^{18}$ | Machine noise |

---

## 3. Resolution of the "Rank 15 vs Rank 13" Mystery

1. **Why the report previously stated Rank 15:**
   The coupled physical state vector has dimension **$n = 15$** (`boundary_layer_height`, `temperature_2m`, `u_wind_10m`, `v_wind_10m`, `wind_speed_10m`, `relative_humidity`, `surface_pressure`, `inversion_strength`, `pm25`, `pm10`, `o3`, `no2`, `so2`, `co`, `cams_aerosol`). The narrative report author conflated the physical state dimension ($n = 15$) with the SVD truncation rank ($r = 12$).
2. **What the actual model artifact contains:**
   Inspection of [`models/artifacts/dmdc/dmdc_model_metadata.json`](file:///d:/SIH%2026/models/artifacts/dmdc/dmdc_model_metadata.json) and [`reports/dmdc/training_report.json`](file:///d:/SIH%2026/reports/dmdc/training_report.json) proves that the model fitted on disk has **ALWAYS been Rank 12**:
   ```json
   {
     "rank": 12,
     "reg_lambda": 0.0,
     "explained_energy": 1.0,
     "best_val_rmse": 0.10324
   }
   ```
   Furthermore:
   $$\max |A_{\text{loaded}} - A_{12}| = 0.0, \quad \max |B_{\text{loaded}} - B_{12}| = 0.0$$
   The production model is mathematically and bit-for-bit identical to the rank-12 operator.

3. **Why Rank 12 is mathematically required:**
   - At rank 12, the condition number is $\kappa = 2.84 \times 10^3$, ensuring high numerical precision without inversion of noise.
   - At rank 13 or 15, the minimum singular value is $\le 2.14 \times 10^{-13}$, which would cause unregularized pseudoinverse filters to invert noise at the level of $10^{12}$ to $10^{15}$, corrupting operator entries ($|A_{12} - A_{13}| > 2.3 \times 10^{12}$).
   - The validation error minimum is achieved at **$r = 12$** ($\text{RMSE} = 0.103237$).

**Audit Verdict: RANK 12 IS SCIENTIFICALLY AND MATHEMATICALLY VERIFIED. The actual model in the repository is already Rank 12. Retraining is NOT required.**
