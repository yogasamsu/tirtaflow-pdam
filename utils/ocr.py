# utils/ocr.py

import requests
import time


def ocr_space_file(
    file_path: str,
    api_key: str,
    language: str = "eng",
    timeout: int = 90,
) -> str:
    """
    Panggil OCR.Space untuk melakukan OCR pada file di file_path.
    Sudah dilengkapi retry 3x dan error handling dasar.
    """
    url = "https://api.ocr.space/parse/image"

    # Coba sampai 3x
    last_err = None
    for attempt in range(3):
        try:
            with open(file_path, "rb") as f:
                res = requests.post(
                    url,
                    files={"file": f},
                    data={
                        "language": language,
                        "isTable": False,
                        "scale": True,
                        "OCREngine": 2,
                    },
                    headers={"apikey": api_key},
                    timeout=timeout,
                )
            # kalau sukses request → keluar dari loop
            break
        except requests.exceptions.Timeout as e:
            last_err = e
            if attempt < 2:
                time.sleep(2)
                continue
            else:
                raise RuntimeError("OCR timeout setelah 3 percobaan.") from e
        except Exception as e:
            # error lain: langsung raise
            raise RuntimeError(f"OCR request error: {e}") from e

    data = res.json()

    if data.get("IsErroredOnProcessing"):
        msg = "; ".join(data.get("ErrorMessage") or [])
        raise RuntimeError(f"OCR error: {msg}")

    results = data.get("ParsedResults") or []
    text = "\n".join([r.get("ParsedText", "") for r in results])
    return text.strip()
