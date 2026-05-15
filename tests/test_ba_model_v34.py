from pmo_studio.core.project import Project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.model.builder import write_ba_model, load_ba_model


def _make(tmp_path, slug, text):
    src=tmp_path/f'{slug}.md'; src.write_text(text, encoding='utf-8')
    p=Project.create(slug, customer='Demo', root_base=tmp_path)
    generate_stage0(p, brief=text[:80], products=['Demo'], sources=[src])
    return p

def test_build_model_asset_crm_eoffice(tmp_path):
    cases=[('asset','Quản lý tài sản cấp phát kiểm kê bảo trì thanh lý'),('crm','CRM lead customer opportunity sales forecast dashboard'),('eoffice','eOffice văn bản đến luồng ký phê duyệt văn thư lưu trữ')]
    for slug,text in cases:
        p=_make(tmp_path,slug,text)
        out=write_ba_model(p)
        assert out.exists()
        m=load_ba_model(p.root)
        assert m.capabilities and m.features and m.requirements and m.user_stories and m.test_cases
        assert all('Asset Manager' not in r.name for r in m.roles) or m.domain.id=='asset_management'
