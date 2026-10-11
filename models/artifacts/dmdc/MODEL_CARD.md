# Model Card: SAMEER-DMDc Spectral Atmospheric Chemistry Emulator

**Version:** 1.1.0 | **Phase:** Phase 3.2 (Verified Mathematical Emulator)  
**Framework:** Dynamic Mode Decomposition with Control (DMDc) / Koopman Operator Theory

---

## 1. Scientific Overview & Architecture
- **Teacher Model:** WRF-Chem v4.5.1 with Two-Way Aerosol-Radiation Coupling (`aer_ra_feedback=1`)
- **Dynamical Formulation:** $x(t+1) = A x(t) + B u(t)$
- **State Dimension:** $n = 15$ (Coupled atmospheric chemistry & meteorology)
- **Control Dimension:** $m = 8$ (Emissions, fire FRP, solar radiation, precipitation)
- **Augmented Space Dimension:** $n + m = 23$
- **Spectral Radius:** $\rho(A_{\text{raw}}) = 1.1512$, $\rho(A_{\text{stab}}) = 1.0000$

---

## 2. SVD Rank & Numerical Conditioning
- **Numerical Rank of $\Omega$:** **12** (determined using standard tolerance $\tau = \sigma_1 \times \max(M, N) \times \epsilon \approx 4.65 \times 10^{-8}$)
- **Selected Truncation Rank:** **$r = 12$** (selected via validation RMSE minimization; optimal minimum $\text{RMSE} = 0.103237$)
- **Retained SVD Energy:** **$100.000000\%$** ($\sigma_1 \dots \sigma_{12}$ capture all physical dynamical energy)
- **Condition Number:** **$\kappa = 2.84 \times 10^3$** (well-conditioned; smallest inverted singular value $\sigma_{12} = 0.4184$)
- **Resolution of Previous Textual Narrative:** The state vector dimension ($n = 15$) was previously conflated with SVD rank in narrative text. The serialized model artifact on disk is and has always been mathematically fitted at rank 12.

---

## 3. Training Data & Leakage Prevention
- **Training Window:** `2023-11-01T00:00:00Z` to `2023-11-03T01:00:00Z` (50 hours, 176,400 snapshots)
- **Validation Window:** `2023-11-03T02:00:00Z` to `2023-11-03T12:00:00Z` (11 hours, 36,000 snapshots)
- **Test Window:** `2023-11-03T13:00:00Z` to `2023-11-03T23:00:00Z` (11 hours, 36,000 snapshots)
- **Data Leakage Status:** ZERO OVERLAP (Verified via strict chronological ordering and train-only scaling)
- **Target Invariance:** Verified (mutating future ground truth in memory does not affect model predictions)

---

## 4. Evaluation Horizon & Claim Boundaries
- **Held-Out Test Accuracy:**  
  Evaluated over **1–10 hours** ($h \in [1, 2, 4, 6, 8, 10]\text{h}$) strictly per-cell across all 3,600 spatial cells within the 11-hour held-out test partition.
- **72-Hour Forward Simulation:**  
  Forward rollout capability and model-propagated analytical uncertainty simulation ($32.22\text{ ms}$ latency), **NOT an independently validated 72-hour held-out forecast accuracy claim**.
- **No Extrapolation:**  
  Test metrics are not mathematically extrapolated from 10h to 72h.

---

## 5. Computational Latency & Inference Acceleration
- **Single-Step Inference:** **0.0026 ms**
- **24-Hour Regional Rollout:** **1.65 ms**
- **72-Hour Forward Rollout:** **32.22 ms**
- **Inference Acceleration vs. WRF-Chem:** **~447,000x faster** (numerical solver ~14,400s vs. forward DMDc rollout 0.0322s)

---

## 6. Uncertainty Estimation
- **Method:** Analytical Lyapunov recursive error covariance propagation: $\Sigma_k = A \Sigma_{k-1} A^T + \Sigma_w$
- **Uncertainty Expansion:** $47.9\times$ expansion over 72 steps driven by nocturnal inversion mode ($\rho = 1.1512$)
- **Prediction Intervals:** 95% analytical confidence bounds ($z = 1.96$)

---

## 7. Limitations
- **Linear Operator Approximation:** Represents coupled atmospheric chemistry as a reduced-order linear Koopman system.
- **Test Partition Length:** Chronological test split covers 11 hours; long-term multi-day accuracy requires extended continuous simulation trajectories.
- **Future Control Assumption:** Retrospective evaluations utilize replayed simulation forcing; operational deployment requires persistence or weather forecast inputs.
