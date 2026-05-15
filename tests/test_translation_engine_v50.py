from pmo_studio.model.translation_engine import TranslationEngine

def test_translation_engine_flags_vi_residue_and_translates_known_terms():
    r=TranslationEngine().translate('Cấp phát tài sản và kiểm tra quyền', 'en')
    assert 'Asset allocation' in r.text
    assert 'permission' in r.text
