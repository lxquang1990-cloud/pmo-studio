from __future__ import annotations
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from pmo_studio.model.generators import ensure_model

RATE=3_900_000
RISK_BY_DOMAIN={'legal_ai':1.15,'asset_management':1.15,'crm':1.12,'eoffice':1.15,'generic':1.10}
NON_SCREEN_BY_DOMAIN={
 'legal_ai':[
  ('Workshop nghiệp vụ, SRS baseline và walkthrough',10,'Làm rõ quy trình, ma trận phân quyền, workflow, template và baseline phạm vi.'),
  ('Solution architecture & integration design',8,'Thiết kế kiến trúc, integration flow eOffice/PMS/AD/Azure/SmartCA/AI provider.'),
  ('AI prompt/guardrail/citation design',10,'Thiết kế prompt, guardrail, citation policy, human review và tiêu chí kiểm soát hallucination.'),
  ('Knowledge base ingestion setup & template mapping',8,'Chuẩn hóa nguồn tri thức, metadata, tài liệu pháp lý, FAQ và template mapping ban đầu.'),
  ('DevOps, môi trường staging/production và deployment',8,'Repository, CI/CD cơ bản, môi trường triển khai, cấu hình bảo mật và release package.'),
  ('Security hardening & access control verification',6,'Kiểm tra MFA/RBAC/audit, quyền truy cập dữ liệu restricted và cấu hình SSL.'),
  ('System/UAT support, bug fixing và go-live',12,'Hỗ trợ UAT, xử lý lỗi, chuẩn bị go-live, checklist vận hành.'),
  ('Đào tạo admin và người dùng cuối',6,'Đào tạo quản trị hệ thống và nhóm người dùng nghiệp vụ.'),
  ('Hypercare sau go-live',6,'Hỗ trợ vận hành giai đoạn đầu sau go-live, theo dõi issue và ổn định hệ thống.'),
 ],
 'default':[
  ('Workshop chi tiết & baseline scope',6,'Làm rõ nghiệp vụ, baseline scope và tiêu chí nghiệm thu.'),
  ('Solution architecture & setup',5,'Thiết kế giải pháp, cấu hình môi trường và chuẩn bị triển khai.'),
  ('UAT, tài liệu hóa & go-live',8,'Hỗ trợ UAT, tài liệu bàn giao và go-live.'),
 ]
}
LEGAL_AI_BREAKDOWN={
 'Gửi câu hỏi pháp lý':[
  ('Cổng gửi câu hỏi pháp lý',3,'Form gửi câu hỏi, phân loại chủ đề, mức độ ưu tiên, đính kèm tài liệu và theo dõi trạng thái.'),
  ('Luồng tiếp nhận, phân công và xử lý câu hỏi',4,'Phân công Legal Officer, SLA xử lý, trạng thái ticket, comment nội bộ và lịch sử xử lý.'),
 ],
 'AI trả lời có trích dẫn nguồn':[
  ('AI gợi ý câu trả lời pháp lý dạng draft',8,'Tích hợp AI provider để sinh câu trả lời nháp dựa trên prompt/template và ngữ cảnh câu hỏi.'),
  ('Trích dẫn nguồn/citation và kiểm soát căn cứ pháp lý',6,'Hiển thị nguồn tham chiếu, tài liệu liên quan, mức độ tin cậy và cảnh báo khi thiếu citation.'),
  ('Review/chỉnh sửa/phát hành câu trả lời cuối',5,'Legal Officer review AI draft, chỉnh sửa, phê duyệt nội dung và publish câu trả lời cuối cùng.'),
 ],
 'Kho tri thức FAQ pháp lý':[
  ('Kho FAQ/câu trả lời đã duyệt',4,'Quản lý FAQ pháp lý, version, hiệu lực, tìm kiếm và tái sử dụng câu trả lời đã duyệt.'),
 ],
 'Tạo đề nghị ủy quyền':[
  ('Tạo đề nghị ủy quyền',4,'Thông tin người ủy quyền/người được ủy quyền, phạm vi, thời hạn, tài liệu liên quan.'),
 ],
 'Phê duyệt và ký số ủy quyền':[
  ('Ma trận thẩm quyền và kiểm tra hiệu lực ủy quyền',5,'Kiểm tra phạm vi, thời hạn, trạng thái hiệu lực và authority matrix theo đơn vị/vai trò.'),
  ('Luồng phê duyệt ủy quyền',5,'Trình duyệt nhiều cấp, comment, approve/reject, lịch sử phê duyệt.'),
  ('Ký số/phát hành văn bản ủy quyền',6,'Tích hợp eOffice/SmartCA ở mức API contract, phát hành văn bản đã ký và lưu hồ sơ.'),
  ('Theo dõi hết hạn/thu hồi/điều chỉnh ủy quyền',4,'Cảnh báo hết hạn, thu hồi, điều chỉnh và lưu version/biến động hồ sơ ủy quyền.'),
 ],
 'Soạn thảo hợp đồng theo mẫu':[
  ('Thư viện template hợp đồng và điều khoản chuẩn',5,'Quản lý template, clause library, metadata, phiên bản và trạng thái hiệu lực.'),
  ('Soạn thảo hợp đồng từ mẫu',6,'Tạo draft hợp đồng từ template, bên liên quan, metadata và điều khoản được chọn.'),
 ],
 'Rà soát pháp lý hợp đồng bằng AI':[
  ('AI rà soát điều khoản/rủi ro pháp lý',9,'Phân tích hợp đồng, phát hiện điều khoản thiếu/rủi ro, nghĩa vụ, deadline và điểm cần review.'),
  ('Comment, redline và version hợp đồng',6,'Ghi chú review, version history, so sánh/changelog ở mức nghiệp vụ.'),
 ],
 'Luồng phê duyệt hợp đồng':[
  ('Luồng phê duyệt hợp đồng nhiều cấp',7,'Approval matrix theo loại hợp đồng/giá trị/đơn vị, approve/reject, audit log.'),
  ('Tích hợp eOffice/ký điện tử cho hợp đồng',8,'Kết nối trình ký/phát hành nếu API/SDK eOffice/SmartCA sẵn sàng và được cấp môi trường test.'),
 ],
 'Tạo hồ sơ thẩm định':[
  ('Tạo hồ sơ thẩm định',4,'Tạo case thẩm định, đính kèm tài liệu, deadline, người xử lý và trạng thái.'),
 ],
 'Checklist và kết luận thẩm định':[
  ('Checklist thẩm định theo loại hồ sơ',5,'Checklist động theo loại hồ sơ, rule bắt buộc và hướng dẫn thu thập bằng chứng.'),
  ('Ghi nhận ý kiến, rủi ro và yêu cầu bổ sung',5,'Review note, risk flag, yêu cầu bổ sung hồ sơ và lịch sử trao đổi.'),
  ('Kết luận thẩm định và phát hành báo cáo',5,'Tổng hợp kết luận, phê duyệt, phát hành report và version kết luận.'),
 ],
 'Dashboard và báo cáo pháp lý':[
  ('Dashboard vận hành pháp chế',5,'Số lượng câu hỏi/hợp đồng/ủy quyền/thẩm định, SLA, tồn đọng và trạng thái xử lý.'),
  ('Báo cáo Excel/PDF theo bộ lọc',4,'Báo cáo theo thời gian, đơn vị, loại hồ sơ, trạng thái, người xử lý.'),
 ],
 'Quản trị phân quyền và cấu hình tích hợp':[
  ('Quản trị người dùng, role và phân quyền RBAC',6,'User/role/permission matrix, phân quyền theo đơn vị, module, loại hồ sơ và dữ liệu restricted.'),
  ('Cấu hình tích hợp AD/Azure, PMS, eOffice, SmartCA',9,'Cấu hình kết nối, mapping user/đơn vị, kiểm tra kết nối và quản lý trạng thái tích hợp.'),
  ('Bảo mật MFA/SSL/audit log và cấu hình hệ thống',7,'MFA, SSL readiness, audit log, cấu hình tham số hệ thống và nhật ký thao tác quan trọng.'),
 ],
}

