
import re
from io import StringIO
from typing import Dict, Optional, Tuple, List
import pandas as pd

def decode_best_effort(data: bytes) -> str:
    for enc in ["utf-8", "utf-8-sig", "cp1252", "latin1"]:
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("latin1", errors="replace")

def iter_balanced_lines(text: str):
    """
    Unisce righe finché il numero di virgolette non è pari.
    Utile quando l'export ha newline "strani" dentro ai campi.
    """
    buf = ""
    for line in text.splitlines():
        buf = buf + ("\n" if buf else "") + line
        if buf.count('"') % 2 == 0:
            yield buf
            buf = ""
    if buf:
        yield buf

def extract_quoted_fields(line: str) -> List[str]:
    return re.findall(r'"([^"]*)"', line)

_CODE_RE = re.compile(r'^\d{1,3}/[A-Z0-9]{2,}', re.IGNORECASE)

def _looks_like_reparto(x: str) -> bool:
    s = (x or "").strip()
    return bool(s) and not s.isdigit() and len(s) >= 4

def _looks_like_supplier(x: str) -> bool:
    s = (x or "").strip()
    # es: "302 IMMA S.R.L."
    return bool(re.search(r'\bS\.?R\.?L\.?\b|\bS\.?P\.?A\.?\b', s, re.IGNORECASE) or re.match(r'^\d+\s+', s))

def parse_num_token(token: str):
    s = str(token).strip()
    if s == "" or s == "%":
        return None
    if not re.fullmatch(r"[0-9][0-9\.,]*", s):
        return None
    # migliaia con '.'
    if "," not in s and "." in s:
        parts = s.split(".")
        if all(len(p)==3 for p in parts[1:]):
            s = s.replace(".", "")
    s = s.replace(",", ".")
    try:
        return float(s) if "." in s else int(s)
    except Exception:
        return None

def clean_anart_report_bytes(data: bytes) -> pd.DataFrame:
    """
    Parser per export 'ANALISI ARTICOLI' (report impaginato).
    Gestisce due forme dopo il label ARTICOLO:
    A) ARTICOLO, REPARTO, CATEGORIA, FORNITORE, N, <COD+DESC>, ORD, CON, VEND, VEN, GIAC, ...
    B) ARTICOLO, N, <COD+DESC>, ORD, CON, VEND, VEN, GIAC, ...
    Mantiene l'ultimo REPARTO/CATEGORIA/FORNITORE visti e li applica alle righe tipo B.
    """
    text = decode_best_effort(data)

    # trova indice del label ARTICOLO in una riga intestazione
    art_label_idx = None
    for line in iter_balanced_lines(text):
        f = extract_quoted_fields(line)
        if not f:
            continue
        for i, v in enumerate(f):
            if v.strip().upper() == "ARTICOLO":
                art_label_idx = i
                break
        if art_label_idx is not None:
            break

    if art_label_idx is None:
        return pd.DataFrame()

    last_reparto = ""
    last_categoria = ""
    last_fornitore = ""

    out = []
    for line in iter_balanced_lines(text):
        f = extract_quoted_fields(line)
        if not f or len(f) <= art_label_idx + 3:
            continue
        if f[art_label_idx].strip().upper() != "ARTICOLO":
            continue

        pos = art_label_idx + 1

        # Caso A: reparto/categoria/fornitore presenti
        reparto = last_reparto
        categoria = last_categoria
        fornitore = last_fornitore

        pos_article = None

        if len(f) > pos + 4 and _looks_like_reparto(f[pos]) and _looks_like_reparto(f[pos+1]) and _looks_like_supplier(f[pos+2]):
            reparto = f[pos].strip()
            categoria = f[pos+1].strip()
            fornitore = f[pos+2].strip()
            last_reparto, last_categoria, last_fornitore = reparto, categoria, fornitore
            # pos+3 è N
            pos_article = pos + 4
        else:
            # Caso B: N, articolo
            if len(f) > pos + 1 and f[pos].strip().isdigit() and _CODE_RE.match(f[pos+1].strip()):
                pos_article = pos + 1
            # Caso C: direttamente articolo (raro)
            elif _CODE_RE.match(f[pos].strip()):
                pos_article = pos

        if pos_article is None or pos_article >= len(f):
            continue

        art_full = f[pos_article].strip()
        if not art_full or art_full.upper().startswith("TOTALI"):
            continue

        parts = art_full.split()
        if not parts:
            continue
        code = parts[0].strip()
        if not _CODE_RE.match(code):
            continue
        descr = " ".join(parts[1:]).strip()

        # prendi i primi 5 numeri (ord, con, vend, ven, giac) dopo articolo
        nums = []
        j = pos_article + 1
        while j < len(f) and len(nums) < 9:  # prendiamo anche prezzi/valori se presenti
            val = parse_num_token(f[j])
            if val is not None:
                nums.append(val)
            j += 1

        if len(nums) < 5:
            continue

        consegnate = int(nums[1])
        vendute = int(nums[2])
        giacenza = int(nums[4])

        prz_acq = float(nums[5]) if len(nums) > 5 else None
        prz_vend = float(nums[6]) if len(nums) > 6 else None
        valore_netto = float(nums[8]) if len(nums) > 8 else None

        out.append({
            "reparto": reparto,
            "categoria": categoria,
            "fornitore": fornitore,
            "code": code,
            "product": descr if descr else art_full,
            "consegnate": consegnate,
            "vendute": vendute,
            "giacenza": giacenza,
            "prz_acq": prz_acq,
            "prz_vend": prz_vend,
            "valore_netto": valore_netto,
        })

    return pd.DataFrame(out)
