import os
import json
from typing import Dict
from groq import Groq
import streamlit as st

# Divisi yang diperbolehkan untuk rekomendasi
ALLOWED_DIVISI = ["Operasi", "Hubungan Pelanggan", "Finance", "Hukum", "IT", "SDM", "Umum"]

SYSTEM_PROMPT = f"""
Anda staf Bagian Umum berpengalaman. Baca teks OCR, simpulkan ringkas untuk disposisi.
Hasilkan JSON dengan key:
- nomor_surat_pengirim (string atau null)
- maksud_surat (string)
- rekomendasi_divisi (SATU dari: {", ".join(ALLOWED_DIVISI)})
Larangan: jangan isi nomor telepon/meeting ID sebagai nomor surat. Jangan tambah key lain.
"""

def build_prompt(teks: str) -> str:
    """Membangun prompt yang konsisten untuk model Groq."""
    return (
        'Contoh:\n'
        'OCR: "Nomor: 000.1.5/854 ... Hal: Undangan ... Selasa 12 Agustus 2025 13.00 WIB ..."\n'
        'Jawab:\n'
        '{\n'
        '  "nomor_surat_pengirim": "000.1.5/854",\n'
        '  "maksud_surat": "Undangan rapat koordinasi pada Selasa, 12 Agustus 2025 pukul 13.00 WIB secara daring.",\n'
        '  "rekomendasi_divisi": "Umum"\n'
        '}\n\n'
        f'Sekarang proses teks berikut, balas hanya JSON valid:\n"""{teks}"""'
    )

def _get_groq_api_key() -> str:
    """Ambil API key dari Streamlit secrets atau environment; error kalau tidak ada."""
    api_key = None

    # Prioritas: secrets Streamlit
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        # Kalau st.secrets tidak ada (misal bukan di Streamlit), skip
        api_key = None

    # Fallback: environment variable
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        # Pesan jelas kalau key belum diset
        msg = (
            "GROQ_API_KEY belum dikonfigurasi.\n\n"
            "- Tambahkan `GROQ_API_KEY` di **Edit secrets** Streamlit Cloud, atau\n"
            "- Set environment variable `GROQ_API_KEY` di lokal."
        )
        # Kalau dipanggil dari Streamlit, tampilkan error di UI
        try:
            st.error(msg)
        except Exception:
            pass
        raise RuntimeError("GROQ_API_KEY is missing")

    return api_key

@st.cache_resource
def _get_groq_client() -> Groq:
    """Client Groq yang di-cache agar tidak inisialisasi berulang."""
    api_key = _get_groq_api_key()
    return Groq(api_key=api_key)

def _get_groq_model() -> str:
    """Ambil nama model dari secrets/env, dengan default yang aman."""
    model = None
    try:
        model = st.secrets.get("GROQ_MODEL")
    except Exception:
        model = None

    if not model:
        model = os.getenv("GROQ_MODEL")

    # Default model
    if not model:
        model = "llama-3.1-8b-instant"

    return model

def analyse_text_with_groq(teks: str) -> Dict:
    """
    Analisa teks OCR dengan Groq, hasilkan dict:
    {
        "nomor_surat_pengirim": str | None,
        "maksud_surat": str,
        "rekomendasi_divisi": str (terbatas ALLOWED_DIVISI)
    }
    """
    teks = (teks or "").strip()
    if not teks:
        return {
            "nomor_surat_pengirim": None,
            "maksud_surat": "Teks OCR kosong, tidak dapat dianalisis.",
            "rekomendasi_divisi": "Umum",
        }

    client = _get_groq_client()
    model = _get_groq_model()

    # Panggil Groq
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(teks)},
        ],
        temperature=0.2,
        max_tokens=300,
        # Minta JSON object langsung (kalau model mendukung)
        response_format={"type": "json_object"},
    )

    raw = (resp.choices[0].message.content or "").strip()

    # Parsing JSON ketat dengan fallback
    data = {}
    try:
        data = json.loads(raw)
    except Exception:
        # Fallback: coba ekstrak substring pertama {...}
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e != -1 and e > s:
            try:
                data = json.loads(raw[s : e + 1])
            except Exception:
                data = {}
        else:
            data = {}

    nomor = data.get("nomor_surat_pengirim") or None
    maksud = data.get("maksud_surat") or "Tidak dapat dianalisis otomatis"
    rekom = data.get("rekomendasi_divisi")

    # Normalisasi rekomendasi divisi
    if rekom not in ALLOWED_DIVISI:
        rekom = "Umum"

    return {
        "nomor_surat_pengirim": nomor,
        "maksud_surat": maksud,
        "rekomendasi_divisi": rekom,
    }
