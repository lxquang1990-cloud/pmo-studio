# Template Excel Testcase PMS AI Q&A

## Mục đích

Đây là template Excel chuẩn để lập, review và ghi nhận kết quả testcase cho chức năng **AI Q&A** dựa trên dữ liệu thật của hệ thống, đặc biệt phù hợp với PMS/eOffice.

Template này là file **BA/QA-facing**: ưu tiên dễ đọc, dễ filter, dễ gửi stakeholder. Raw API/debug execution không nằm trong workbook này; nếu cần, AI Agent Tester phải lưu ở artifact riêng như `execution_raw.jsonl`, `execution_summary.json` hoặc `execution_log.md`.

## Cấu trúc workbook chuẩn

Workbook cuối chỉ gồm 4 sheet:

| Sheet | Mục đích |
|---|---|
| `00_Bia` | Thông tin bộ testcase: dự án/hệ thống, module, số testcase, phạm vi. |
| `00_TomTat_KetQua_Test` | Tóm tắt cách dùng, số lượng testcase, cột kết quả chính và phân bổ trạng thái. |
| `01_ChuThich` | Giải thích các cột chính bằng ngôn ngữ BA/QA. |
| `02_TatCa_TestCases` | Sheet chính chứa toàn bộ testcase, có filter/freeze header. |

Không tách sheet theo nhóm A-J nữa. Nhóm test được thể hiện bằng cột `Loại test`.

## Bộ cột chuẩn

Sheet `02_TatCa_TestCases` dùng đúng 15 cột sau:

| # | Cột | Ý nghĩa |
|---:|---|---|
| 1 | Mã TC | Mã testcase. Khuyến nghị: `TC_<DOMAIN>_<GROUP>_<NNN>`, ví dụ `PMS-AI-STAT-2026-001`. |
| 2 | Module | Phân hệ hoặc module đang kiểm thử, ví dụ `PMS AI Q&A`. |
| 3 | Chức năng | Nhóm chức năng hoặc mục tiêu kiểm thử. |
| 4 | Loại test | Nhóm kiểm thử nghiệp vụ A-J. |
| 5 | Priority | Mức ưu tiên: `P1`, `P2`, `P3`. |
| 6 | Tiêu đề testcase | Tên ngắn gọn, dễ hiểu của testcase/câu hỏi. |
| 7 | Tiền điều kiện | Vai trò đăng nhập, phạm vi dữ liệu, dữ liệu cần tồn tại, nguồn đối chiếu. |
| 8 | Các bước thực hiện | Các bước hỏi AI, kiểm tra kết quả và ghi nhận evidence. |
| 9 | Dữ liệu test | Câu hỏi tự nhiên, input, filter hoặc dữ liệu mẫu dùng để test. |
| 10 | Kết quả mong đợi | Câu trả lời/hành vi kỳ vọng của AI, gồm quy tắc đúng/sai rõ ràng. |
| 11 | Kết quả thực tế | Chỉ chứa nội dung phản hồi AI người dùng nhìn thấy, không chứa JSON/API log. |
| 12 | Trạng thái | Kết quả test: `Pass`, `Fail`, `Review`, `Not Run`, `Blocked`. |
| 13 | Tester | Người thực hiện test. |
| 14 | Ngày test | Ngày thực hiện test. |
| 15 | Ghi chú | Ghi chú nghiệp vụ/QA nếu cần. |

## Nhóm `Loại test`

Cột `Loại test` dùng các nhãn chuẩn:

```text
A - Dữ kiện trực tiếp
B - Tổng hợp, tính toán
C - Tìm kiếm, lọc dữ liệu
D - Thời gian, tiến trình
E - Dữ liệu lồng nhau/chi tiết
F - File đính kèm
G - So sánh
H - Citation/nguồn tham chiếu
I - Phân quyền dữ liệu
J - Adversarial/chống bịa dữ liệu
```

## Các cột không đưa vào workbook final

Các cột kỹ thuật/debug sau không thuộc template BA/QA-facing:

```text
Mã defect
HTTP Status
API Success
Actual response
Follow-up questions
Auto verdict
Execution note
Executed at
```

Nếu cần lưu các dữ liệu này, AI Agent Tester phải ghi vào raw execution artifact riêng.

## Quy tắc `Kết quả thực tế`

`Kết quả thực tế` chỉ giữ nội dung AI trả lời cho người dùng. Nếu raw response có dạng:

```json
{"data": {"answer": "..."}, "success": true}
```

thì workbook chỉ ghi phần `data.answer`.

Không ghi vào workbook:

```text
Executed at
HTTP status
Elapsed
JSON wrapper
success/message/citations/should_auto_search
```

## Quy tắc `Trạng thái`

`Trạng thái` là kết quả test chính.

Giá trị chuẩn:

```text
Pass
Fail
Review
Not Run
Blocked
```

Nếu agent không chắc pass/fail, dùng `Review`, không tự ép `Pass`.

## Tích hợp trong PMO Studio

Exporter module:

```python
pmo_studio.exporters.pms_ai_testcase_template
```

API chính:

```python
from pmo_studio.exporters.pms_ai_testcase_template import PmsAiTestCase, export_pms_ai_testcases

export_pms_ai_testcases(cases, out_path)
```

`webdoc-ingest` hiện cũng xuất workbook theo template này tại:

```text
artifacts/ba/05-test-cases.xlsx
```

## Quality gate cho AI Agent Tester

Trước khi xuất file final, agent nên kiểm tra:

- [ ] Workbook có đúng 4 sheet chuẩn không?
- [ ] Sheet `02_TatCa_TestCases` có đúng 15 cột bắt buộc không?
- [ ] Không còn cột kỹ thuật/debug không?
- [ ] `Kết quả thực tế` không còn JSON/API wrapper không?
- [ ] `Trạng thái` chỉ dùng tập giá trị chuẩn không?
- [ ] Có auto filter/freeze header không?
- [ ] Không còn text nội bộ như `Generated từ...` không?

## Nguyên tắc thiết kế

**Workbook cho người đọc, raw log cho máy đọc.**

Cách này giúp bộ testcase vừa sạch để BA/QA dùng, vừa đủ cấu trúc để AI Agent Tester tự động ingest, execute, update kết quả và xuất báo cáo sau này.
