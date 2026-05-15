from pmo_studio.core.project import Project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.model.builder import write_ba_model, load_ba_model


def _project(tmp_path, slug, text):
    src=tmp_path/f'{slug}.md'; src.write_text(text, encoding='utf-8')
    p=Project.create(slug, customer='Demo', root_base=tmp_path)
    generate_stage0(p, brief=text, products=['Demo'], sources=[src])
    write_ba_model(p)
    return load_ba_model(p.root)

def test_asset_model_uses_pack_v2_content(tmp_path):
    m=_project(tmp_path,'asset-v41','Quản lý tài sản cấp phát kiểm kê bảo trì thanh lý')
    names='\n'.join(f.name for f in m.features)
    assert m.schema=='pmo.ba_model.v2'
    assert 'Cấp phát tài sản' in names
    assert 'Kỳ kiểm kê tài sản' in names
    assert any('Asset' in x for x in m.data_entities)
    assert any('RFID' in x for x in m.out_of_scope)

def test_crm_model_uses_crm_terms_not_asset(tmp_path):
    m=_project(tmp_path,'crm-v41','CRM lead customer opportunity sales forecast discount approval')
    names='\n'.join(f.name for f in m.features)
    assert 'Opportunity pipeline' in names
    assert 'Phê duyệt chiết khấu' in names
    assert 'Cấp phát tài sản' not in names

def test_eoffice_model_uses_document_terms_not_crm(tmp_path):
    m=_project(tmp_path,'eoffice-v41','eOffice văn bản đến trình ký phê duyệt phát hành lưu trữ')
    names='\n'.join(f.name for f in m.features)
    assert 'Tiếp nhận văn bản đến' in names
    assert 'Phân công và xử lý công việc' in names
    assert 'Opportunity' not in names
