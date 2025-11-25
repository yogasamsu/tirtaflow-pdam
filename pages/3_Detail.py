# pages/3_Detail.py

import os
import streamlit as st
from db import get_letter_by_id, get_dispositions_for_letter, DB_PATH

# ─────────────────────────────────────────────
# 0. Cek login
# ─────────────────────────────────────────────
if st.session_state.get("authentication_status") is not True:
    st.warning("Silakan login di halaman utama.")
    st.stop()

st.set_page_config(page_title="Detail Surat", layout="wide")
st.markdown("## 📄 Detail Surat & Disposisi")


# ─────────────────────────────────────────────
# 1. Input ID Surat
# ─────────────────────────────────────────────
col_id1, col_id2 = st.columns([3, 1])
with col_id1:
    input_id = st.number_input(
        "Masukkan ID Surat",
        min_value=1,
        step=1,
        value=st.session_state.get("detail_letter_id", 1),
    )
with col_id2:
    if st.button("Bersihkan pilihan ID"):
        st.session_state.pop("detail_letter_id", None)
        st.rerun()

# tombol tampilkan
if st.button("Tampilkan"):
    st.session_state["detail_letter_id"] = int(input_id)

letter_id = st.session_state.get("detail_letter_id")

if not letter_id:
    st.info("Masukkan ID surat lalu klik **Tampilkan**.")
    st.stop()

# ─────────────────────────────────────────────
# 2. Ambil data surat dari database
# ─────────────────────────────────────────────
letter = get_letter_by_id(letter_id)

if not letter:
    st.error(f"❌ Tidak ditemukan surat dengan ID {letter_id}.")
    st.stop()

# ─────────────────────────────────────────────
# 3. Layout utama: Info Surat + File + OCR
# ─────────────────────────────────────────────
left, right = st.columns([3, 2])

with left:
    st.markdown(f"### 🧾 Info Surat ID {letter_id}")

    st.write("**Nomor Internal**:", letter.get("nomor_internal") or "-")
    st.write("**Uploader**:", letter.get("uploader") or "-")
    st.write("**Divisi Upload**:", letter.get("division") or "-")
    st.write("**Status Teknis**:", letter.get("status") or "-")
    st.write("**Waktu Masuk**:", letter.get("timestamp") or "-")

    st.markdown("#### 🤖 Hasil Analisa AI")
    st.write("**Nomor Surat Pengirim (AI)**:", letter.get("ai_nomor_pengirim") or "-")
    st.write("**Maksud / Inti Surat (AI)**:", letter.get("ai_maksud") or "-")
    st.write("**Rekomendasi Divisi (AI)**:", letter.get("ai_rekomendasi") or "-")


with right:
    st.markdown("### ⬇️ File Asli & Isi OCR")

    UPLOAD_DIR = "data/letters"
    filename = letter.get("filename")

    # --- download file asli ---
    if filename:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            st.download_button(
                "⬇️ Unduh File Asli",
                data=file_bytes,
                file_name=filename,
                mime="application/octet-stream",
            )
        else:
            st.error(f"⚠️ File asli tidak ditemukan di server:\n`{file_path}`")
    else:
        st.info("Belum ada informasi nama file tersimpan untuk surat ini.")

    # ────────── OCR Result ──────────
    st.markdown("#### 📜 Isi OCR")
    ocr_text = letter.get("ocr_text") or "(Belum ada OCR tersimpan)"
    st.text_area("Teks OCR", value=ocr_text, height=300, label_visibility="collapsed")


# ─────────────────────────────────────────────
# 4. Riwayat Disposisi
# ─────────────────────────────────────────────
st.markdown("### 📨 Riwayat Disposisi")

history = get_dispositions_for_letter(letter_id)

if not history:
    st.info("Belum ada disposisi. Surat masih di Bagian Umum / uploader.")
else:
    for d in history:
        st.markdown(
            f"""
- **{d.get('created_at','-')}**  
  Dari **{d.get('from_role','-')} ({d.get('from_division','-')})**  
  → **{d.get('to_role','-')} ({d.get('to_division','-')})**  
  Oleh **{d.get('created_by','-')}**  
  _Catatan_: {d.get('note','-')}
"""
        )
