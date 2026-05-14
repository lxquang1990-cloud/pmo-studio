from pmo_studio.domain.rendering import build_render_context, render_table


def test_render_context_uses_yaml_pack_modules():
    ctx = build_render_context("HRM nhân sự payroll leave attendance")
    assert ctx.pack.id == "hrm"
    assert any("payroll" in m.lower() for m in ctx.modules)
    text = render_table(ctx.requirements)
    assert "REQ-CORE-001" in text
    assert "BR-CORE-001" in text
