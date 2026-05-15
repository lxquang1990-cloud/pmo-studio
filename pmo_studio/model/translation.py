from __future__ import annotations
from copy import deepcopy
from pmo_studio.model.schema import BAModel

VI_EN = {
 'Quản lý danh mục tài sản':'Asset master management','Danh sách/tra cứu tài sản':'Asset list and search','Hồ sơ tài sản':'Asset profile','Import/export tài sản':'Asset import/export','Quản lý vòng đời tài sản':'Asset lifecycle management','Cấp phát tài sản':'Asset allocation','Thu hồi/điều chuyển tài sản':'Asset return/transfer','Kiểm kê và bảo trì':'Inventory and maintenance','Kỳ kiểm kê tài sản':'Asset inventory campaign','Phiếu bảo trì/sửa chữa':'Maintenance/repair ticket','Báo cáo và quản trị':'Reporting and governance',
 'Tiếp nhận văn bản đến':'Incoming document intake','Soạn thảo và phát hành văn bản đi':'Outgoing document drafting and release','Phân công và xử lý công việc':'Task assignment and processing','Tra cứu và lưu trữ văn bản':'Document search and archive',
 'Phê duyệt chiết khấu':'Discount approval','Hồ sơ khách hàng':'Customer profile',
}

EXTRA = {
 'Quản lý tài sản':'Asset Manager','Quản lý phòng ban':'Department Manager','Nhân viên sử dụng tài sản':'Asset User','Kế toán tài sản':'Asset Accountant',
 'Tìm kiếm, lọc và xem danh sách tài sản theo mã, serial, nhóm, phòng ban, người sử dụng và trạng thái.':'Search, filter, and view asset lists by asset code, serial, category, department, current holder, and status.',
 'Tạo và cập nhật thông tin chi tiết tài sản gồm mã, serial, nhóm, ngày mua, giá trị, vị trí và người sử dụng.':'Create and update detailed asset records including code, serial, category, purchase date, value, location, and current holder.',
 'Import danh sách tài sản từ Excel, validate từng dòng và export dữ liệu theo quyền.':'Import asset lists from Excel, validate each row, and export data according to permissions.',
 'Lập phiếu cấp phát tài sản khả dụng cho nhân sự hoặc phòng ban.':'Create allocation vouchers for available assets assigned to employees or departments.',
 'Thu hồi tài sản từ người dùng hoặc điều chuyển sang người dùng/phòng ban khác.':'Return assets from users or transfer assets to another user/department.',
 'Tạo kỳ kiểm kê theo phạm vi phòng ban/vị trí và ghi nhận kết quả thực tế.':'Create inventory campaigns by department/location scope and record actual results.',
 'Ghi nhận yêu cầu bảo trì/sửa chữa, theo dõi trạng thái và chi phí liên quan.':'Record maintenance/repair requests and track status and related costs.',
 'thực hiện ':'perform ', 'và':'and', 'kiểm tra quyền':'permission check', 'mã tài sản':'asset code','nhóm tài sản':'asset category','phòng ban':'department','người sử dụng':'current holder','trạng thái':'status','serial':'serial',
 'danh sách tài sản':'asset list','bộ lọc đã áp dụng':'applied filters','file export nếu có':'export file if any','thông tin tài sản':'asset information','chứng từ đính kèm':'attachments','hồ sơ tài sản':'asset profile','lịch sử cập nhật':'update history',
 'mỗi tài sản có một mã duy nhất':'each asset has a unique code','trạng thái tài sản phải phản ánh vòng đời hiện tại':'asset status must reflect the current lifecycle state','điều kiện lọc ngày phải hợp lệ':'date filters must be valid','người dùng chỉ xem dữ liệu theo quyền':'users can only view data within their permissions','Asset Manager xem toàn bộ':'Asset Manager can view all data','Department Manager xem theo phòng ban':'Department Manager can view department-scoped data','Auditor chỉ xem':'Auditor has read-only access','Export dữ liệu chỉ được phép với người dùng có quyền export tương ứng.':'Data export is only allowed for users with the corresponding export permission.','export danh sách tài sản':'export asset list',
 'tài sản đã thanh lý không được chỉnh sửa nghiệp vụ cấp phát':'disposed assets cannot be modified for allocation operations','chỉ Asset Manager hoặc Admin được tạo/sửa hồ sơ':'only Asset Manager or Admin can create/update profiles','tạo tài sản':'create asset','cập nhật tài sản':'update asset','tài sản khả dụng':'available asset','người nhận':'recipient','ngày cấp phát':'allocation date','biên bản':'handover record','phiếu cấp phát':'allocation voucher','trạng thái tài sản đã cấp phát':'allocated asset status','lịch sử nắm giữ':'holder history',
 'Chỉ cho phép chuyển trạng thái theo luồng nghiệp vụ hợp lệ đã cấu hình.':'Status transitions are only allowed according to the configured business workflow.',
 'Vai trò nghiệp vụ trong hệ thống.':'Business role in the system.','Tài liệu mô tả yêu cầu phần mềm được sinh từ Canonical BA Model, áp dụng cho domain':'This Software Requirements Specification is generated from the Canonical BA Model and applies to the domain',
 'Cần workshop xác nhận rule chi tiết trước baseline cuối.':'A workshop is required to confirm detailed rules before final baseline.',
 'Tích hợp nâng cao chưa có API contract':'Advanced integration without confirmed API contract','Mobile native/RFID/AI advanced nếu source chưa xác nhận':'Native mobile/RFID/advanced AI unless confirmed by source',
 'Dữ liệu nhân sự/phòng ban được cung cấp hoặc tích hợp qua API/Excel':'Employee/department data is provided or integrated via API/Excel','Quy trình phê duyệt chi tiết sẽ được xác nhận trong workshop':'Detailed approval workflows will be confirmed during workshop',
 'Mobile native app':'Native mobile app','RFID realtime nếu chưa có thiết bị/API':'Realtime RFID without confirmed devices/API','Tích hợp kế toán realtime nếu chưa có contract':'Realtime accounting integration without contract'
}
VI_EN.update(EXTRA)

