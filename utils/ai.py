import os, json
from typing import Dict
from groq import Groq
import streamlit as st

ALLOWED_DIVISI = ["Operasi","Hubungan Pelanggan","Finance","Hukum","IT","SDM","Umum"]

SYSTEM_PROMPT = f"""
Anda staf Bagian Umum berpengalaman. Baca teks OCR, simpulkan ringkas untuk disposisi.
Hasilkan JSON dengan key:
- nomor_surat_pengirim (string atau null)
- maksud_surat (string)
- rekomendasi_divisi (SATU dari: {", ".join(ALLOWED_DIVISI)})
Larangan: jangan isi nomor telepon/meeting ID sebagai nomor surat. Jangan tambah key lain.
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
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    model = st.secrets.get("GROQ_MODEL") or os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant"
    client = Groq(api_key=api_key)

    # panggil
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content": SYSTEM_PROMPT},
            {"role":"user","content": build_prompt(teks)}
        ],
        temperature=0.2,
        max_tokens=300
    )
    raw = (resp.choices[0].message.content or "").strip()

    # parse ketat
    try:
        data = json.loads(raw)
    except Exception:
        s, e = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[s:e+1]) if s!=-1 and e!=-1 and e>s else {}

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
