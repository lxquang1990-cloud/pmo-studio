from pmo_studio.domain.pack_loader import load_domain_pack

def test_expanded_domain_packs_have_capabilities_v2():
    for d in ['hse','procurement','legal_ai','hrm','lms']:
        raw=load_domain_pack(d).raw
        assert raw.get('capabilities_v2'), d
        assert raw.get('data_entities'), d
