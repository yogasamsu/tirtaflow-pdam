import os
import json
from typing import Dict
from groq import Groq
import streamlit as st

ALLOWED_DIVISI = [
    "Operasi", "Hubungan Pelanggan", "Finance",
    "Hukum", "IT", "SDM", "Umum"
]

SYSTEM_PROMPT = f"""
Anda staf Bagian Umum berpengalaman. Baca teks OCR, simpulkan ringkas untuk disposisi.

Hasilkan JSON dengan key:
- nomor_surat_pengirim (string atau null)
- maksud_surat (string)
- rekomendasi_divisi (SATU dari: {", ".join(ALLOWED_DIVISI)})

Larangan:
- jangan isi nomor telepon/meeting ID sebagai nomor surat.
- jangan tambah key lain di luar 3 key tersebut.
"""


def build_prompt(teks: str) -> str:
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


def analyse_text_with_groq(teks: str) -> Dict:
    # 🔑 AMBIL API KEY DARI secrets / environment
    groq_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise RuntimeError("GROQ_API_KEY belum diset di secrets atau environment.")

    model_name = (
        st.secrets.get("GROQ_MODEL")
        or os.getenv("GROQ_MODEL")
        or "llama-3.1-8b-instant"
    )

    # 🔑 CLIENT GROQ — versi stabil tanpa proxies
    client = Groq(api_key=groq_key)

    # =========================================
    #  PANGGIL GROQ CHAT COMPLETION
    # =========================================
    resp = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(teks)}
        ],
        temperature=0.2,
        max_tokens=300
    )

    raw = (resp.choices[0].message.content or "").strip()

    # =========================================
    #  PARSE JSON (robust)
    # =========================================
    try:
        data = json.loads(raw)
    except Exception:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e != -1 and e > s:
            data = json.loads(raw[s:e+1])
        else:
            raise RuntimeError("Balasan AI tidak berbentuk JSON valid.")

    nomor = data.get("nomor_surat_pengirim") or None
    maksud = data.get("maksud_surat") or "Tidak dapat dianalisis otomatis"
    rekom = data.get("rekomendasi_divisi")

    if rekom not in ALLOWED_DIVISI:
        rekom = "Umum"

    return {
        "nomor_surat_pengirim": nomor,
        "maksud_surat": maksud,
        "rekomendasi_divisi": rekom,
    }
