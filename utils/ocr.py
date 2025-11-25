import requests
import streamlit as st

def ocr_space_file(file_path: str, api_key: str, language: str="eng", timeout: int=30) -> str:
    url = "https://api.ocr.space/parse/image"
    with open(file_path, "rb") as f:
        res = requests.post(
            url,
            files={"filename": f},
            data={
                "language": language,
                "isTable": False,
                "scale": True,
                "OCREngine": 2
            },
            headers={"apikey": api_key},
            timeout=timeout
        )
    data = res.json()
    if data.get("IsErroredOnProcessing"):
        msg = "; ".join(data.get("ErrorMessage") or [])
        raise RuntimeError(f"OCR error: {msg} | payload={data}")
    results = data.get("ParsedResults") or []
    text = "\n".join([r.get("ParsedText","") for r in results])
    return text.strip()
