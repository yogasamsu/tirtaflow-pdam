import requests
import streamlit as st
from PIL import Image
import io

# ==========================
#  Kompres file jika >1MB
# ==========================
MAX_SIZE = 1024 * 1024  # 1MB

file_bytes = uploaded_file.getvalue()

# Jika bukan PDF, compress gambar
if uploaded_file.type in ["image/jpeg", "image/png"]:
    if len(file_bytes) > MAX_SIZE:

        st.info("📉 File besar, melakukan kompres sebelum OCR…")

        img = Image.open(io.BytesIO(file_bytes))
        img = img.convert("RGB")

        # Resize kalau resolusi besar
        max_dim = 1500
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim))

        # Kompresi kualitas JPEG bertahap
        quality = 85
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        
        # Turunkan kualitas sampai <1MB (minimal 30)
        while buffer.tell() > MAX_SIZE and quality > 30:
            quality -= 10
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality)

        compressed_bytes = buffer.getvalue()

        st.success(f"📦 Ukuran setelah kompres: {len(compressed_bytes)/1024:.1f} KB")

        # simpan ke file yg akan dikirim ke OCR
        temp_path = letters_dir / f"compressed_{unique_filename}.jpg"
        with open(temp_path, "wb") as f:
            f.write(compressed_bytes)

        ocr_input_path = str(temp_path)

    else:
        # gambar sudah kecil, safe
        ocr_input_path = str(save_path)

else:
    # PDF atau file lain → langsung
    ocr_input_path = str(save_path)


def ocr_space_file(file_path: str, api_key: str, language: str="eng", timeout: int=90) -> str:
    url = "https://api.ocr.space/parse/image"

    for attempt in range(3):  # coba 3x
        try:
            with open(file_path, "rb") as f:
                res = requests.post(
                    url,
                    files={"file": f},
                    data={
                        "language": language,
                        "isTable": False,
                        "scale": True,
                        "OCREngine": 2
                    },
                    headers={"apikey": api_key},
                    timeout=timeout
                )
            break
        except requests.exceptions.Timeout:
            if attempt < 2:
                time.sleep(2)
                continue
            else:
                raise RuntimeError("OCR timeout setelah 3x percobaan.")

    data = res.json()

    if data.get("IsErroredOnProcessing"):
        msg = "; ".join(data.get("ErrorMessage") or [])
        raise RuntimeError(f"OCR error: {msg}")

    results = data.get("ParsedResults") or []
    text = "\n".join([r.get("ParsedText", "") for r in results])
    return text.strip()
