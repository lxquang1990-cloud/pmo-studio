import json, zipfile
from pmo_studio.core.project import Project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.model.builder import write_ba_model
from pmo_studio.model.delivery_pack import export_delivery_pack


def test_delivery_pack_manifest_and_zip(tmp_path):
    src=tmp_path/'asset.md'; src.write_text('Quản lý tài sản cấp phát kiểm kê bảo trì thanh lý', encoding='utf-8')
    p=Project.create('asset-delivery', customer='Demo', root_base=tmp_path)
    generate_stage0(p, brief='asset', products=['Asset'], sources=[src])
    write_ba_model(p)
    manifest_path=export_delivery_pack(p, 'vi')
    assert manifest_path.exists()
    data=json.loads(manifest_path.read_text(encoding='utf-8'))
    assert data['schema']=='pmo.delivery_manifest.v1'
    assert data['language']=='vi'
    assert data['model_hash'] and len(data['model_hash'])==64
    kinds={a['kind'] for a in data['artifacts']}
    assert {'srs_docx','user_stories_docx','uat_xlsx','quotation_xlsx','quality_json','ba_model_json'} <= kinds
    zip_path=data['zip_path']
    assert zip_path and zipfile.is_zipfile(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        names=set(zf.namelist())
    assert any(n.endswith('DELIVERY_MANIFEST.json') for n in names)
    assert any(n.endswith('01-srs-customer-ready.vi.docx') for n in names)
