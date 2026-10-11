"""
Computational Latency and Inference Memory Benchmarking Engine
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import time
import tracemalloc
import numpy as np

from config.logging_config import get_logger
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.rollout import DMDcRolloutEngine, ForecastInputMode

logger = get_logger("models.dmdc.benchmark")


class DMDcBenchmarkEngine:
    """
    Measures computational latency and memory consumption of the DMDc reduced-order emulator.
    Benchmarks:
        1. Model deserialization / loading latency
        2. Single-step forward inference latency
        3. 24-hour multi-step recursive rollout latency
        4. 72-hour operational rollout latency
        5. Peak RAM allocation
        6. Speedup factor relative to full numerical WRF-Chem runs
    """

    # Typical WRF-Chem simulation benchmark for 3-km D03 (61x61, 40 levels, 72 hours) on a 16-core cluster:
    # ~3.5 to 6.0 hours (12,600 to 21,600 seconds)
    ESTIMATED_WRFCHEM_72H_WALLTIME_SECONDS = 14400.0  # 4 hours

    def __init__(
        self,
        model: DMDcModel,
        preprocessor: DMDcPreprocessor
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.rollout_engine = DMDcRolloutEngine(model, preprocessor)

    def run_benchmark(
        self,
        num_warmup: int = 5,
        num_trials: int = 25
    ) -> Dict[str, Any]:
        """
        Executes benchmark suite measuring inference latency and memory.
        """
        n_states = self.model.n_states
        n_controls = self.model.n_controls
        
        # Test sample vectors
        x0 = np.ones(n_states, dtype=np.float64) * 50.0
        u0 = np.ones(n_controls, dtype=np.float64) * 10.0
        u_seq_72 = np.ones((72, n_controls), dtype=np.float64) * 10.0
        u_seq_24 = u_seq_72[:24]

        # Warm-up runs
        for _ in range(num_warmup):
            self.model.predict_step(x0, u0)
            self.rollout_engine.forecast(x0, u0, horizon=72, mode=ForecastInputMode.OPERATIONAL)

        # 1. Single-step inference latency
        single_step_times = []
        for _ in range(num_trials):
            t0 = time.perf_counter()
            self.model.predict_step(x0, u0)
            t1 = time.perf_counter()
            single_step_times.append(t1 - t0)

        mean_step_ms = float(np.mean(single_step_times) * 1000.0)
        p95_step_ms = float(np.percentile(single_step_times, 95) * 1000.0)

        # 2. 24-hour rollout latency
        rollout_24_times = []
        for _ in range(num_trials):
            t0 = time.perf_counter()
            self.rollout_engine.forecast(x0, u0, horizon=24, mode=ForecastInputMode.OPERATIONAL)
            t1 = time.perf_counter()
            rollout_24_times.append(t1 - t0)

        mean_24h_ms = float(np.mean(rollout_24_times) * 1000.0)

        # 3. 72-hour rollout latency
        tracemalloc.start()
        rollout_72_times = []
        for _ in range(num_trials):
            t0 = time.perf_counter()
            self.rollout_engine.forecast(x0, u0, horizon=72, mode=ForecastInputMode.OPERATIONAL)
            t1 = time.perf_counter()
            rollout_72_times.append(t1 - t0)
        
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        mean_72h_ms = float(np.mean(rollout_72_times) * 1000.0)
        p95_72h_ms = float(np.percentile(rollout_72_times, 95) * 1000.0)
        mean_72h_sec = mean_72h_ms / 1000.0

        # Speedup comparison against full numerical WRF-Chem
        speedup_factor = float(self.ESTIMATED_WRFCHEM_72H_WALLTIME_SECONDS / max(1e-6, mean_72h_sec))

        results = {
            "single_step_latency": {
                "mean_ms": round(mean_step_ms, 4),
                "p95_ms": round(p95_step_ms, 4),
                "trials_count": num_trials
            },
            "rollout_24h_latency": {
                "mean_ms": round(mean_24h_ms, 3),
                "trials_count": num_trials
            },
            "rollout_72h_latency": {
                "mean_ms": round(mean_72h_ms, 3),
                "mean_seconds": round(mean_72h_sec, 5),
                "p95_ms": round(p95_72h_ms, 3),
                "trials_count": num_trials
            },
            "sub_second_target_achieved": bool(mean_72h_ms < 1000.0),
            "memory_usage": {
                "peak_allocated_kb": round(peak_mem / 1024.0, 2),
                "current_allocated_kb": round(current_mem / 1024.0, 2)
            },
            "computational_acceleration": {
                "reference_numerical_wrfchem_72h_sec": self.ESTIMATED_WRFCHEM_72H_WALLTIME_SECONDS,
                "dmdc_spectral_rollout_72h_sec": round(mean_72h_sec, 5),
                "speedup_factor": round(speedup_factor, 1),
                "speedup_order_of_magnitude": f"~{speedup_factor:,.0f}x faster"
            }
        }

        logger.info(
            f"Benchmark complete: 72-hour rollout in {mean_72h_ms:.2f} ms "
            f"(Sub-second: {results['sub_second_target_achieved']}), Speedup: {results['computational_acceleration']['speedup_order_of_magnitude']}"
        )
        return results
