
from dataclasses import dataclass
from typing import Optional

@dataclass
class CatalogItem:
    code: str
    product: str
    supplier: str
    consegnate: int
    vendute: int
    giacenza: int
    perc_vendita: float
    tacco_mm: Optional[float] = None
