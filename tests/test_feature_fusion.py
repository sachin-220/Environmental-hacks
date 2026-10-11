"""
Unit tests for end-to-end feature fusion pipeline and canonical schema validation
"""
import pytest
from processing.feature_fusion import FeatureFusionPipeline
from schemas.canonical import CanonicalHourlySchema, CANONICAL_COLUMNS


def test_feature_fusion_pipeline_execution(monkeypatch):
    from config.settings import settings
    monkeypatch.setattr(settings, "SAMEER_MODE", "demo")
    
    pipeline = FeatureFusionPipeline()
    # Run fusion in demo mode
    fused_df = pipeline.run_fusion(save_output=False)
    
    assert not fused_df.empty
    assert len(fused_df) > 0
    
    # Validate against canonical schema
    schema_errors = CanonicalHourlySchema.validate_dataframe(fused_df)
    assert len(schema_errors) == 0, f"Schema validation failed: {schema_errors}"

    # Check key columns
    assert "timestamp" in fused_df.columns
    assert "grid_id" in fused_df.columns
    assert "temperature_2m" in fused_df.columns
    assert "pm25" in fused_df.columns
    assert "inversion_strength" in fused_df.columns
    assert "plume_transport_score" in fused_df.columns
    assert "provenance" in fused_df.columns
    assert "quality_flag" in fused_df.columns
