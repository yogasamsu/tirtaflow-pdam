# pages/2_Dashboard.py

import streamlit as st
import pandas as pd
import sqlite3

from db import add_disposition, DB_PATH  # kita pakai DB_PATH dari db.py biar konsisten

st.title("📊 Dashboard Surat")

# ─────────────────────────────
# 1. Cek user sudah login
# ─────────────────────────────
if st.session_state.get("authentication_status") is not True:
    st.warning("Silakan login di halaman utama.")
    st.stop()

role = st.session_state.get("role", "STAFF")
division = st.session_state.get("division", "Umum")
username = st.session_state.get("username", "unknown")

# ─────────────────────────────
# 2. Ambil data surat & disposisi dari SQLite
# ─────────────────────────────
# (kalau DB belum ada, sqlite akan bikin kosong; kita handle pakai cek df kosong)
conn = sqlite3.connect(DB_PATH)

df_letters = pd.read_sql_query("SELECT * FROM letters", conn)

try:
    df_disp = pd.read_sql_query("SELECT * FROM dispositions", conn)
except Exception:
    # kalau tabel dispositions belum pernah dibuat (harusnya sudah oleh init_db, tapi jaga-jaga)
    df_disp = pd.DataFrame()

conn.close()

if df_letters.empty:
    st.info("Belum ada surat di sistem. Silakan upload surat dulu di menu **Upload**.")
    st.stop()

# ─────────────────────────────
# 3. Gabungkan dengan assignment terakhir (disposisi terakhir)
# ─────────────────────────────
if df_disp.empty:
    df = df_letters.copy()
    df["assigned_role"] = None
    df["assigned_division"] = None
else:
    df_disp_latest = (
        df_disp.sort_values("created_at")
               .groupby("letter_id")
               .tail(1)[["letter_id", "to_role", "to_division"]]
               .rename(columns={"to_role": "assigned_role", "to_division": "assigned_division"})
    )

    df = df_letters.merge(
        df_disp_latest,
        left_on="id",
        right_on="letter_id",
        how="left",
    )

# ─────────────────────────────
# 4. Filter sesuai role/divisi login
#    - IT_ADMIN / BAGIAN_UMUM / DIREKTUR: lihat semua
#    - lainnya: hanya yang assigned_division = division masing-masing
# ─────────────────────────────
if role in ("IT_ADMIN", "BAGIAN_UMUM", "DIREKTUR"):
    filtered = df
else:
    # kalau kolom belum ada (misalnya belum ada disposisi sama sekali), paksa kolom kosong dulu
    if "assigned_division" not in df.columns:
        df["assigned_division"] = None
    filtered = df[df["assigned_division"] == division]

if filtered.empty:
    st.info("Tidak ada surat untuk role/divisi Anda saat ini.")
    st.stop()

# ─────────────────────────────
# 5. Tampilkan tabel utama
# ─────────────────────────────
expected_cols = [
    "id",
    "nomor_internal",
    "uploader",
    "division",
    "status",
    "ai_nomor_pengirim",
    "ai_maksud",
    "ai_rekomendasi",
    "assigned_role",
    "assigned_division",
    "timestamp",
    "filename",
]

available_cols = [c for c in expected_cols if c in filtered.columns]

if "id" in filtered.columns:
    filtered = filtered.sort_values("id", ascending=False)

st.dataframe(filtered[available_cols], use_container_width=True)

# =====================================================================
#  ⚡ FORM DISPOSISI CEPAT LANGSUNG DARI DASHBOARD
# =====================================================================
if role in ("BAGIAN_UMUM", "DIREKTUR") and not filtered.empty:

    st.subheader("⚡ Disposisi Cepat dari Dashboard")

    # direktur / umum boleh memilih dari semua surat
    source_df = df_letters.copy()

    def make_label(row):
        nomor = row["nomor_internal"] or f"ID {row['id']}"
        judul = row["ai_maksud"] or "(tanpa judul)"
        return f"{nomor} — {judul[:60]}"

    options = {
        int(r["id"]): make_label(r)
        for _, r in source_df.iterrows()
    }

    selected_id = st.selectbox(
        "Pilih surat yang akan didisposisikan:",
        options=list(options.keys()),
        format_func=lambda x: options[x],
    )

    # Tujuan disposisi — disesuaikan dengan nama divisi yang kita pakai
    tujuan_map = {
        "Kirim ke Direksi": ("DIREKTUR", "Direksi"),
        "Divisi Operasi": ("MANAGER", "Operasi"),
        "Divisi Hubungan Pelanggan": ("MANAGER", "Hubungan Pelanggan"),
        "Divisi Umum": ("BAGIAN_UMUM", "Umum"),
        "Divisi IT": ("STAFF", "IT"),
    }

    tujuan_label = st.selectbox(
        "Tujuan disposisi:",
        list(tujuan_map.keys()),
    )

    note = st.text_area(
        "Catatan untuk penerima (opsional):",
        value="",
        height=80,
    )

    if st.button("Kirimkan Disposisi"):
        to_role, to_div = tujuan_map[tujuan_label]

        add_disposition(
            letter_id=int(selected_id),
            from_role=role,
            from_division=division,
            to_role=to_role,
            to_division=to_div,
            note=note,
            created_by=username,
        )

        st.success(f"Disposisi tersimpan: Surat ID {selected_id} ⇒ {tujuan_label}")
        st.rerun()   # refresh supaya assigned_division di tabel ikut update

# ─────────────────────────────
# 6. Tombol download CSV
# ─────────────────────────────
st.download_button(
    "⬇️ Unduh CSV (Dashboard)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="surat_dashboard.csv",
    mime="text/csv",
)

st.caption(
    "Tabel di atas otomatis difilter sesuai **role** dan **divisi**. "
    "IT Admin / Bagian Umum / Direktur melihat semua; divisi lain hanya melihat yang sudah didisposisikan ke divisinya."
)