def generate_detailed_quotation(project, lang='vi') -> Path:
    m=ensure_model(project); out=project.root/f'exports/customer/{lang}/quotation-customer-ready-detailed.{lang}.xlsx'; out.parent.mkdir(parents=True,exist_ok=True)
    wb=Workbook(); ws=wb.active; ws.title='Feature List'
    ws.append(['STT','Chức năng / Hạng mục','Đơn giá (VNĐ/MD)','Manday','Thành tiền (VNĐ)','Ghi chú'])
    rows=[]
    ws.append(['I',f'PHẦN MỀM {m.domain.label}',RATE,None,None,''])
    cap_no=0; software=0
    for cap in m.capabilities:
        cap_no+=1; cap_row=ws.max_row+1; ws.append([str(cap_no),cap.name,RATE,None,None,cap.description]); cap_total=0; f_no=0
        for f in [x for x in m.features if x.capability_id==cap.id]:
            f_no+=1; frow=ws.max_row+1; ws.append([f'{cap_no}.{f_no}',f.name,RATE,None,None,f.description]); f_total=0; item_no=0
            for name,md,note in _items_for(m.domain.id, f.name, f.description):
                item_no+=1; r=ws.max_row+1; ws.append([f'{cap_no}.{f_no}.{item_no}',name,RATE,md,f'=C{r}*D{r}',note]); f_total+=md
            ws.cell(frow,4).value=f'=ROUNDUP(SUM(D{frow+1}:D{ws.max_row}),0)'; ws.cell(frow,5).value=f'=C{frow}*D{frow}'
            cap_total+=f_total
        ws.cell(cap_row,4).value=f'=ROUNDUP(SUM(D{cap_row+1}:D{ws.max_row}),0)'; ws.cell(cap_row,5).value=f'=C{cap_row}*D{cap_row}'
        software+=cap_total
    r=ws.max_row+1; ws.append(['∑','TỔNG CỘNG PHẦN MỀM (Chưa bao gồm VAT)',RATE,software,f'=C{r}*D{r}',''])
    _summary(wb,m,software); _assumptions(wb,m); _style(wb); wb.save(out); return out

