# utils/ocr.py

import requests

def ocr_space_file(
    file_path: str,
    api_key: str,
    language: str = "eng",
    timeout: int = 30,
) -> str:
    """
    Panggil OCR.Space untuk melakukan OCR pada file di file_path.
    Timeout default 30 detik. Kalau gagal / timeout, akan raise RuntimeError.
    """
    url = "https://api.ocr.space/parse/image"

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
    except requests.exceptions.Timeout as e:
        raise RuntimeError("OCR timeout (melewati 30 detik).") from e
    except Exception as e:
        raise RuntimeError(f"OCR request error: {e}") from e

    data = res.json()

    if data.get("IsErroredOnProcessing"):
        msg = "; ".join(data.get("ErrorMessage") or [])
        raise RuntimeError(f"OCR error: {msg}")

    results = data.get("ParsedResults") or []
    text = "\n".join([r.get("ParsedText", "") for r in results])
    return text.strip()
