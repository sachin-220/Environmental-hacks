# SAMEER Phase 3.2 — Audit Summary: Mathematical Rank & Forecast Horizon

**Spectral Atmosphere-Mode Emulator for Emission Response**  
*Phase 3.2: Mathematical Rank Verification & Forecast-Horizon Claim Correction*

---

## 1. Resolution of the Mathematical Rank Inconsistency

| Feature | Phase 3 Textual Narrative | Actual Model Artifact on Disk | Mathematical Truth | Verdict |
|---|---|---|---|---|
| **Augmented Matrix $\Omega$** | $\mathbb{R}^{23 \times 176400}$ | $\mathbb{R}^{23 \times 176400}$ | $\mathbb{R}^{23 \times 176400}$ | **VERIFIED** |
| **Numerical Rank** | Reported as 13 | Numerical rank is 12 | 12 (Tolerance $\tau = 4.65 \times 10^{-8}$) | **CORRECTED TO 12** |
| **Selected Truncation Rank** | Stated as 15 | Serialized metadata: **`rank: 12`** | $r^* = 12$ (Minimum Validation RMSE) | **VERIFIED ARTIFACT: 12** |
| **Retained SVD Energy** | 100.0% | 100.000000% | 100.000000% | **VERIFIED** |
| **Condition Number** | Unreported | $\kappa = 2.84 \times 10^3$ | Well-conditioned ($\sigma_{12} = 0.4184$) | **VERIFIED STABLE** |
| **Model Retraining?** | — | — | Loaded model is already Rank 12 | **NOT REQUIRED** |

### Mathematical Findings:
1. **The 12-Order Cliff Drop:** Singular values $\sigma_1 \dots \sigma_{12}$ span from $1186.29$ down to $0.4184$. Then $\sigma_{13} = 2.14 \times 10^{-13}$, dropping by a factor of $1.95 \times 10^{12}$ directly into machine roundoff noise.
2. **Pseudoinverse Safety:** Truncating at $r=12$ ensures that the smallest inverted singular value is $0.4184$ ($1/\sigma_{12} = 2.39$), preventing ill-conditioned noise amplification. Inverting at rank 13 or 15 would invert values below $10^{-12}$, corrupting operator entries by over $10^{12}$.
3. **Artifact Integrity:** The serialized model artifact [`models/artifacts/dmdc/dmdc_model.npz`](file:///d:/SIH%2026/models/artifacts/dmdc/dmdc_model.npz) and [`models/artifacts/dmdc/dmdc_model_metadata.json`](file:///d:/SIH%2026/models/artifacts/dmdc/dmdc_model_metadata.json) were fitted with $r = 12$. The text in the earlier narrative report stated "Rank 15" simply due to an author conflating the physical state dimension ($n = 15$) with the SVD rank ($r = 12$).

---

## 2. Distinction: 72-Hour Rollout Capability vs. Held-Out Forecast Accuracy

| Dimension | 72-Hour Forward Simulation | 1–10 Hour Held-Out Evaluation |
|---|---|---|
| **Nature of Metric** | Computational execution & analytical model propagation | Empirical validation against held-out ground truth |
| **Ground Truth Sourcing** | N/A (Test partition is 11h long) | Held-out test partition (hours 61–71, 3,600 spatial cells) |
| **Horizons Evaluated** | 72 discrete steps (72 hours) | 1h, 2h, 4h, 6h, 8h, 10h |
| **Accuracy Claim** | **NOT CLAIMED** (No 72h continuous test partition) | **VERIFIED** (PBLH 1h RMSE 1.59m, O3 1h RMSE 1.70 $\mu$g/m$^3$) |
| **Computational Latency** | **32.22 ms** (~447,000x inference acceleration) | Evaluated concurrently in batch |
| **Uncertainty Bounds** | Model-propagated Lyapunov expansion ($\Sigma_k = A \Sigma_{k-1} A^T + \Sigma_w$) | Verified against test distribution |
| **Future Control Sourcing** | Replayed / Operational persistence / Scenario multipliers | Replayed held-out forcing |

### Approved Scientific Claim Structure:
- "SAMEER's DMDc emulator supports a 72-step forward rollout and can generate a 72-hour forecast trajectory in 32.2 milliseconds (~447,000x inference acceleration over numerical WRF-Chem integration)."
- "Held-out chronological forecast accuracy evaluation was performed over the 1–10 hour horizons supported by the available held-out test partition."
- "The 72-hour forward simulation demonstrates computational rollout capability, physical bounds compliance, and model-propagated analytical uncertainty, NOT an independently validated 72-hour held-out forecast accuracy claim."