PHRASES = {
 'Hệ thống cho phép người dùng có quyền thực hiện':'The system allows authorized users to perform','với kiểm soát dữ liệu, phân quyền, validation và audit log phù hợp.':'with proper data control, permissions, validation, and audit logging.','Người dùng thực hiện':'The user performs','hệ thống kiểm tra điều kiện nghiệp vụ, quyền và trạng thái dữ liệu trước khi ghi nhận kết quả.':'the system checks business conditions, permissions, and data status before saving the result.','Dữ liệu nghiệp vụ phải nhất quán theo trạng thái hiện tại.':'Business data must remain consistent with the current status.','Trường bắt buộc phải được nhập đúng định dạng.':'Required fields must be provided in the correct format.','Chỉ vai trò được phân quyền mới được thực hiện thao tác.':'Only authorized roles can perform the action.','Ghi audit log khi tạo/sửa/phê duyệt/xóa hoặc export dữ liệu.':'Record audit logs for create/update/approve/delete or data export actions.','hệ thống xử lý thành công, cập nhật dữ liệu liên quan và ghi nhận audit log nếu có':'the system processes successfully, updates related data, and records audit logs if applicable','hệ thống chặn thao tác, hiển thị lỗi rõ ràng và không làm sai lệch dữ liệu':'the system blocks the action, shows a clear error, and does not corrupt data','có quyền và dữ liệu hợp lệ':'has permission and valid data','không đủ quyền hoặc dữ liệu không hợp lệ':'has insufficient permission or invalid data'
}

def model_to_language(model:BAModel, lang:str)->BAModel:
    if lang == 'vi': return model
    m=deepcopy(model); m.project.language=lang
    for c in m.capabilities: c.name=_t(c.name); c.description=_t(c.description)
    for f in m.features: f.name=_t(f.name); f.description=_t(f.description)
    for r in m.requirements:
        r.name=_t(r.name); r.description=_t(r.description); r.inputs=[_t(x) for x in r.inputs]; r.process=_t(r.process); r.outputs=[_t(x) for x in r.outputs]; r.business_rules=[_t(x) for x in r.business_rules]; r.validation_rules=[_t(x) for x in r.validation_rules]; r.permission_rules=[_t(x) for x in r.permission_rules]; r.audit_events=[_t(x) for x in r.audit_events]
    for us in m.user_stories: us.want=_t(us.want); us.benefit=_t(us.benefit)
    for ac in m.acceptance_criteria: ac.given=_t(ac.given); ac.when=_t(ac.when); ac.then=_t(ac.then)
    for tc in m.test_cases: tc.precondition=_t(tc.precondition); tc.test_data=_t(tc.test_data); tc.steps=[_t(x) for x in tc.steps]; tc.expected_result=_t(tc.expected_result)
    m.business_rules=[_t(x) for x in m.business_rules]; m.data_entities=[_t(x) for x in m.data_entities]; m.permissions=[_t(x) for x in m.permissions]; m.audit_events=[_t(x) for x in m.audit_events]; m.integrations=[_t(x) for x in m.integrations]; m.assumptions=[_t(x) for x in m.assumptions]; m.out_of_scope=[_t(x) for x in m.out_of_scope]
    return m

def _t(s:str)->str:
    if not s: return s
    out=VI_EN.get(s,s)
    for vi,en in sorted(PHRASES.items(), key=lambda x: -len(x[0])): out=out.replace(vi,en)
    for vi,en in VI_EN.items(): out=out.replace(vi,en)
    return out
