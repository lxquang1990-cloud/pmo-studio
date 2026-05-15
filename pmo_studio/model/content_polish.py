from __future__ import annotations
from pmo_studio.model.schema import BAModel

def polish_model(model:BAModel, lang:str='vi')->BAModel:
    for r in model.requirements:
        if lang=='vi':
            r.description = _vi_req(r.name, r.description)
            r.process = f'Người dùng nhập/chọn dữ liệu cần thiết cho “{r.name}”. Hệ thống kiểm tra quyền, validation và trạng thái nghiệp vụ trước khi lưu kết quả.'
        else:
            r.description = _en_req(r.name, r.description)
            r.process = f'The user provides the required data for “{r.name}”. The system validates permissions, business rules, and data status before saving the result.'
    for us in model.user_stories:
        if lang=='vi':
            us.want = us.want.replace('thực hiện ', '').strip()
            us.benefit = us.benefit.replace('đảm bảo nghiệp vụ', 'giúp nghiệp vụ').strip()
        else:
            us.want = us.want.replace('thực hiện ', '').strip()
    for tc in model.test_cases:
        if lang=='vi':
            tc.precondition = 'Người dùng đã đăng nhập, có quyền phù hợp và dữ liệu test đã được chuẩn bị.'
            tc.steps = [s.replace('Nhập/chọn dữ liệu theo test data','Nhập hoặc chọn dữ liệu theo bộ test data') for s in tc.steps]
        else:
            tc.precondition = 'The user is logged in, has the required permissions, and test data is prepared.'
    return model

def _vi_req(name, desc):
    if desc and len(desc.split()) >= 8 and not desc.startswith('Hệ thống cho phép người dùng có quyền thực hiện'):
        return desc
    return f'Hệ thống cho phép người dùng có thẩm quyền quản lý “{name}” theo đúng quy trình nghiệp vụ, bảo đảm dữ liệu được kiểm tra, lưu vết và phân quyền rõ ràng.'

def _en_req(name, desc):
    if desc and len(desc.split()) >= 8 and not any(v in desc for v in ['Tạo ', 'Quản lý ', 'Người dùng']):
        return desc
    return f'The system allows authorized users to manage “{name}” according to the agreed business workflow, with clear validation, permissions, and auditability.'
