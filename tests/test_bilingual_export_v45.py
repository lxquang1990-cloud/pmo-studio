from pmo_studio.core.project import Project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.model.builder import write_ba_model
from pmo_studio.model.generators import generate_srs_from_model

def test_english_export_has_english_path_and_translated_terms(tmp_path):
    src=tmp_path/'asset.md'; src.write_text('Quản lý tài sản cấp phát kiểm kê bảo trì thanh lý',encoding='utf-8')
    p=Project.create('asset-en', customer='Demo', root_base=tmp_path)
    generate_stage0(p, brief='asset', products=['Asset'], sources=[src]); write_ba_model(p)
    out=generate_srs_from_model(p, lang='en')
    txt=out.read_text(encoding='utf-8')
    assert out.name.endswith('.en.md')
    assert 'Asset allocation' in txt
    assert (p.root/'exports/customer/en/srs-customer-ready.docx').exists()
