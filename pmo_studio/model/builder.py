from __future__ import annotations
import json, re
from pathlib import Path
from pmo_studio.domain.detector import detect_domain
from pmo_studio.domain.pack_loader import load_domain_pack
from pmo_studio.generators.source_ba import read_redacted_sources
from pmo_studio.model.schema import *

DEFAULT_FEATURES = {
 'asset_management': [('CAP-001','Asset Master',['Asset catalog','Asset profile','Asset import/export']),('CAP-002','Asset Lifecycle',['Allocation','Handover','Return/Transfer']),('CAP-003','Inventory & Maintenance',['Inventory campaign','Maintenance ticket','Liquidation request']),('CAP-004','Reporting & Governance',['Dashboard/report','Permission and audit'])],
 'crm': [('CAP-001','Customer Management',['Customer profile','Contact history','Lead capture']),('CAP-002','Sales Pipeline',['Opportunity management','Stage workflow','Forecast']),('CAP-003','Reporting',['Sales dashboard','Export'])],
 'eoffice': [('CAP-001','Document Intake',['Incoming document','Document metadata','Attachment management']),('CAP-002','Routing & Approval',['Assignment workflow','Review/approval','Digital signing']),('CAP-003','Archive & Search',['Archive','Search','Reporting'])],
 'generic': [('CAP-001','Core Operations',['Core workspace','Workflow processing','Search and report']),('CAP-002','Governance',['Permission','Audit','Import/export'])]
}
ROLE_DEFAULTS = {
 'asset_management':['Admin','Asset Manager','Department Manager','Staff','Auditor'],
 'crm':['Sales Admin','Sales Manager','Sales Representative','Customer Support'],
 'eoffice':['Văn thư','Chuyên viên','Lãnh đạo phòng','Lãnh đạo đơn vị','Quản trị hệ thống'],
 'generic':['Admin','Business User','Approver','Viewer']
}

def build_ba_model(project) -> BAModel:
    source = read_redacted_sources(project)
    det = detect_domain(source, project_slug=project.config.project_slug, customer=project.config.customer)
    domain_id = det.selected_domain if det.selected_domain in DEFAULT_FEATURES else 'generic'
    try:
        pack = load_domain_pack(domain_id)
        label = getattr(pack, 'label', domain_id)
    except Exception:
        label = domain_id
    roles = [Role(_id('ROLE', r, i), r) for i, r in enumerate(ROLE_DEFAULTS.get(domain_id, ROLE_DEFAULTS['generic']),1)]
    caps=[]; feats=[]; reqs=[]; stories=[]; acs=[]; tcs=[]; est=[]
    for ci,(cid,cname,fnames) in enumerate(DEFAULT_FEATURES[domain_id],1):
        cap_id=f'CAP-{ci:03d}'; caps.append(Capability(cap_id, _localize(cname, domain_id), f'Năng lực nghiệp vụ: {_localize(cname, domain_id)}', ['SRC-001']))
        for fi,fname in enumerate(fnames,1):
            fid=f'FEAT-{ci:02d}-{fi:03d}'; fl=_localize(fname, domain_id)
            feats.append(Feature(fid, cap_id, fl, f'Thực hiện {fl.lower()} theo phạm vi domain {label}.', 'Must', _complexity(fname), ['SRC-001']))
            rid=f'REQ-{ci:02d}-{fi:03d}'; role_names=[r.name for r in roles[:2]]
            reqs.append(Requirement(rid,fid,fl, _req_desc(fl), role_names, _inputs(fl), f'Người dùng thực hiện {fl.lower()}, hệ thống kiểm tra dữ liệu/quyền và xử lý nghiệp vụ.', ['Kết quả xử lý','Thông báo trạng thái','Nhật ký thao tác'], ['Dữ liệu nghiệp vụ phải nhất quán theo trạng thái hiện tại.'], ['Trường bắt buộc phải được nhập đúng định dạng.'], ['Chỉ vai trò được phân quyền mới được thực hiện thao tác.'], ['Ghi audit log khi tạo/sửa/phê duyệt/xóa hoặc export dữ liệu.'], 'Must', ['SRC-001']))
            usid=f'US-{ci:02d}-{fi:03d}'; stories.append(UserStory(usid,fid,role_names[0],f'thực hiện {fl.lower()}',f'xử lý nghiệp vụ {fl.lower()} nhanh và kiểm soát được', 'Must',[rid]))
            for ai,kind in enumerate(['happy path','negative validation'],1):
                aid=f'AC-{ci:02d}-{fi:03d}-{ai:02d}'
                acs.append(AcceptanceCriteria(aid,usid,rid,f'{role_names[0]} có quyền và dữ liệu {"hợp lệ" if ai==1 else "không hợp lệ"}',f'thực hiện {fl.lower()}', 'hệ thống xử lý thành công và ghi nhận kết quả' if ai==1 else 'hệ thống chặn thao tác, hiển thị lỗi rõ ràng và không làm sai lệch dữ liệu'))
                tcs.append(TestCase(f'TC-{ci:02d}-{fi:03d}-{ai:02d}',rid,usid,aid,role_names[0],'P1','Người dùng đã đăng nhập và có dữ liệu test phù hợp',f'Dữ liệu mẫu cho {fl}',[f'Mở chức năng {fl}', 'Nhập/chọn dữ liệu test', 'Thực hiện thao tác chính', 'Kiểm tra kết quả và audit/log nếu có'], acs[-1].then))
            est.append(EstimateItem(f'EST-{ci:02d}-{fi:03d}',fid,fl,_complexity(fname),_manday(fname),f'Estimate theo độ phức tạp {_complexity(fname)} và phạm vi {fl}.'))
    return BAModel('pmo.ba_model.v1', now_iso(), ProjectInfo(project.config.project_slug, project.config.customer, getattr(project.config,'product',''), 'vi'), DomainInfo(domain_id,label,float(getattr(det,'confidence_score',getattr(det,'score',0)) or 0)), roles,caps,feats,reqs,stories,acs,tcs,est, ['Tuân thủ trạng thái nghiệp vụ và phân quyền theo vai trò.'], ['Core business entity','User/role','Audit log'], ['Role-based permissions'], ['Create/update/approve/export actions'], ['API/import-export nếu có contract'], ['Cần workshop xác nhận rule chi tiết trước baseline cuối.'], ['Tích hợp nâng cao chưa có API contract','Mobile native/RFID/AI advanced nếu source chưa xác nhận'])

