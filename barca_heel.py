
import re
from typing import Optional

def extract_heel_mm_from_descr(descr: str) -> Optional[float]:
    """
    Regole Diego (solo sulla descrizione, NON sul codice):
    - Preferisci Txx (mm) es: T30 => 30mm
    - Altrimenti primo numero:
      - 6,5 => 6 cm e 5 mm => 65mm
      - intero senza 0 finale => cm => *10
      - intero con 0 finale => mm
    """
    if not descr:
        return None
    s = str(descr).upper()

    m = re.search(r'\bT\s*(\d+(?:[.,]\d{1,2})?)\b', s)
    token = m.group(1) if m else None
    if token is None:
        m2 = re.search(r'(\d+(?:[.,]\d{1,2})?)', s)
        if not m2:
            return None
        token = m2.group(1)

    if '.' in token or ',' in token:
        a, b = re.split(r'[.,]', token, maxsplit=1)
        try:
            cm = int(a)
            mm = int(b)
            return float(cm * 10 + mm)
        except Exception:
            return None

    try:
        n = int(token)
    except Exception:
        return None

    if n % 10 != 0:
        return float(n * 10)
    return float(n)
