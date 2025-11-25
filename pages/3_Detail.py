# pages/3_Detail.py

import os
import streamlit as st
from db import get_letter_by_id, get_dispositions_for_letter

st.set_page_config(page_title="Detail Surat", layout="wide")

st.markdown("## 📄 Detail Surat & Disposisi")

# --- input ID surat ---
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
        if "detail_letter_id" in st.session_state:
            del st.session_state["detail_letter_id"]
        st.rerun()

if st.button("Tampilkan"):
    st.session_state["detail_letter_id"] = int(input_id)

letter_id = st.session_state.get("detail_letter_id")

if not letter_id:
    st.info("Masukkan ID surat lalu klik **Tampilkan**.")
    st.stop()

# --- ambil data dari DB ---
letter = get_letter_by_id(letter_id)

if not letter:
    st.error(f"Tidak ditemukan surat dengan ID {letter_id}.")
    st.stop()

# --- layout 2 kolom: info & download ---
left, right = st.columns([3, 2])

with left:
    st.markdown(f"### 🧾 Info Surat ID {letter_id}")

    st.write("**Nomor Internal**:", letter.get("nomor_internal") or "-")
    st.write("**Uploader**:", letter.get("uploader") or "-")
    st.write("**Divisi Upload**:", letter.get("division") or "-")
    st.write("**Status Teknis**:", letter.get("status") or "-")
    st.write("**Waktu Masuk**:", letter.get("timestamp") or "-")

    st.markdown("#### 🔍 Hasil Analisa AI")
    st.write("**Nomor Surat Pengirim (AI)**:", letter.get("ai_nomor_pengirim") or "-")
    st.write("**Maksud / Inti Surat (AI)**:", letter.get("ai_maksud") or "-")
    st.write("**Rekomendasi Divisi (AI)**:", letter.get("ai_rekomendasi") or "-")

with right:
    st.markdown("### ⬇️ File Asli & Isi OCR")

    # --- tombol download file asli ---
    UPLOAD_DIR = "data/letters"  # GANTI kalau folder upload kamu beda
    filename = letter.get("filename")

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
            st.warning(f"File asli tidak ditemukan di server: `{file_path}`")
    else:
        st.info("Belum ada info nama file tersimpan untuk surat ini.")

    # --- tampilkan isi OCR ---
    st.markdown("#### 📜 Isi OCR")
    ocr_text = letter.get("ocr_text") or "(Belum ada OCR tersimpan)"
    st.text_area("Teks OCR", value=ocr_text, height=300, label_visibility="collapsed")

# --- riwayat disposisi ---
st.markdown("### 📨 Riwayat Disposisi")

history = get_dispositions_for_letter(letter_id)

if not history:
    st.info("Belum ada disposisi. Saat ini surat masih di Bagian Umum / uploader.")
else:
    for d in history:
        st.markdown(
            f"- **{d.get('created_at','-')}** · dari "
            f"**{d.get('from_role','-')} ({d.get('from_division','-')})** "
            f"→ **{d.get('to_role','-')} ({d.get('to_division','-')})** "
            f"oleh **{d.get('created_by','-')}**  \n"
            f"  _Catatan_: {d.get('note','-')}"
        )