def _items_for(domain, feature_name, desc):
    if domain=='legal_ai' and feature_name in LEGAL_AI_BREAKDOWN: return LEGAL_AI_BREAKDOWN[feature_name]
    md=6 if any(k in feature_name.lower() for k in ['ai','tích hợp','phê duyệt','workflow','ký']) else 4
    return [(feature_name,md,desc)]

def _summary(wb,m,software):
    ws=wb.create_sheet('Tổng hợp'); ws.append([f'TỔNG HỢP BÁO GIÁ — {m.project.product or m.project.slug}',None,None,None,None]); ws.append([None,'A. MANDAY PHẦN MỀM THEO PHÂN HỆ',None,None,None])
    for cap in m.capabilities:
        md=0
        for f in [x for x in m.features if x.capability_id==cap.id]: md += sum(i[1] for i in _items_for(m.domain.id,f.name,f.description))
        ws.append([None,'  '+cap.name,md,md*RATE,None])
    ws.append([None,'Cộng A — Phần mềm',software,software*RATE,None]); ws.append([None,'B. HẠNG MỤC NGOÀI MÀN HÌNH',None,None,None])
    extra_items=NON_SCREEN_BY_DOMAIN.get(m.domain.id,NON_SCREEN_BY_DOMAIN['default']); extra=sum(x[1] for x in extra_items)
    for i,(name,md,note) in enumerate(extra_items,1): ws.append([i,name,md,md*RATE,note])
    base=software+extra; risk=RISK_BY_DOMAIN.get(m.domain.id,1.10); final=round(base*risk)
    ws.append([None,'Cộng B — Ngoài màn hình',extra,extra*RATE,None]); ws.append([None,'C. TỔNG MANDAY GỐC (A+B)',base,base*RATE,None]); ws.append([None,'D. HỆ SỐ RỦI RO / PHỨC TẠP',risk,None,'AI/tích hợp/bảo mật/workflow nếu áp dụng']); ws.append([None,'E. GRAND TOTAL',final,final*RATE,'Chưa bao gồm VAT']); ws.append([None,f'Đơn giá: {RATE:,} VNĐ/manday | Risk factor: x{risk} | Nền tảng: Web App + Mobile responsive',None,None,None])

def _assumptions(wb,m):
    ws=wb.create_sheet('Giả định'); ws.append(['STT','Loại','Nội dung giả định']); idx=1
    for x in m.assumptions: ws.append([idx,'Phạm vi',x]); idx+=1
    for x in m.out_of_scope: ws.append([idx,'Ngoài phạm vi',x]); idx+=1
    ws.append([idx,'Thương mại',f'Đơn giá manday: {RATE:,} VNĐ/MD. Giá chưa bao gồm VAT.'])

def _style(wb):
    for sh in wb.worksheets:
        thin=Side(style='thin',color='CCCCCC')
        for row in sh.iter_rows():
            for c in row: c.border=Border(left=thin,right=thin,top=thin,bottom=thin); c.alignment=Alignment(wrap_text=True,vertical='top')
        for c in sh[1]: c.font=Font(bold=True,color='FFFFFF'); c.fill=PatternFill('solid',fgColor='305496')
        for r in range(2,sh.max_row+1):
            st=sh.cell(r,1).value
            if st in ['I','1','2','3','4','5'] or (isinstance(st,str) and st.startswith('∑')):
                for col in range(1,sh.max_column+1): sh.cell(r,col).font=Font(bold=True); sh.cell(r,col).fill=PatternFill('solid',fgColor='D9EAF7')
        for i,w in enumerate([12,52,18,12,18,70][:sh.max_column],1): sh.column_dimensions[get_column_letter(i)].width=w
