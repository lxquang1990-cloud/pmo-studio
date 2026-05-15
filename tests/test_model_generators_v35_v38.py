from pmo_studio.core.project import Project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.model.builder import write_ba_model
from pmo_studio.model.generators import generate_srs_from_model, generate_stories_from_model, generate_uat_from_model, generate_quote_from_model


def test_model_generators_outputs_customer_files(tmp_path):
    src=tmp_path/'asset.md'; src.write_text('Quản lý tài sản cấp phát kiểm kê bảo trì thanh lý',encoding='utf-8')
    p=Project.create('asset-gen', customer='Demo', root_base=tmp_path)
    generate_stage0(p, brief='asset', products=['Asset'], sources=[src])
    write_ba_model(p)
    assert generate_srs_from_model(p).exists()
    assert generate_stories_from_model(p).exists()
    assert generate_uat_from_model(p).exists()
    assert generate_quote_from_model(p).exists()
    assert (p.root/'exports/customer/vi/srs-customer-ready.docx').exists()
