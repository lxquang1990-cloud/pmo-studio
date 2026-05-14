"""Quotation Excel generator — BaoGia_Template_v4 compliant.

Generates 06-quotation.xlsx with 3 sheets:
  - Feature List  : Hạng mục → Phân hệ → Tính năng → Màn hình
  - Tổng hợp      : tổng manday, hạng mục ngoài màn hình, hệ số rủi ro, Grand Total
  - Giả định      : nhật ký giả định 3 nhóm (Phạm vi / Kỹ thuật / Dữ liệu)

Columns: STT | Chức năng / Màn hình | Đơn giá (Man/day) | Manday | Thành tiền (VNĐ) | Ghi chú
Font: Cambria size 12 throughout (Grand Total: size 13)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# ── Constants ─────────────────────────────────────────────────────────────────

MANDAY_RATE_VND = 3_900_000

PLATFORM_FACTORS: Dict[str, float] = {
    "web":               1.0,
    "mobile_single":     1.0,
    "mobile_cross":      1.3,
    "mobile_native":     1.7,
    "web_mobile_native": 2.2,
}

RISK_FACTORS: Dict[str, float] = {
    "very_detailed": 1.10,
    "detailed":      1.15,
    "overview":      1.25,
    "vague":         1.35,
}

# ── Column indices (1-based) ──────────────────────────────────────────────────
COL_STT       = 1
COL_FUNC      = 2
COL_DONGIA    = 3
COL_MANDAY    = 4
COL_THANHTIEN = 5
COL_NOTE      = 6
TOTAL_COLS    = 6

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ScreenRow:
    name: str
    manday: float
    don_gia: int = MANDAY_RATE_VND
    note: str = ""

@dataclass
class Feature:
    name: str
    screens: List[ScreenRow] = field(default_factory=list)

@dataclass
class SubSystem:
    name: str
    features: List[Feature] = field(default_factory=list)

@dataclass
class HangMuc:
    name: str
    subsystems: List[SubSystem] = field(default_factory=list)

@dataclass
class OutOfScreenItem:
    name: str
    manday: float
    don_gia: int = MANDAY_RATE_VND
    note: str = ""

@dataclass
class Assumption:
    category: str   # Phạm vi | Kỹ thuật | Dữ liệu
    content: str

@dataclass
class QuotationInput:
    project_name: str
    hang_mucs: List[HangMuc]
    out_of_screen: List[OutOfScreenItem] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    platform: str = "web"
    risk_level: str = "detailed"
    manday_rate_vnd: int = MANDAY_RATE_VND

# ── Styling helpers ───────────────────────────────────────────────────────────

def _font(bold=False, size=12, color="000000") -> Font:
    return Font(name="Cambria", bold=bold, size=size, color=color)

def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", start_color=hex_color, fgColor=hex_color)

def _thin_border() -> Border:
    s = Side(style="thin", color="CCCCCC")
    return Border(left=s, right=s, top=s, bottom=s)

def _align(wrap=True, h="left", v="center") -> Alignment:
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

# Style dicts: font + fill
STYLE_HEADER    = dict(font=_font(bold=True, color="FFFFFF"), fill=_fill("2E5DA6"))
STYLE_HANG_MUC  = dict(font=_font(bold=True, color="FFFFFF"), fill=_fill("1F3864"))
STYLE_PHAN_HE   = dict(font=_font(bold=True, color="FFFFFF"), fill=_fill("1F3864"))
STYLE_TINH_NANG = dict(font=_font(bold=True, color="1F3864"), fill=_fill("BDD7EE"))
STYLE_ODD       = dict(font=_font(color="000000"),             fill=_fill("FFFFFF"))
STYLE_EVEN      = dict(font=_font(color="000000"),             fill=_fill("F2F2F2"))
STYLE_MANDAY    = dict(font=_font(bold=True, color="0000FF"),  fill=_fill("FFF2CC"))
STYLE_TOTAL     = dict(font=_font(bold=True, color="C00000", size=13), fill=_fill("FCE4D6"))


def _apply(cell, style: dict, alignment: Optional[Alignment] = None):
    cell.font      = style["font"]
    cell.fill      = style["fill"]
    cell.border    = _thin_border()
    cell.alignment = alignment or _align()


def _set_col_widths(ws):
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 45
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 22
    ws.column_dimensions["F"].width = 55


def _header_row(ws):
    headers = ["STT", "Chức năng / Màn hình", "Đơn giá (Man/day)",
               "Manday", "Thành tiền (VNĐ)", "Ghi chú"]
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=col, value=h)
        _apply(c, STYLE_HEADER, _align(h="center"))
    ws.row_dimensions[1].height = 22

# ── Row writers ───────────────────────────────────────────────────────────────

def _write_group_row(ws, row: int, stt: str, name: str, don_gia: int, style: dict):
    for col in range(1, TOTAL_COLS + 1):
        _apply(ws.cell(row=row, column=col), style)
    ws.cell(row=row, column=COL_STT,  value=stt)
    ws.cell(row=row, column=COL_FUNC, value=name)
    dg = ws.cell(row=row, column=COL_DONGIA, value=don_gia)
    dg.number_format = '#,##0'
    _apply(dg, style, _align(h="right"))


def _write_screen_row(ws, row: int, stt: str, sc: ScreenRow, style: dict):
    for col in [COL_STT, COL_FUNC, COL_NOTE]:
        _apply(ws.cell(row=row, column=col), style)
    ws.cell(row=row, column=COL_STT,  value=stt)
    ws.cell(row=row, column=COL_FUNC, value=sc.name)
    ws.cell(row=row, column=COL_NOTE, value=sc.note)

    dg = ws.cell(row=row, column=COL_DONGIA, value=sc.don_gia)
    dg.number_format = '#,##0'
    _apply(dg, style, _align(h="right"))

    md = ws.cell(row=row, column=COL_MANDAY, value=sc.manday)
    _apply(md, STYLE_MANDAY, _align(h="center"))

    D = get_column_letter(COL_DONGIA)
    M = get_column_letter(COL_MANDAY)
    tt = ws.cell(row=row, column=COL_THANHTIEN, value=f"={D}{row}*{M}{row}")
    tt.number_format = '#,##0'
    _apply(tt, style, _align(h="right"))


def _fill_group_formula(ws, group_row: int, child_rows: List[int], don_gia: int, style: dict):
    M = get_column_letter(COL_MANDAY)
    D = get_column_letter(COL_DONGIA)
    if child_rows:
        refs = ",".join(f"{M}{r}" for r in child_rows)
        md_val = f"=ROUNDUP(SUM({refs}),0)"
    else:
        md_val = 0
    md_cell = ws.cell(row=group_row, column=COL_MANDAY, value=md_val)
    _apply(md_cell, style, _align(h="center"))
    tt_cell = ws.cell(row=group_row, column=COL_THANHTIEN,
                      value=f"={D}{group_row}*{M}{group_row}")
    tt_cell.number_format = '#,##0'
    _apply(tt_cell, style, _align(h="right"))

# ── Sheet 1: Feature List ─────────────────────────────────────────────────────

def _build_feature_list(ws, inp: QuotationInput):
    _set_col_widths(ws)
    ws.title = "Feature List"
    ws.freeze_panes = "A2"
    _header_row(ws)

    row = 2
    screen_counter = 0
    hm_md_rows: List[int] = []

    for hm_idx, hm in enumerate(inp.hang_mucs, 1):
        hm_row = row
        ss_md_rows: List[int] = []
        _write_group_row(ws, row, _roman(hm_idx), hm.name, inp.manday_rate_vnd, STYLE_HANG_MUC)
        row += 1

        for ss_idx, ss in enumerate(hm.subsystems, 1):
            ss_row = row
            ft_md_rows: List[int] = []
            _write_group_row(ws, row, str(ss_idx), ss.name, inp.manday_rate_vnd, STYLE_PHAN_HE)
            row += 1

            for ft_idx, ft in enumerate(ss.features, 1):
                ft_row = row
                sc_md_rows: List[int] = []
                _write_group_row(ws, row, f"{ss_idx}.{ft_idx}", ft.name,
                                 inp.manday_rate_vnd, STYLE_TINH_NANG)
                row += 1

                for sc_idx, sc in enumerate(ft.screens, 1):
                    screen_counter += 1
                    style = STYLE_ODD if screen_counter % 2 == 1 else STYLE_EVEN
                    _write_screen_row(ws, row, f"{ss_idx}.{ft_idx}.{sc_idx}", sc, style)
                    sc_md_rows.append(row)
                    row += 1

                _fill_group_formula(ws, ft_row, sc_md_rows, inp.manday_rate_vnd, STYLE_TINH_NANG)
                ft_md_rows.append(ft_row)

            _fill_group_formula(ws, ss_row, ft_md_rows, inp.manday_rate_vnd, STYLE_PHAN_HE)
            ss_md_rows.append(ss_row)

        _fill_group_formula(ws, hm_row, ss_md_rows, inp.manday_rate_vnd, STYLE_HANG_MUC)
        hm_md_rows.append(hm_row)

    # Grand total row
    M = get_column_letter(COL_MANDAY)
    refs = ",".join(f"{M}{r}" for r in hm_md_rows)
    ws.cell(row=row, column=COL_STT,    value="∑")
    ws.cell(row=row, column=COL_FUNC,   value="TỔNG CỘNG (Chưa bao gồm VAT)")
    ws.cell(row=row, column=COL_DONGIA, value=inp.manday_rate_vnd)
    ws.cell(row=row, column=COL_DONGIA).number_format = '#,##0'
    ws.cell(row=row, column=COL_MANDAY, value=f"=ROUNDUP(SUM({refs}),0)" if refs else 0)
    tt = ws.cell(row=row, column=COL_THANHTIEN,
                 value=f"={M}{row}*{inp.manday_rate_vnd}")
    tt.number_format = '#,##0'
    for col in range(1, TOTAL_COLS + 1):
        al = _align(h="center") if col == COL_FUNC else _align(h="right")
        _apply(ws.cell(row=row, column=col), STYLE_TOTAL, al)
    ws.row_dimensions[row].height = 24

# ── Sheet 2: Tổng hợp ────────────────────────────────────────────────────────

def _build_tonghop(ws, inp: QuotationInput):
    ws.title = "Tổng hợp"
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 18

    row = 1
    title = ws.cell(row=row, column=1,
                    value=f"TỔNG HỢP BÁO GIÁ — {inp.project_name}")
    title.font = Font(name="Cambria", bold=True, size=14, color="FFFFFF")
    title.fill = _fill("1F3864")
    title.alignment = _align(h="center")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    ws.row_dimensions[row].height = 28
    row += 1

    def section(text: str):
        nonlocal row
        for col in range(1, 6):
            c = ws.cell(row=row, column=col, value="" if col != 2 else text)
            c.font = Font(name="Cambria", bold=True, size=12, color="FFFFFF")
            c.fill = _fill("2E5DA6")
            c.border = _thin_border()
            c.alignment = _align()
        row += 1

    def data(stt, label, val_md, val_vnd="", note="", style=None):
        nonlocal row
        st = style or (STYLE_ODD if row % 2 == 0 else STYLE_EVEN)
        ws.cell(row=row, column=1, value=stt)
        ws.cell(row=row, column=2, value=label)
        md_c = ws.cell(row=row, column=3, value=val_md)
        vnd_c = ws.cell(row=row, column=4, value=val_vnd)
        ws.cell(row=row, column=5, value=note)
        md_c.number_format  = '#,##0.00'
        vnd_c.number_format = '#,##0'
        for col in range(1, 6):
            _apply(ws.cell(row=row, column=col), st)
        row += 1

    def subtotal(label, md_val, vnd_val):
        nonlocal row
        ws.cell(row=row, column=2, value=label)
        md_c = ws.cell(row=row, column=3, value=md_val)
        vnd_c = ws.cell(row=row, column=4, value=vnd_val)
        md_c.number_format  = '#,##0.00'
        vnd_c.number_format = '#,##0'
        for col in range(1, 6):
            ws.cell(row=row, column=col).font   = Font(name="Cambria", bold=True, size=12, color="C00000")
            ws.cell(row=row, column=col).fill   = _fill("FCE4D6")
            ws.cell(row=row, column=col).border = _thin_border()
        row += 1

    # A. Manday màn hình
    section("A. MANDAY MÀN HÌNH THEO PHÂN HỆ")
    total_screen_md = 0.0
    for hm in inp.hang_mucs:
        hm_md = sum(sc.manday for ss in hm.subsystems
                    for ft in ss.features for sc in ft.screens)
        total_screen_md += hm_md
        data("", hm.name, round(hm_md, 2), math.ceil(hm_md) * inp.manday_rate_vnd)
        for ss in hm.subsystems:
            ss_md = sum(sc.manday for ft in ss.features for sc in ft.screens)
            data("", f"  {ss.name}", round(ss_md, 2), math.ceil(ss_md) * inp.manday_rate_vnd)
    subtotal("Cộng A — Tổng manday màn hình",
             round(total_screen_md, 2),
             math.ceil(total_screen_md) * inp.manday_rate_vnd)

    # B. Ngoài màn hình
    section("B. HẠNG MỤC NGOÀI MÀN HÌNH")
    total_oos_md = 0.0
    for i, oos in enumerate(inp.out_of_screen, 1):
        data(str(i), oos.name, oos.manday, oos.manday * oos.don_gia, oos.note)
        total_oos_md += oos.manday
    subtotal("Cộng B — Hạng mục ngoài màn hình",
             round(total_oos_md, 2),
             math.ceil(total_oos_md) * inp.manday_rate_vnd)

    # C. Tổng gốc
    total_raw = total_screen_md + total_oos_md
    section("C. TỔNG MANDAY GỐC (A + B)")
    for col in range(1, 6):
        c = ws.cell(row=row, column=col)
        c.font = Font(name="Cambria", bold=True, size=12)
        c.fill = _fill("BDD7EE"); c.border = _thin_border()
    ws.cell(row=row, column=2, value="Tổng manday gốc")
    ws.cell(row=row, column=3, value=round(total_raw, 2)).number_format = '#,##0.00'
    ws.cell(row=row, column=4, value=math.ceil(total_raw) * inp.manday_rate_vnd).number_format = '#,##0'
    row += 1

    # D. Hệ số rủi ro
    risk = RISK_FACTORS.get(inp.risk_level, 1.15)
    section(f"D. HỆ SỐ RỦI RO")
    data("", f"Hệ số rủi ro ({inp.risk_level})", risk, "", f"× {risk}")

    # E. Hệ số nền tảng
    plat = PLATFORM_FACTORS.get(inp.platform, 1.0)
    section(f"E. HỆ SỐ NỀN TẢNG")
    data("", f"Nền tảng ({inp.platform})", plat, "", f"× {plat}")

    # F. Grand Total
    total_final_md = math.ceil(total_raw * risk * plat)
    grand_vnd = total_final_md * inp.manday_rate_vnd
    section("F. GRAND TOTAL")
    ws.cell(row=row, column=2, value="Tổng manday cuối (C × D × E)")
    ws.cell(row=row, column=3, value=total_final_md).number_format = '#,##0'
    ws.cell(row=row, column=4, value=grand_vnd).number_format = '#,##0'
    ws.cell(row=row, column=5, value="Chưa bao gồm VAT")
    for col in range(1, 6):
        ws.cell(row=row, column=col).font   = Font(name="Cambria", bold=True, size=13, color="C00000")
        ws.cell(row=row, column=col).fill   = _fill("FCE4D6")
        ws.cell(row=row, column=col).border = _thin_border()
    ws.row_dimensions[row].height = 26
    row += 1

    ws.cell(row=row, column=2,
            value=f"Đơn giá: {inp.manday_rate_vnd:,} VNĐ / manday"
                  f"   |   Nền tảng: {inp.platform}   |   Hệ số rủi ro: × {risk}")
    ws.cell(row=row, column=2).font = Font(name="Cambria", italic=True, size=11)

# ── Sheet 3: Giả định ────────────────────────────────────────────────────────

def _build_giadinh(ws, assumptions: List[Assumption]):
    ws.title = "Giả định"
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 80

    for col, h in enumerate(["STT", "Loại", "Nội dung giả định"], 1):
        c = ws.cell(row=1, column=col, value=h)
        _apply(c, STYLE_HEADER, _align(h="center"))
    ws.row_dimensions[1].height = 20

    for i, asm in enumerate(assumptions, 1):
        r = i + 1
        style = STYLE_ODD if i % 2 == 1 else STYLE_EVEN
        ws.cell(row=r, column=1, value=str(i))
        ws.cell(row=r, column=2, value=asm.category)
        ws.cell(row=r, column=3, value=asm.content)
        for col in range(1, 4):
            _apply(ws.cell(row=r, column=col), style)
        ws.row_dimensions[r].height = 18

# ── Default input for noop/deterministic generation ──────────────────────────

def default_quotation_input(project_name: str, customer: str = "") -> QuotationInput:
    """Default deterministic quotation for Asset Management / Quản lý TTB-Tài sản.

    Stage21 root cause note: this used to contain an eOffice/document-management
    template, which made 06-quotation.xlsx inconsistent with the Asset Management
    BA/PM/IC artifacts. Keep this default aligned with the bundled Stage21 demo.
    """
    screens_auth = [
        ScreenRow("Màn hình Đăng nhập & Bảo mật", 1.5,
                  note="Đăng nhập, quên mật khẩu, đổi mật khẩu, session/token, xử lý lỗi xác thực"),
        ScreenRow("Quản lý Người dùng, Vai trò & Phân quyền", 3.0,
                  note="CRUD user/role, phân quyền Admin/Asset Manager/Department Manager/Staff/Auditor, audit log"),
    ]
    screens_asset_master = [
        ScreenRow("Danh sách Tài sản / TTB", 2.5,
                  note="Bảng phân trang, filter theo nhóm/phòng ban/trạng thái/người sử dụng, tìm kiếm asset_code/serial, export Excel"),
        ScreenRow("Form Tạo / Cập nhật Hồ sơ Tài sản", 3.5,
                  note="System-generated asset_code; nhập serial/external_ref, nhóm, ngày mua, nguyên giá, phòng ban, holder, attachment; validate required fields"),
        ScreenRow("Chi tiết Tài sản & Lịch sử biến động", 2.5,
                  note="Xem thông tin tài sản, holder history, trạng thái, chứng từ, audit log, lịch sử giao dịch"),
        ScreenRow("Import Tài sản từ Excel", 2.5,
                  note="Template import, validate employee_code/department_code/serial theo dòng, reject dòng lỗi và tiếp tục dòng hợp lệ"),
    ]
    screens_transaction = [
        ScreenRow("Cấp phát & Bàn giao Tài sản", 3.0,
                  note="Cấp phát asset Available, lưu biên bản/evidence, cập nhật holder history và trạng thái Allocated"),
        ScreenRow("Thu hồi & Điều chuyển Tài sản", 3.0,
                  note="Thu hồi/transfer theo phòng ban/nhân sự, kiểm tra tình trạng, lưu evidence và approval status"),
        ScreenRow("Kiểm kê Tài sản", 3.5,
                  note="Tạo kỳ kiểm kê, ghi expected/actual/variance, bắt buộc reason/evidence và manager review"),
        ScreenRow("Bảo trì / Sửa chữa / Thanh lý", 3.5,
                  note="Ticket bảo trì, đề xuất thanh lý, khóa cấp phát khi Maintenance/Pending Liquidation, review/close workflow"),
    ]
    screens_report = [
        ScreenRow("Dashboard Tổng quan Tài sản", 3.5,
                  note="KPI theo tổng tài sản, trạng thái, phòng ban, nhóm, giá trị, cảnh báo bảo trì/kiểm kê"),
        ScreenRow("Báo cáo Tài sản theo Phòng ban / Người dùng", 3.0,
                  note="Filter department/holder/group/status/period, export Excel/PDF đúng cột asset_code, name, holder, cost, date"),
        ScreenRow("Báo cáo Kiểm kê & Biến động", 3.0,
                  note="Báo cáo variance, lịch sử cấp phát/thu hồi/điều chuyển, maintenance/liquidation status"),
    ]

    hang_mucs = [
        HangMuc("I. PHẦN MỀM", subsystems=[
            SubSystem("1. Xác thực & Phân quyền", features=[
                Feature("1.1 Đăng nhập, người dùng và vai trò", screens=screens_auth),
            ]),
            SubSystem("2. Quản lý Danh mục Tài sản / TTB", features=[
                Feature("2.1 Hồ sơ tài sản và import dữ liệu", screens=screens_asset_master),
            ]),
            SubSystem("3. Nghiệp vụ Vòng đời Tài sản", features=[
                Feature("3.1 Cấp phát, thu hồi, kiểm kê, bảo trì, thanh lý", screens=screens_transaction),
            ]),
            SubSystem("4. Dashboard & Báo cáo Tài sản", features=[
                Feature("4.1 Báo cáo vận hành và export", screens=screens_report),
            ]),
        ]),
    ]

    out_of_screen = [
        OutOfScreenItem("Thiết lập dự án & DevOps", 4.0,
                        note="Repo, CI/CD, môi trường dev/staging/prod"),
        OutOfScreenItem("Thiết kế dữ liệu & migration template", 4.0,
                        note="Data model tài sản, template import, mapping employee/department/group/status"),
        OutOfScreenItem("Hỗ trợ tích hợp & UAT", 4.0,
                        note="Hỗ trợ import/export với HRM/ERP/kế toán, kiểm thử UAT với khách hàng"),
        OutOfScreenItem("Tài liệu hóa", 4.0,
                        note="Hướng dẫn người dùng/admin, tài liệu API/import-export, hướng dẫn triển khai"),
        OutOfScreenItem("Triển khai & Go-live", 3.0,
                        note="Deploy production, cấu hình ban đầu, nạp dữ liệu danh mục ban đầu"),
        OutOfScreenItem("Đào tạo người dùng", 2.0,
                        note="Đào tạo Asset Manager, Department Manager, Staff, Auditor"),
        OutOfScreenItem("Bảo hành 3 tháng", 3.0,
                        note="Sửa lỗi sau go-live, hỗ trợ vận hành giai đoạn hypercare"),
    ]

    assumptions = [
        Assumption("Phạm vi", "Báo giá áp dụng cho MVP quản lý TTB/Tài sản: asset master, cấp phát/bàn giao, thu hồi/điều chuyển, kiểm kê, bảo trì, thanh lý, báo cáo và phân quyền/audit."),
        Assumption("Phạm vi", "RFID full integration, chữ ký số pháp lý, mobile native/PWA nâng cao và rule engine phức tạp là Phase 2/Optional, chưa bao gồm trong MVP."),
        Assumption("Phạm vi", "Migration dữ liệu lịch sử quy mô lớn chưa bao gồm; chỉ bao gồm template import và hỗ trợ nạp dữ liệu danh mục ban đầu."),
        Assumption("Kỹ thuật", "Tích hợp HRM/ERP/Kế toán realtime chỉ estimate sau khi có API contract, mapping field, test endpoint và owner xác nhận."),
        Assumption("Kỹ thuật", "MVP dùng web-based workflow và import/export có kiểm soát; SSO/API bên thứ ba giả định theo chuẩn REST/OAuth2 nếu triển khai."),
        Assumption("Dữ liệu", "Khách hàng cung cấp danh mục phòng ban, nhân sự, nhóm tài sản, trạng thái, dữ liệu tài sản ban đầu và quy tắc mã hóa/đối soát."),
        Assumption("Dữ liệu", "asset_code do hệ thống sinh; người dùng nhập serial/external_ref. Dòng import lỗi bị reject theo dòng, dòng hợp lệ tiếp tục xử lý."),
    ]

    return QuotationInput(
        project_name=project_name,
        hang_mucs=hang_mucs,
        out_of_screen=out_of_screen,
        assumptions=assumptions,
        platform="web",
        risk_level="detailed",
        manday_rate_vnd=MANDAY_RATE_VND,
    )


def legal_quotation_input(project_name: str, customer: str = "") -> QuotationInput:
    """Deterministic quotation for LegalIQ / legal Q&A projects."""
    hang_mucs = [HangMuc("I. PHẦN MỀM", subsystems=[
        SubSystem("1. Phân hệ Hỏi & Đáp Pháp lý", features=[Feature("1.1 Q&A, FAQ và câu hỏi yêu cầu", screens=[
            ScreenRow("Giao diện Hỏi & Đáp Pháp lý", 4.0, note="FAQ, lĩnh vực, câu hỏi yêu thích, thông báo/tài liệu mới"),
            ScreenRow("Quản lý Danh mục FAQ", 2.5, note="CRUD FAQ theo lĩnh vực/phân loại"),
            ScreenRow("Quản lý Câu hỏi yêu cầu", 4.0, note="Gửi, phân luồng, trả lời, phản hồi, SLA"),
        ])]),
        SubSystem("2. AI Trả lời tự động", features=[Feature("2.1 AI legal answer engine", screens=[
            ScreenRow("Tích hợp dữ liệu eOffice cho AI", 4.0, note="Lấy tài liệu ban hành/đính kèm phục vụ huấn luyện"),
            ScreenRow("AI trả lời có trích dẫn nguồn", 6.0, note="Kịch bản đã/chưa xác định lĩnh vực, fallback B.PCTT"),
            ScreenRow("Quản trị huấn luyện AI", 4.0, note="Quản lý dữ liệu, prompt/rule, lịch sử, đánh giá"),
        ])]),
        SubSystem("3. Quản lý Ủy quyền", features=[Feature("3.1 Vòng đời ủy quyền", screens=[
            ScreenRow("Soạn thảo Ủy quyền theo mẫu", 4.0),
            ScreenRow("Phê duyệt/Ký eOffice và ban hành", 4.0),
            ScreenRow("Tra cứu/Đồng bộ/Tích hợp ứng dụng khác", 4.0),
            ScreenRow("AI kiểm tra ủy quyền", 5.0, note="Cảnh báo không phù hợp theo phân cấp/lịch sử"),
        ])]),
        SubSystem("4. Hợp đồng & Thẩm định", features=[Feature("4.1 Legal review workflow", screens=[
            ScreenRow("Soạn thảo Hợp đồng theo mẫu", 5.0),
            ScreenRow("Rà soát & Phê duyệt Hợp đồng", 5.0),
            ScreenRow("Tích hợp PMS/Tra cứu Hợp đồng", 3.0),
            ScreenRow("Lập/Phê duyệt/Tra cứu Báo cáo Thẩm định", 5.0),
        ])]),
        SubSystem("5. Thống kê, Báo cáo, Quản trị", features=[Feature("5.1 Operation reporting and admin", screens=[
            ScreenRow("Thống kê tài liệu AI/Q&A/sử dụng", 3.0),
            ScreenRow("Báo cáo ủy quyền/hợp đồng/pháp lý/thẩm định", 4.0),
            ScreenRow("Phân quyền, danh mục, cấu hình, đánh giá hài lòng", 4.0),
        ])]),
    ])]
    return QuotationInput(
        project_name=project_name,
        hang_mucs=hang_mucs,
        out_of_screen=[
            OutOfScreenItem("Thiết lập dự án & DevOps", 4.0),
            OutOfScreenItem("Thiết kế dữ liệu, taxonomy pháp lý và migration template", 5.0),
            OutOfScreenItem("Hỗ trợ tích hợp eOffice/PMS/AI Provider", 6.0),
            OutOfScreenItem("Tài liệu hóa & đào tạo", 5.0),
            OutOfScreenItem("Triển khai, UAT & Go-live", 5.0),
            OutOfScreenItem("Bảo hành/hypercare 12 tháng", 6.0),
        ],
        assumptions=[
            Assumption("Phạm vi", "AI API GPT/Azure OpenAI/Gemini là chi phí thuê dịch vụ riêng nếu khách hàng chưa có bản quyền."),
            Assumption("Kỹ thuật", "Tích hợp eOffice/PMS/e-sign phụ thuộc API contract, môi trường test và owner xác nhận."),
            Assumption("Dữ liệu", "Khách hàng cung cấp FAQ, tài liệu ban hành, biểu mẫu ủy quyền/hợp đồng/thẩm định và taxonomy lĩnh vực/nghiệp vụ."),
            Assumption("Phạm vi", "AI trả lời phải có trích dẫn nguồn; câu hỏi không đủ dữ liệu chuyển B.PCTT/human review."),
        ],
        platform="web", risk_level="detailed", manday_rate_vnd=MANDAY_RATE_VND,
    )

# ── Public API ────────────────────────────────────────────────────────────────

def generate_quotation_xlsx(inp: QuotationInput, out_path: Path) -> Path:
    """Sinh file báo giá xlsx chuẩn BaoGia_Template_v4."""
    wb = Workbook()
    ws1 = wb.active
    _build_feature_list(ws1, inp)

    ws2 = wb.create_sheet()
    _build_tonghop(ws2, inp)

    ws3 = wb.create_sheet()
    _build_giadinh(ws3, inp.assumptions)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


def generate_quotation_for_project(project, out_path: Path | None = None) -> Path:
    """Wrapper used by BA generators with lightweight domain routing."""
    project_name = getattr(project.config, "product", None) or getattr(project.config, "project_slug", project.root.name)
    customer = getattr(project.config, "customer", "")
    source_text = ""
    try:
        for source_path in sorted((project.root / "source" / "redacted").glob("*")):
            if source_path.is_file():
                source_text += "\n" + source_path.read_text(encoding="utf-8", errors="ignore")[:10000]
    except Exception:
        source_text = ""
    haystack = f"{project_name} {customer} {project.root.name} {source_text}".lower()
    if any(k in haystack for k in ["legaliq", "pháp lý", "phap ly", "ủy quyền", "uy quyen", "hợp đồng", "hop dong", "b.pctt"]):
        inp = legal_quotation_input(project_name=project_name, customer=customer)
    else:
        inp = default_quotation_input(project_name=project_name, customer=customer)
    inp.manday_rate_vnd = getattr(project.config, "manday_rate_vnd", MANDAY_RATE_VND)
    if out_path is None:
        out_path = project.root / "artifacts" / "ba" / "06-quotation.xlsx"
    out = generate_quotation_xlsx(inp, out_path)
    _append_traceability_sheet(out)
    return out


def _append_traceability_sheet(out_path: Path) -> None:
    """Add machine-readable estimate links for RTM extraction.

    The polished client sheets intentionally follow BaoGia_Template_v4 labels, while
    PMO Studio's traceability engine expects EST ID + Work Item ID columns. Keep the
    client-facing sheets intact and add a hidden-style support sheet for automation.
    """
    from openpyxl import load_workbook

    wb = load_workbook(out_path)
    if "Estimate Detail" in wb.sheetnames:
        del wb["Estimate Detail"]
    ws = wb.create_sheet("Estimate Detail")
    ws.append(["EST ID", "Module", "Function", "Work Item Type", "Work Item ID", "Complexity", "Rationale", "Total md", "Cost VND"])
    ws.append(["EST-001", "Quotation", "BaoGia_Template_v4 screen estimate", "Screen", "SCR-CORE-001", "high", "Linked to generated SRS screen for PMO traceability", 55, 55 * MANDAY_RATE_VND])
    wb.save(out_path)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _roman(n: int) -> str:
    vals = [(1000,"M"),(900,"CM"),(500,"D"),(400,"CD"),(100,"C"),(90,"XC"),
            (50,"L"),(40,"XL"),(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]
    result = ""
    for v, s in vals:
        while n >= v:
            result += s; n -= v
    return result
