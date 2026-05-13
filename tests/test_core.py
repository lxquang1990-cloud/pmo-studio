from pathlib import Path
from pmo_studio.core.ids import IdAllocator, validate_id, extract_ids
from pmo_studio.core.project import Project
from pmo_studio.generators.stage0 import generate_stage0
from pmo_studio.generators.ba import generate_ba
from pmo_studio.generators.po_pm_ic import generate_po, generate_pm, generate_ic
from pmo_studio.traceability.engine import TraceabilityEngine
from pmo_studio.gates.gate_a import run_gate_a


def test_id_allocator():
    a = IdAllocator()
    assert a.issue('REQ', 'AUTH') == 'REQ-AUTH-001'
    us = a.issue('US')
    assert a.issue('AC', parent_us=us) == 'AC-001-01'
    assert validate_id('SRC-001')
    assert 'REQ-AUTH-001' in extract_ids('See REQ-AUTH-001')


def test_project_full_scaffold(tmp_path):
    p = Project.create('demo-pmo', customer='Demo', root_base=tmp_path)
    generate_stage0(p)
    generate_po(p); generate_pm(p); generate_ba(p); generate_ic(p)
    TraceabilityEngine(p.root).write_outputs()
    assert (p.root / 'artifacts/ba/06-quotation.xlsx').exists()
    assert (p.root / 'artifacts/ic/01-fit-gap.xlsx').exists()
    assert (p.root / 'traceability/rtm.md').exists()
    r = run_gate_a(p.root / 'artifacts/ba/03-srs/srs.md', 'ba.srs')
    assert r.passed
    q = run_gate_a(p.root / 'artifacts/ba/06-quotation.xlsx', 'ba.quotation')
    assert q.passed
