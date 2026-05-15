from pmo_studio.model.content_polish import polish_model
from pmo_studio.model.schema import BAModel, ProjectInfo, DomainInfo, Requirement

def test_content_polish_expands_weak_requirement():
    m=BAModel('x','now',ProjectInfo('p'),DomainInfo('d'),requirements=[Requirement('REQ-1','F','Cấp phát tài sản','short')])
    polish_model(m,'vi')
    assert 'Hệ thống cho phép' in m.requirements[0].description
    assert len(m.requirements[0].description.split()) > 10
