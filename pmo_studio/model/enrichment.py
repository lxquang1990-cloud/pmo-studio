from __future__ import annotations
from pmo_studio.model.schema import BAModel

STATUS_KEYWORDS = ['trạng thái','stage','status','phê duyệt','approval','ký','cấp phát','thu hồi','kiểm kê']
IMPORT_KEYWORDS = ['import','excel','migration','dữ liệu']
EXPORT_KEYWORDS = ['export','báo cáo','dashboard','report']

def enrich_ba_model(model: BAModel, source_text: str = '') -> BAModel:
    """Deterministic enrichment pass: adds source-aware rules and safeguards without LLM."""
    src=(source_text or '').lower()
    for req in model.requirements:
        text=(req.name+' '+req.description).lower()
        if any(k in text for k in STATUS_KEYWORDS) and not _has(req.business_rules,'trạng thái'):
            req.business_rules.append('Chỉ cho phép chuyển trạng thái theo luồng nghiệp vụ hợp lệ đã cấu hình.')
        if any(k in text for k in IMPORT_KEYWORDS) and not _has(req.validation_rules,'template'):
            req.validation_rules.append('File import phải đúng template và hiển thị lỗi theo từng dòng dữ liệu.')
        if (any(k in text for k in EXPORT_KEYWORDS) or 'export' in src) and not _has(req.permission_rules,'export'):
            req.permission_rules.append('Export dữ liệu chỉ được phép với người dùng có quyền export tương ứng.')
        if 'api' in src and not _has(model.integrations,'API'):
            model.integrations.append('API integration theo contract được xác nhận')
    model.business_rules = _unique(model.business_rules + [r for req in model.requirements for r in req.business_rules])
    model.permissions = _unique(model.permissions + [r for req in model.requirements for r in req.permission_rules])
    model.audit_events = _unique(model.audit_events + [r for req in model.requirements for r in req.audit_events])
    return model

def _has(items, term): return any(term.lower() in x.lower() for x in items)
def _unique(items):
    out=[]
    for x in items:
        if x and x not in out: out.append(x)
    return out
