from pmo_studio.core.project import Project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.model.builder import write_ba_model, load_ba_model

def test_enrichment_adds_state_and_export_rules(tmp_path):
    src=tmp_path/'asset.md'; src.write_text('Quản lý tài sản cấp phát kiểm kê báo cáo export API',encoding='utf-8')
    p=Project.create('asset-enrich', customer='Demo', root_base=tmp_path)
    generate_stage0(p, brief='asset', products=['Asset'], sources=[src])
    write_ba_model(p); m=load_ba_model(p.root)
    rules='\n'.join(m.business_rules)
    perms='\n'.join(m.permissions)
    assert 'trạng thái' in rules
    assert 'Export dữ liệu' in perms
    assert any('API integration' in x for x in m.integrations)
