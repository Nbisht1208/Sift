import pytest
import polars as pl
from sift.chaos_monkey.polluter import ChaosMonkey
from sift.core.profiler import Profiler
from sift.core.inference import InferenceEngine

@pytest.fixture
def clean_data():
    return pl.DataFrame({
        "age": [25, 30, 35, 40, 45] * 100,
        "city": ["New York", "London", "Paris", "Tokyo", "Berlin"] * 100,
        "salary": [50000.0, 60000.0, 70000.0, 80000.0, 90000.0] * 100
    })

def test_profiler_detects_nulls(clean_data):
    monkey = ChaosMonkey(seed=123)
    df_dirty = monkey.inject_nulls(clean_data, ["age"], fraction=0.2)
    
    profiler = Profiler(df_dirty)
    report = profiler.run()
    
    age_profile = report.columns["age"]
    assert age_profile.missing_count == 100
    assert age_profile.missing_ratio == 0.2

def test_inference_detects_outliers(clean_data):
    monkey = ChaosMonkey(seed=42)
    df_dirty = monkey.inject_outliers(clean_data, ["salary"], scale=100.0)
    
    engine = InferenceEngine(df_dirty)
    outliers = engine.detect_outliers("salary")
    
    assert len(outliers) > 0

    bad_values = df_dirty[outliers, "salary"]
    assert bad_values.min() > 1000000 # type: ignore # Should be huge

def test_inference_detects_string_clusters():
    df = pl.DataFrame({
        "city": ["NY", "New York", "new york", "SF", "San Fran"] * 50
    })
    
    engine = InferenceEngine(df)
    clusters = engine.detect_string_clusters("city")
    
    assert len(clusters) > 0
    
    ny_cluster = next(c for c in clusters if "New York" in c["values"])
    assert "new york" in ny_cluster["values"]