import streamlit as st
from datetime import datetime
from pathlib import Path
import time

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

# ambil identitas user dari session (diset di app.py)
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

    # 3.a Simpan file fisik ke folder data/letters dengan nama unik
    letters_dir = Path("data/letters")
    letters_dir.mkdir(parents=True, exist_ok=True)

    # nama unik: <timestamp>_<nama_asli>
    unique_filename = f"{int(time.time())}_{uploaded_file.name}"
    save_path = letters_dir / unique_filename

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # 3.b OCR
    st.info("🔍 OCR in progress…")
    try:
        ocr_text = ocr_space_file(
            str(save_path),
            api_key=st.secrets["OCR_SPACE_KEY"],
            language="eng",
        )
        st.success("OCR selesai.")
    except Exception as e:
        st.error(f"OCR gagal: {e}")
        ocr_text = ""

    # 3.c Analisa AI (Groq) – kalau OCR sukses
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

    # 3.d Generate nomor internal sistem
    nomor_internal = datetime.now().strftime("%Y/%m/") + f"{int(time.time()) % 1000:03d}"

    # 3.e Simpan ke database
    letter_id = insert_letter(
        nomor_internal=nomor_internal,
        uploader=username,
        division=division_user,
        filename=unique_filename,      # ⬅️ nama file persis seperti di folder data/letters
        ocr_text=ocr_text,
        ai_nomor_pengirim=ai_nomor,
        ai_maksud=ai_maksud,
        ai_rekomendasi=ai_rekom,
        status=status,
        timestamp=datetime.now().isoformat(timespec="seconds"),
    )

    # 3.f Feedback ke user
    st.success(f"Sukses simpan surat ID #{letter_id} — Nomor Internal: {nomor_internal}")
    st.link_button("Lihat Dashboard", "/2_Dashboard")
