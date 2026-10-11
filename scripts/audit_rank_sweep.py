"""
Phase 3.2 SVD Rank & Regularization Mathematical Audit
"""
import sys
import json
from pathlib import Path
import numpy as np
import scipy.linalg as la

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.dmdc_model import DMDcModel

def main():
    data = np.load("data/final/wrfchem_trajectories/wrfchem_dmdc_matrices.npz", allow_pickle=True)
    prep = DMDcPreprocessor.load("models/artifacts/dmdc/scaler.json")

    X_tr = prep.transform_state(data["X_train"])
    U_tr = prep.transform_control(data["U_train"])
    X_p_tr = prep.transform_state(data["X_prime_train"])

    X_v = prep.transform_state(data["X_val"])
    U_v = prep.transform_control(data["U_val"])
    X_p_v = prep.transform_state(data["X_prime_val"])

    X_te = prep.transform_state(data["X_test"])
    U_te = prep.transform_control(data["U_test"])
    X_p_te = prep.transform_state(data["X_prime_test"])

    Omega = np.vstack([X_tr.T, U_tr.T])  # (23, 176400)
    U_omega, s, Vt_omega = la.svd(Omega, full_matrices=False)

    print("=== SINGULAR VALUES OF OMEGA (23) ===")
    for i, val in enumerate(s):
        print(f"sigma_{i+1:02d}: {val:.10e}")

    eps = np.finfo(float).eps
    tol_numpy = s[0] * max(Omega.shape) * eps
    print(f"\nNumPy default tolerance (sigma_1 * max(M,N) * eps): {tol_numpy:.10e}")
    num_rank_numpy = int(np.sum(s > tol_numpy))
    print(f"Numerical rank (NumPy tol): {num_rank_numpy}")

    tol_1e12 = 1e-12
    num_rank_1e12 = int(np.sum(s > tol_1e12))
    print(f"Numerical rank (1e-12 tol): {num_rank_1e12}")

    # Energy calculations
    total_energy = np.sum(s**2)
    print(f"Total energy: {total_energy:.10e}")

    # Run rank sweep from 1 to 23 for lambda=0.0 and others
    ranks = list(range(1, 24))
    lambdas = [0.0, 1e-6, 1e-4, 1e-2, 0.1, 1.0]

    sweep_records = []
    
    for r in ranks:
        for lmb in lambdas:
            m = DMDcModel()
            m.fit(X_tr, X_p_tr, U_tr, rank=r, reg_lambda=lmb)
            
            # Val prediction
            X_p_v_pred = m.predict_step(X_v, U_v)
            v_rmse = float(np.sqrt(np.mean((X_p_v - X_p_v_pred)**2)))
            v_mae = float(np.mean(np.abs(X_p_v - X_p_v_pred)))
            
            # Test prediction
            X_p_te_pred = m.predict_step(X_te, U_te)
            te_rmse = float(np.sqrt(np.mean((X_p_te - X_p_te_pred)**2)))
            te_mae = float(np.mean(np.abs(X_p_te - X_p_te_pred)))

            eigvals = la.eigvals(m.A)
            spec_rad = float(np.max(np.abs(eigvals)))
            energy = float(np.sum(s[:r]**2) / total_energy)

            # Check if finite
            is_finite = bool(np.isfinite(m.A).all() and np.isfinite(m.B).all())

            # Retained condition number
            cond_num = float(s[0] / s[r-1]) if s[r-1] > 0 else float("inf")

            sweep_records.append({
                "rank": r,
                "lambda": lmb,
                "val_rmse": v_rmse,
                "val_mae": v_mae,
                "test_rmse": te_rmse,
                "test_mae": te_mae,
                "spectral_radius": spec_rad,
                "energy": energy,
                "is_finite": is_finite,
                "condition_number": cond_num,
                "s_min": float(s[r-1])
            })

    print("\n=== RANK SWEEP (lambda=0.0) ===")
    print(f"{'Rank':>4} | {'Val RMSE':>10} | {'Test RMSE':>10} | {'Energy %':>12} | {'rho(A)':>8} | {'Cond Num':>12} | {'s_min':>12} | {'Finite'}")
    print("-" * 85)
    for rec in sweep_records:
        if rec["lambda"] == 0.0:
            print(f"{rec['rank']:4d} | {rec['val_rmse']:10.6f} | {rec['test_rmse']:10.6f} | {rec['energy']*100:11.6f}% | {rec['spectral_radius']:8.4f} | {rec['condition_number']:12.2e} | {rec['s_min']:12.2e} | {rec['is_finite']}")

    # Save to json
    out_dir = Path("reports/dmdc/audit")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "rank_sweep.json", "w", encoding="utf-8") as f:
        json.dump({
            "singular_values": [float(v) for v in s],
            "numpy_tolerance": tol_numpy,
            "numerical_rank_numpy": num_rank_numpy,
            "numerical_rank_1e12": num_rank_1e12,
            "sweep_results": sweep_records
        }, f, indent=2)

    print("\nSaved rank_sweep.json")

if __name__ == "__main__":
    main()
