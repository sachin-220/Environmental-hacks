"""
Unit tests for DMDc Model, SVD Solver, and Linear System Recovery
"""
import pytest
import numpy as np
from pathlib import Path
from models.dmdc.dmdc_model import DMDcModel


def test_dmdc_exact_recovery_synthetic_linear_system():
    """
    Validates mathematical correctness by testing exact recovery of
    known A_true and B_true from clean synthetic simulation snapshots:
        x_{k+1} = A_true * x_k + B_true * u_k
    """
    np.random.seed(101)
    n, m = 3, 2
    N = 100

    # Stable ground truth system
    A_true = np.array([
        [0.85, 0.10, -0.05],
        [0.05, 0.80,  0.10],
        [0.00, 0.05,  0.90]
    ])
    B_true = np.array([
        [0.5, 0.2],
        [0.1, 0.4],
        [0.3, 0.1]
    ])

    # Generate trajectory
    X = np.zeros((N, n))
    X_prime = np.zeros((N, n))
    U = np.random.normal(0, 1, (N, m))

    current_x = np.array([1.0, 0.5, -0.5])
    for k in range(N):
        X[k] = current_x
        u_k = U[k]
        next_x = (A_true @ current_x) + (B_true @ u_k)
        X_prime[k] = next_x
        current_x = next_x

    # Fit DMDc
    state_vars = ["s1", "s2", "s3"]
    control_vars = ["c1", "c2"]
    model = DMDcModel(state_vars=state_vars, control_vars=control_vars)
    model.fit(X, X_prime, U, rank=n+m, reg_lambda=0.0)

    assert model.is_fitted
    assert model.A.shape == (n, n)
    assert model.B.shape == (n, m)

    # Assert exact recovery with high precision
    np.testing.assert_allclose(model.A, A_true, rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(model.B, B_true, rtol=1e-4, atol=1e-4)


def test_dmdc_rank_truncation_and_energy():
    np.random.seed(42)
    n, m = 15, 8
    N = 100

    X = np.random.rand(N, n)
    X_prime = np.random.rand(N, n)
    U = np.random.rand(N, m)

    model = DMDcModel()
    model.fit(X, X_prime, U, rank=10, reg_lambda=1e-4)

    assert model.rank == 10
    assert 0.0 < model.explained_energy <= 1.0
    assert len(model.singular_values) == n + m


def test_dmdc_model_serialization(tmp_path: Path):
    n, m = 15, 8
    N = 50
    X = np.random.rand(N, n)
    X_prime = np.random.rand(N, n)
    U = np.random.rand(N, m)

    model = DMDcModel()
    model.fit(X, X_prime, U, rank=12, reg_lambda=1e-3)

    model.save(tmp_path)
    assert (tmp_path / "dmdc_model.npz").exists()
    assert (tmp_path / "dmdc_model_metadata.json").exists()

    loaded = DMDcModel.load(tmp_path)
    assert loaded.is_fitted
    assert loaded.rank == 12
    np.testing.assert_allclose(loaded.A, model.A)
    np.testing.assert_allclose(loaded.B, model.B)
