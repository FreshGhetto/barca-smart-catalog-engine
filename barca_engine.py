import io
import zipfile
from typing import List

from barca_layout import draw_card
from barca_image_fetcher import fetch_image_for_code


def generate_catalog_zip(items: List, folder_name: str = "BARCA") -> bytes:
    zip_buffer = io.BytesIO()
    missing = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for rank, item in enumerate(items, start=1):

            code = getattr(item, "code", "")
            product = getattr(item, "product", "")
            supplier = getattr(item, "fornitore", None) or getattr(item, "supplier", None) or ""
            consegnate = getattr(item, "consegnate", 0)
            vendute = getattr(item, "vendute", 0)
            giacenza = getattr(item, "giacenza", 0)
            tacco_mm = getattr(item, "tacco_mm", None)

            perc_vendita = None
            if consegnate and consegnate > 0:
                perc_vendita = (vendute / consegnate) * 100

            image_bytes, image_err = fetch_image_for_code(code)
            if not image_bytes:
                missing.append(f"{code}\t{image_err or 'missing'}")

            card_bytes = draw_card(
                code=code,
                product=product,
                supplier=supplier,
                perc_vendita=perc_vendita,
                consegnate=consegnate,
                vendute=vendute,
                giacenza=giacenza,
                tacco_mm=tacco_mm,
                rank=rank,
                image_bytes=image_bytes,
                image_err=image_err,
            )

            safe_code = code.replace("/", "_")
            filename = f"{rank:03d}_{safe_code}.jpg"

            z.writestr(f"{folder_name}/cards/{filename}", card_bytes)

            if image_bytes:
                z.writestr(f"{folder_name}/_raw/{filename}", image_bytes)

        if missing:
            z.writestr(f"{folder_name}/_missing_report.txt", "\n".join(missing))

    zip_buffer.seek(0)
    return zip_buffer.getvalue()
