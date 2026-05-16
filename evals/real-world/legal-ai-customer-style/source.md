# Legal AI Customer-Style Source

Khách hàng cần hệ thống Legal AI hỗ trợ phòng pháp chế xử lý câu hỏi pháp lý nội bộ, quản lý ủy quyền và rà soát hợp đồng.

## Modules

1. Hỏi đáp pháp lý nội bộ
   - Người dùng gửi câu hỏi, đính kèm tài liệu, chọn chủ đề và mức độ ưu tiên.
   - AI gợi ý câu trả lời có trích dẫn nguồn từ kho tri thức đã duyệt.
   - Legal Officer review trước khi phát hành câu trả lời cuối.

2. Quản lý ủy quyền
   - Tạo đề nghị ủy quyền với người ủy quyền, người được ủy quyền, phạm vi, thời hạn.
   - Trình duyệt, ký số SmartCA/eOffice và phát hành văn bản ủy quyền.
   - Cảnh báo hết hạn và thu hồi/điều chỉnh ủy quyền.

3. Soạn thảo và rà soát hợp đồng
   - Tạo draft từ template hợp đồng.
   - AI phát hiện điều khoản rủi ro, nghĩa vụ, deadline và thiếu điều khoản bắt buộc.
   - Tích hợp PMS/eOffice để lấy metadata dự án và trình phê duyệt.

## Non-functional

- RBAC theo Business User, Legal Officer, Approver, Admin, Auditor.
- Audit log đầy đủ cho generate AI answer, review, publish, approve, sign.
- AI output là bản nháp hỗ trợ, không thay thế ý kiến pháp lý chính thức.
- Dữ liệu confidential chỉ hiển thị theo quyền.

## Out of scope

- Tư vấn pháp lý tự động không có người duyệt.
- Ký số vendor mới ngoài SmartCA/eOffice trong phase 1.
