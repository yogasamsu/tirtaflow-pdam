import streamlit as st
from datetime import datetime
from pathlib import Path
import time
import io
from PIL import Image  # untuk kompres gambar

from db import insert_letter
from utils.ocr import ocr_space_file
from utils.ai import analyse_text_with_groq

st.title("📥 Upload Surat Masuk")

# ─────────────────────────────
# 1. Cek user sudah login atau belum
# ─────────────────────────────
if st.session_state.get("authentication_status") is not True:
    st.warning("Silakan login di halaman utama terlebih dahulu.")
    st.stop()

username = st.session_state.get("username", "unknown")
role = st.session_state.get("role", "STAFF")
division_user = st.session_state.get("division", "Umum")

# ─────────────────────────────
# 2. Form upload
# ─────────────────────────────
with st.form("upload_form"):
    penerima_nama = st.text_input("Nama Penerima (Bagian Umum / staf):", value="")
    uploaded_file = st.file_uploader(
        "File Surat (PDF/JPG/PNG)",
        type=["pdf", "jpg", "jpeg", "png"],
    )
    submitted = st.form_submit_button("Upload & Proses")

# ─────────────────────────────
# 3. Proses setelah submit
# ─────────────────────────────
if submitted:

    if not uploaded_file:
        st.error("Pilih file dulu sebelum klik *Upload & Proses*.")
        st.stop()

    # Simpan file fisik
    letters_dir = Path("data/letters")
    letters_dir.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{int(time.time())}_{uploaded_file.name}"
    save_path = letters_dir / unique_filename

    # baca bytes sekali saja
    file_bytes = uploaded_file.getvalue()

    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # ─────────────────────────────
    #  3.b OCR (dengan kompres gambar >1MB)
    # ─────────────────────────────
    st.info("🔍 OCR in progress…")

    OCR_API_KEY = st.secrets.get("OCR_SPACE_API_KEY")
    if not OCR_API_KEY:
        st.error("OCR_SPACE_API_KEY belum diset di secrets!")
        st.stop()

    MAX_SIZE = 1024 * 1024  # 1 MB

    # Tentukan path yang akan dikirim ke OCR
    if uploaded_file.type in ["image/jpeg", "image/jpg", "image/png"]:
        # Gambar → kompres jika perlu
        if len(file_bytes) > MAX_SIZE:
            st.info("📉 File besar, melakukan kompres sebelum OCR…")

            img = Image.open(io.BytesIO(file_bytes))
            img = img.convert("RGB")

            # Resize kalau resolusi sangat besar
            max_dim = 1500
            if max(img.size) > max_dim:
                img.thumbnail((max_dim, max_dim))

            quality = 85
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality)

            # Turunkan kualitas sampai <1MB atau minimal quality = 30
            while buffer.tell() > MAX_SIZE and quality > 30:
                quality -= 10
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=quality)

            compressed_bytes = buffer.getvalue()
            st.success(f"📦 Ukuran setelah kompres: {len(compressed_bytes)/1024:.1f} KB")

            # simpan file hasil kompres untuk OCR
            temp_path = letters_dir / f"compressed_{unique_filename}.jpg"
            with open(temp_path, "wb") as f:
                f.write(compressed_bytes)

            ocr_input_path = str(temp_path)
        else:
            # gambar sudah cukup kecil → pakai file asli
            ocr_input_path = str(save_path)
    else:
        # PDF atau tipe lain → langsung pakai file asli
        ocr_input_path = str(save_path)

    # Panggil OCR di sini
    try:
        ocr_text = ocr_space_file(
            ocr_input_path,
            api_key=OCR_API_KEY,
            language="eng",
        )
        st.success("OCR selesai.")
    except Exception as e:
        st.error(f"OCR gagal: {e}")
        st.caption("Anda masih bisa menyimpan surat ini. Detail OCR & AI dapat diisi manual nanti.")
        ocr_text = ""

    # ─────────────────────────────
    #  3.c AI Analysis
    # ─────────────────────────────
    ai_nomor = ai_maksud = ai_rekom = None
    status = "Pending"

    if ocr_text:
        st.info("🤖 Analisa AI (Groq)…")
        try:
            ai_result = analyse_text_with_groq(ocr_text)
            ai_nomor = ai_result.get("nomor_surat_pengirim")
            ai_maksud = ai_result.get("maksud_surat")
            ai_rekom = ai_result.get("rekomendasi_divisi")
            status = "Analisa Selesai"
            st.success("Analisa AI selesai.")
        except Exception as e:
            st.warning(f"Analisa AI gagal: {e}")
            status = "OCR Selesai"

    # ─────────────────────────────
    #  3.d Simpan ke database (nomor_internal auto-generated)
    # ─────────────────────────────
    letter_id, nomor_internal = insert_letter(
        nomor_internal=None,          # ➡️ gunakan auto-generate dari db.py
        uploader=username,
        division=division_user,
        filename=unique_filename,
        ocr_text=ocr_text,
        ai_nomor_pengirim=ai_nomor,
        ai_maksud=ai_maksud,
        ai_rekomendasi=ai_rekom,
        status=status,
        timestamp=datetime.now().isoformat(timespec="seconds"),
    )

    # ─────────────────────────────
    #  3.e Feedback
    # ─────────────────────────────
    st.success(f"Sukses simpan surat ID #{letter_id} — Nomor Internal: {nomor_internal}")
    st.link_button("Lihat Dashboard", "/2_Dashboard")
