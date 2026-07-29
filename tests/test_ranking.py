import pytest
from sift.core.synthesizer import IssueSynthesizer

def test_synthesizer_ranks_critical_issues_first():
    synth = IssueSynthesizer()
    
    # 1. Add a Low Severity issue (Missing Data)
    synth.add_null_issue("age", missing_count=10, total_rows=1000) # ~0.1 severity
    
    # 2. Add a High Severity issue (String Clusters)
    synth.add_string_cluster_issue("city", [{"values": ["NY", "ny"], "suggestion": "fix"}]) # 0.85 severity
    
    # 3. Get Ranked List
    ranked = synth.get_ranked_issues()
    
    # 4. Assert Sorting
    assert len(ranked) == 2
    assert ranked[0].type == "String Inconsistency" # Should be first
    assert ranked[1].type == "Missing Values"       # Should be second
    assert ranked[0].severity > ranked[1].severity  # Math check