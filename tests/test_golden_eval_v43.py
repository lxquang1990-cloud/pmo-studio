from pmo_studio.model.golden_eval import run_golden_eval

def test_golden_eval_passes():
    results=run_golden_eval()
    assert len(results)>=3
    assert all(r.passed for r in results), results
