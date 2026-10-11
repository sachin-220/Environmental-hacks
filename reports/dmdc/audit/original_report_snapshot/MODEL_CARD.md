# Model Card: SAMEER-DMDc Spectral Atmospheric Chemistry Emulator

**Version:** 1.0.0 | **Phase:** Phase 3 (Physical Reduced-Order Dynamical Emulator)  
**Framework:** Dynamic Mode Decomposition with Control (DMDc) / Koopman Operator Theory

---

## 1. Scientific Overview & Architecture
- **Teacher Model:** WRF-Chem v4.5.1 with Two-Way Aerosol-Radiation Coupling (aer_ra_feedback=1)
- **Dynamical Formulation:** $x(t+1) = A x(t) + B u(t)$
- **State Dimension:** $n = 15$ (Coupled atmospheric chemistry & meteorology)
- **Control Dimension:** $m = 8$ (Emissions, fire FRP, solar radiation)
- **SVD Rank:** $r = 15$
- **Energy Retained:** 100.0%
- **Spectral Radius:** $\rho(A) = 1.1512$

---

## 2. Training Data & Leakage Prevention
- **Training Window:** `2023-11-01T00:00:00Z` to `2023-11-02T10:00:00Z`
- **Validation Window:** `2023-11-02T11:00:00Z` to `2023-11-02T17:00:00Z`
- **Test Window:** `2023-11-02T18:00:00Z` to `2023-11-03T01:00:00Z`
- **Data Leakage Status:** NONE (Verified via strict chronological partitioning)
- **Normalization:** Strictly fit on training data only

---

## 3. Computational Latency & Acceleration
- **72-Hour Rollout Latency:** **32.22 ms**
- **Sub-Second Rollout:** Verified (PASSED)
- **Acceleration vs. WRF-Chem:** **~446,997x faster**

---

## 4. Uncertainty Estimation
- **Method:** Analytical residual covariance error propagation: Sigma_k = A * Sigma_{k-1} * A^T + Sigma_w
- **Confidence Intervals:** 95% confidence bounds (z = 1.96)

---

## 5. Limitations
- Linear Operator Approximation: Assumes atmospheric dynamics can be projected into a finite-dimensional linear Koopman subspace.
- Extrapolation Limits: Extreme unprecedented emission shocks far outside training distribution may exhibit reduced accuracy.
- Nonlinear Regime Shifts: Abrupt deep convective thunderstorms or severe synoptic frontal passages require updated lateral boundary forcing.
