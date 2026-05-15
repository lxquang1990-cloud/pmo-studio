from __future__ import annotations
import re
from dataclasses import dataclass, field
from pmo_studio.model.translation import _t

@dataclass
class TranslationResult:
    text: str
    warnings: list[str] = field(default_factory=list)

VI_CHARS = re.compile(r'[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]', re.I)

class TranslationEngine:
    def translate(self, text: str, target_lang: str = 'en') -> TranslationResult:
        if target_lang == 'vi': return TranslationResult(text)
        out = _t(text)
        warnings=[]
        if VI_CHARS.search(out): warnings.append('possible_vi_residue')
        return TranslationResult(out, warnings)

def translate_text(text: str, target_lang: str='en') -> str:
    return TranslationEngine().translate(text, target_lang).text