def write_ba_model(project) -> Path:
    model=build_ba_model(project); out=project.root/'artifacts/model/ba-model.json'; out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(model.to_dict(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out.parent/'ba-model.md').write_text(render_model_markdown(model),encoding='utf-8')
    return out

def load_ba_model(project_root: Path) -> BAModel:
    data=json.loads((project_root/'artifacts/model/ba-model.json').read_text(encoding='utf-8'))
    return _from_dict(data)

def render_model_markdown(m:BAModel)->str:
    lines=[f'# BA Model: {m.project.slug}','',f'- Domain: {m.domain.id} ({m.domain.label})',f'- Roles: {len(m.roles)}',f'- Capabilities: {len(m.capabilities)}',f'- Features: {len(m.features)}',f'- Requirements: {len(m.requirements)}',f'- User stories: {len(m.user_stories)}',f'- Test cases: {len(m.test_cases)}','']
    for c in m.capabilities:
        lines += [f'## {c.id} — {c.name}','']
        for f in [x for x in m.features if x.capability_id==c.id]: lines.append(f'- {f.id}: {f.name} ({f.priority}, {f.complexity})')
        lines.append('')
    return '\n'.join(lines)

def _from_dict(d):
    return BAModel(d['schema'],d['created_at'],ProjectInfo(**d['project']),DomainInfo(**d['domain']),[Role(**x) for x in d.get('roles',[])],[Capability(**x) for x in d.get('capabilities',[])],[Feature(**x) for x in d.get('features',[])],[Requirement(**x) for x in d.get('requirements',[])],[UserStory(**x) for x in d.get('user_stories',[])],[AcceptanceCriteria(**x) for x in d.get('acceptance_criteria',[])],[TestCase(**x) for x in d.get('test_cases',[])],[EstimateItem(**x) for x in d.get('estimate_items',[])],d.get('business_rules',[]),d.get('data_entities',[]),d.get('permissions',[]),d.get('audit_events',[]),d.get('integrations',[]),d.get('assumptions',[]),d.get('out_of_scope',[]))
def _id(prefix,s,i): return f'{prefix}-{i:03d}'
def _id_slug(s): return re.sub(r'[^A-Z0-9]+','-',s.upper()).strip('-')
def _complexity(n): return 'Complex' if any(k in n.lower() for k in ['workflow','approval','inventory','import','signing']) else 'Medium'
def _manday(n): return 5.0 if _complexity(n)=='Complex' else 3.0
def _req_desc(n): return f'Hệ thống cho phép người dùng có quyền thực hiện {n.lower()} với kiểm soát dữ liệu, phân quyền, validation và audit log phù hợp.'
def _inputs(n): return ['Từ khóa/bộ lọc','Dữ liệu nghiệp vụ','Tệp đính kèm nếu có']
def _localize(n,d):
    vi={'Asset Master':'Quản lý danh mục tài sản','Asset Lifecycle':'Quản lý vòng đời tài sản','Inventory & Maintenance':'Kiểm kê và bảo trì','Reporting & Governance':'Báo cáo và quản trị','Asset catalog':'Danh sách/tra cứu tài sản','Asset profile':'Hồ sơ tài sản','Asset import/export':'Import/export tài sản','Allocation':'Cấp phát tài sản','Handover':'Bàn giao tài sản','Return/Transfer':'Thu hồi/điều chuyển tài sản','Inventory campaign':'Kỳ kiểm kê tài sản','Maintenance ticket':'Phiếu bảo trì/sửa chữa','Liquidation request':'Đề xuất thanh lý','Dashboard/report':'Dashboard/báo cáo','Permission and audit':'Phân quyền và audit log'}
    return vi.get(n,n)
