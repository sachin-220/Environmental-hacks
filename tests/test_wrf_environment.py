"""
Unit tests for WRF-Chem computational environment detection and prerequisites
"""
import pytest
from models.wrfchem.environment import (
    WRFEnvironmentDetector,
    WRFExecutionStatus,
    get_memory_info
)


def test_memory_info():
    total_gb, avail_gb = get_memory_info()
    assert total_gb > 0.0
    assert avail_gb >= 0.0
    assert total_gb >= avail_gb


def test_environment_inspection():
    report = WRFEnvironmentDetector.inspect_environment()
    assert report.resources.cpu_logical_cores >= 1
    assert report.resources.ram_total_gb > 0.0
    assert report.resources.disk_free_gb >= 0.0
    assert isinstance(report.status, WRFExecutionStatus)
    assert report.status in [
        WRFExecutionStatus.CONFIGURED,
        WRFExecutionStatus.READY,
        WRFExecutionStatus.UNAVAILABLE
    ]
    assert len(report.recommended_execution_backend) > 0
    assert len(report.summary_message) > 0
