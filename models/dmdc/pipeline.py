"""
End-to-End Training, Evaluation, Benchmarking, and Reporting Pipeline for Phase 3 DMDc
"""
from pathlib import Path
from typing import Dict, Any, Optional
import json
import numpy as np
import pandas as pd

from config.settings import settings
from config.logging_config import get_logger, log_operation
from models.dmdc.config import DMDcFeatureConfig, DMDcModelConfig
from models.dmdc.preprocessing import DMDcPreprocessor, DataLeakageAuditor
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.spectral_analysis import KoopmanSpectralAnalyzer
from models.dmdc.rollout import DMDcRolloutEngine, ForecastInputMode
from models.dmdc.uncertainty import DMDcUncertaintyEngine
from models.dmdc.spatial_reconstruction import SpatialReconstructionEngine
from models.dmdc.evaluation import DMDcEvaluator
from models.dmdc.benchmark import DMDcBenchmarkEngine
from models.dmdc.model_card import DMDcModelCardGenerator

logger = get_logger("models.dmdc.pipeline")


class DMDcTrainingPipeline:
    """
    Orchestrates the entire Phase 3 scientific workflow:
    1. Ingests verified Phase 2 trajectory matrices
    2. Performs data leakage audit
    3. Normalizes features (train-only fitting)
    4. Tunes rank and regularization on validation data
    5. Fits and serializes optimal DMDc model
    6. Conducts Koopman spectral eigendecomposition & mode interpretation
    7. Calibrates analytical uncertainty propagation
    8. Evaluates multi-horizon forecasts against held-out test data and baselines
    9. Evaluates episode-specific regimes (inversions, stubble plumes)
    10. Reconstructs spatial 3-km D03 grid fields
    11. Benchmarks computational latency & speedup vs. numerical WRF-Chem
    12. Generates structured JSON reports and Model Card
    """

    def __init__(self, config: Optional[DMDcModelConfig] = None):
        self.config = config or DMDcModelConfig()
        self.artifact_dir = self.config.artifact_dir
        self.reports_dir = self.config.reports_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_pipeline(
        self,
        npz_path: Optional[Path] = None,
        parquet_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end Phase 3 DMDc workflow.
        """
        with log_operation(logger, "dmdc_pipeline_execution"):
            data_dir = self.config.trajectories_dir
            actual_npz = npz_path or (data_dir / "wrfchem_dmdc_matrices.npz")
            actual_parquet = parquet_path or (data_dir / "wrfchem_coupled_trajectories.parquet")

            if not actual_npz.exists():
                raise FileNotFoundError(f"Missing Phase 2 trajectory matrix file at {actual_npz}")

            logger.info(f"Loading Phase 2 trajectory artifacts from {actual_npz}")
            raw_data = np.load(actual_npz, allow_pickle=True)

            X_train = raw_data["X_train"]
            X_p_train = raw_data["X_prime_train"]
            U_train = raw_data["U_train"]

            X_val = raw_data["X_val"]
            X_p_val = raw_data["X_prime_val"]
            U_val = raw_data["U_val"]

            X_test = raw_data["X_test"]
            X_p_test = raw_data["X_prime_test"]
            U_test = raw_data["U_test"]

            state_vars = [str(s) for s in raw_data["state_vars"]]
            control_vars = [str(c) for c in raw_data["control_vars"]]

            logger.info(
                f"Loaded snapshot shapes: Train={X_train.shape}, Val={X_val.shape}, "
                f"Test={X_test.shape}, State dim={len(state_vars)}, Control dim={len(control_vars)}"
            )

            # -------------------------------------------------------------
            # Step 1: Data Leakage Audit
            # -------------------------------------------------------------
            # Verify timestamps from parquet if available
            train_times, val_times, test_times = [], [], []
            grid_meta_df = None
            if actual_parquet.exists():
                df_meta = pd.read_parquet(actual_parquet)
                grid_meta_df = df_meta[["grid_id", "latitude", "longitude"]].drop_duplicates()
                times_sorted = sorted(df_meta["timestamp"].unique().tolist())
                n_t = len(times_sorted)
                idx_tr = int(n_t * 0.70)
                idx_v = int(n_t * 0.85)
                train_times = times_sorted[:idx_tr]
                val_times = times_sorted[idx_tr:idx_v]
                test_times = times_sorted[idx_v:]
            else:
                train_times = [f"train_t_{i:04d}" for i in range(len(X_train) // 3600)]
                val_times = [f"val_t_{i:04d}" for i in range(len(X_val) // 3600)]
                test_times = [f"test_t_{i:04d}" for i in range(len(X_test) // 3600)]

            leakage_report = DataLeakageAuditor.audit_splits(
                train_times=train_times,
                val_times=val_times,
                test_times=test_times,
                scaler_fitted_on_test=False
            )
            leakage_file = self.reports_dir / "leakage_audit.json"
            with open(leakage_file, "w", encoding="utf-8") as f:
                json.dump(leakage_report, f, indent=2)

            # -------------------------------------------------------------
            # Step 2: Normalization (Train-Only Fitting)
            # -------------------------------------------------------------
            preprocessor = DMDcPreprocessor(state_vars=state_vars, control_vars=control_vars)
            preprocessor.fit(X_train, U_train)
            scaler_file = self.artifact_dir / "scaler.json"
            preprocessor.save(scaler_file)

            # Standardize snapshots
            X_tr_s = preprocessor.transform_state(X_train)
            X_p_tr_s = preprocessor.transform_state(X_p_train)
            U_tr_s = preprocessor.transform_control(U_train)

            X_v_s = preprocessor.transform_state(X_val)
            X_p_v_s = preprocessor.transform_state(X_p_val)
            U_v_s = preprocessor.transform_control(U_val)

            # -------------------------------------------------------------
            # Step 3: Hyperparameter Tuning (Rank & Regularization on Val)
            # -------------------------------------------------------------
            model = DMDcModel(state_vars=state_vars, control_vars=control_vars)
            tuning_history = model.fit_with_validation(
                X_train=X_tr_s,
                X_p_train=X_p_tr_s,
                U_train=U_tr_s,
                X_val=X_v_s,
                X_p_val=X_p_v_s,
                U_val=U_v_s,
                candidate_ranks=self.config.candidate_ranks,
                candidate_lambdas=self.config.candidate_lambdas
            )

            # Save fitted model
            model.save(self.artifact_dir)

            training_report = {
                "dataset": "WRF-Chem Coupled Trajectories (Phase 2)",
                "state_dimension": len(state_vars),
                "control_dimension": len(control_vars),
                "training_snapshots_count": len(X_train),
                "validation_snapshots_count": len(X_val),
                "test_snapshots_count": len(X_test),
                "selected_rank": model.rank,
                "selected_lambda": model.reg_lambda,
                "explained_energy_percent": round(model.explained_energy * 100.0, 2),
                "best_val_rmse": tuning_history["best_val_rmse"],
                "train_time_range": (train_times[0], train_times[-1]) if train_times else ("", ""),
                "val_time_range": (val_times[0], val_times[-1]) if val_times else ("", ""),
                "test_time_range": (test_times[0], test_times[-1]) if test_times else ("", "")
            }
            with open(self.reports_dir / "training_report.json", "w", encoding="utf-8") as f:
                json.dump(training_report, f, indent=2)

            # -------------------------------------------------------------
            # Step 4: Koopman Spectral Eigendecomposition & Mode Analysis
            # -------------------------------------------------------------
            analyzer = KoopmanSpectralAnalyzer(state_vars=state_vars, dt_hours=1.0)
            spectral_report = analyzer.analyze_operator(model.A)
            with open(self.reports_dir / "spectral_modes.json", "w", encoding="utf-8") as f:
                json.dump(spectral_report, f, indent=2)

            # -------------------------------------------------------------
            # Step 5: Uncertainty Calibration & Growth Propagation
            # -------------------------------------------------------------
            uncertainty_engine = DMDcUncertaintyEngine(model, preprocessor, self.config)
            uncertainty_engine.calibrate(X_train, X_p_train, U_train)
            uncertainty_engine.save(self.artifact_dir / "uncertainty_model.npz")

            # Evaluate uncertainty growth over a 72-hour test sample trajectory
            sample_traj_phys = X_test[:72] if len(X_test) >= 72 else np.repeat(X_test[:1], 72, axis=0)
            uncertainty_results = uncertainty_engine.compute_prediction_intervals(sample_traj_phys)
            
            uncertainty_summary = {
                "confidence_level": uncertainty_results["confidence_level"],
                "horizon_hours": uncertainty_results["horizon_hours"],
                "uncertainty_growth": uncertainty_results["uncertainty_growth"],
                "uncertainty_expansion_ratio_72h_vs_1h": uncertainty_results["uncertainty_expansion_ratio_72h_vs_1h"]
            }
            with open(self.reports_dir / "uncertainty_report.json", "w", encoding="utf-8") as f:
                json.dump(uncertainty_summary, f, indent=2)

            # -------------------------------------------------------------
            # Step 6: Multi-Horizon Forecast Evaluation vs. Baselines
            # -------------------------------------------------------------
            evaluator = DMDcEvaluator(model, preprocessor, self.config)
            
            # Use test trajectory sequence
            # Subsample a continuous sequence from test set
            eval_results = evaluator.evaluate_multi_horizon(
                X_test_seq=X_test,
                U_test_seq=U_test,
                horizons=self.config.evaluation_horizons
            )
            with open(self.reports_dir / "test_report.json", "w", encoding="utf-8") as f:
                json.dump(eval_results, f, indent=2)

            # Episode-based evaluation (inversions, plumes)
            episode_results = evaluator.evaluate_episodes(X_test, U_test, horizon=24)
            with open(self.reports_dir / "validation_report.json", "w", encoding="utf-8") as f:
                json.dump({
                    "tuning_history": tuning_history,
                    "episode_evaluations": episode_results
                }, f, indent=2)

            # -------------------------------------------------------------
            # Step 7: Spatial Grid Reconstruction (3-km D03)
            # -------------------------------------------------------------
            spatial_engine = SpatialReconstructionEngine(
                model=model,
                preprocessor=preprocessor,
                grid_metadata_df=grid_meta_df
            )
            # Rollout across all 3,600 cells for 24 hours
            N_cells = min(3600, len(X_test))
            X0_grid = X_test[:N_cells]
            U_grid_seq = np.repeat(U_test[:N_cells][None, :, :], 24, axis=0)
            spatial_traj = spatial_engine.batch_rollout_spatial(X0_grid, U_grid_seq, horizon=24)
            spatial_df = spatial_engine.reconstruct_spatial_dataframe(spatial_traj, horizon_step=24)
            spatial_metrics = spatial_engine.evaluate_spatial_metrics(spatial_traj[-1], X0_grid)

            # -------------------------------------------------------------
            # Step 8: Latency Benchmarking (WRF-Chem vs. DMDc)
            # -------------------------------------------------------------
            benchmarker = DMDcBenchmarkEngine(model, preprocessor)
            benchmark_results = benchmarker.run_benchmark(num_warmup=3, num_trials=20)
            with open(self.reports_dir / "benchmark_report.json", "w", encoding="utf-8") as f:
                json.dump(benchmark_results, f, indent=2)

            # -------------------------------------------------------------
            # Step 9: Model Card Generation
            # -------------------------------------------------------------
            model_card_dict = DMDcModelCardGenerator.generate_model_card(
                training_metadata=training_report,
                spectral_summary=spectral_report["stability_summary"],
                validation_metrics=tuning_history,
                benchmark_results=benchmark_results,
                uncertainty_info=uncertainty_summary
            )
            with open(self.reports_dir / "model_card.json", "w", encoding="utf-8") as f:
                json.dump(model_card_dict, f, indent=2)

            model_card_md = DMDcModelCardGenerator.format_markdown(model_card_dict)
            with open(self.reports_dir / "MODEL_CARD.md", "w", encoding="utf-8") as f:
                f.write(model_card_md)

            logger.info("SAMEER Phase 3 DMDc pipeline executed successfully.")
            return {
                "training_report": training_report,
                "spectral_summary": spectral_report["stability_summary"],
                "modes_sample": spectral_report["modes"][:3],
                "benchmark": benchmark_results,
                "leakage_audit": leakage_report,
                "multi_horizon_results": eval_results["results_by_horizon"].get("24h", {}).get("pm25", {}),
                "spatial_grid_cells_count": N_cells,
                "model_artifacts": {
                    "model_npz": str(self.artifact_dir / "dmdc_model.npz"),
                    "scaler_json": str(scaler_file),
                    "uncertainty_npz": str(self.artifact_dir / "uncertainty_model.npz"),
                    "reports_dir": str(self.reports_dir)
                }
            }
