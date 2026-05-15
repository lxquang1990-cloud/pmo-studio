from pathlib import Path
from pmo_studio.model.quality import run_quality_v3

def test_quality_v3_catches_placeholder(tmp_path):
    root=tmp_path/'p'; (root/'artifacts/ba').mkdir(parents=True); (root/'artifacts/ba/x.md').write_text('${overview}\nValidate scenario 1',encoding='utf-8')
    r=run_quality_v3(root)
    assert r.readiness=='NOT_READY'
    assert any(f.id=='Q3-PLACEHOLDER' for f in r.findings)
