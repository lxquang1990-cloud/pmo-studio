from pmo_studio.model.quality import _semantic_model_checks
from pmo_studio.model.schema import BAModel, ProjectInfo, DomainInfo, Requirement, AcceptanceCriteria

def test_semantic_quality_catches_weak_req_and_duplicate_ac():
    m=BAModel('x','now',ProjectInfo('p'),DomainInfo('d'),requirements=[Requirement('REQ-1','F','Name','short')],acceptance_criteria=[AcceptanceCriteria('AC-1','US','REQ-1','g','w','t'),AcceptanceCriteria('AC-2','US','REQ-1','g','w','t')])
    ids={f.id for f in _semantic_model_checks(m)}
    assert 'Q3-WEAK-REQ' in ids
    assert 'Q3-INCOMPLETE-REQ' in ids
    assert 'Q3-DUP-AC' in ids
