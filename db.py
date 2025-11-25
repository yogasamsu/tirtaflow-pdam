import os
import sqlite3
from datetime import datetime

DB_PATH = "data/tirtaflow.db"


# -------------------------------------------------
# 1. INIT DB
# -------------------------------------------------
def init_db():
    """Buat folder data + tabel SQLite kalau belum ada."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tabel surat masuk
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomor_internal TEXT,
            uploader TEXT,
            division TEXT,
            status TEXT,
            ai_nomor_pengirim TEXT,
            ai_maksud TEXT,
            ai_rekomendasi TEXT,
            timestamp TEXT,
            filename TEXT,
            ocr_text TEXT
        )
        """
    )

    # Tabel disposisi surat
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS dispositions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letter_id INTEGER NOT NULL,
            from_role TEXT,
            from_division TEXT,
            to_role TEXT,
            to_division TEXT,
            note TEXT,
            created_by TEXT,
            created_at TEXT,
            FOREIGN KEY(letter_id) REFERENCES letters(id)
        )
        """
    )

    conn.commit()
    conn.close()


# -------------------------------------------------
# 2. INSERT SURAT
# -------------------------------------------------
def insert_letter(
    nomor_internal=None,
    uploader=None,
    division=None,
    status=None,
    ai_nomor_pengirim=None,
    ai_maksud=None,
    ai_rekomendasi=None,
    timestamp=None,
    filename=None,
    ocr_text=None,
    file_path=None,   # <--- supaya kompatibel dengan pemanggilan lama
):
    """
    Simpan 1 surat ke tabel letters.

    - nomor_internal: boleh None -> dibuat otomatis YYYY/MM/NNN
    - timestamp: boleh None -> pakai waktu sekarang
    - filename:
        - kalau None tapi file_path ada -> otomatis pakai nama file dari file_path
    - return: (letter_id, nomor_internal)
    """
    import os  # pastikan ada di atas file juga boleh

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # waktu sekarang
    if not timestamp:
        now = datetime.now()
        timestamp = now.isoformat(timespec="seconds")
    else:
        try:
            now = datetime.fromisoformat(timestamp)
        except Exception:
            now = datetime.now()

    # kalau filename belum diisi tapi kita dapat file_path
    if not filename and file_path:
        filename = os.path.basename(file_path)

    # auto-generate nomor_internal kalau belum ada
    if not nomor_internal:
        year = now.year
        month = now.month
        prefix = f"{year}-{month:02d}"
        c.execute(
            "SELECT COUNT(*) FROM letters WHERE substr(timestamp, 1, 7) = ?",
            (prefix,),
        )
        seq = c.fetchone()[0] + 1
        nomor_internal = f"{year}/{month:02d}/{seq:03d}"

    c.execute(
        """
        INSERT INTO letters (
            nomor_internal,
            uploader,
            division,
            status,
            ai_nomor_pengirim,
            ai_maksud,
            ai_rekomendasi,
            timestamp,
            filename,
            ocr_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nomor_internal,
            uploader,
            division,
            status,
            ai_nomor_pengirim,
            ai_maksud,
            ai_rekomendasi,
            timestamp,
            filename,
            ocr_text,
        ),
    )

    letter_id = c.lastrowid
    conn.commit()
    conn.close()

    return letter_id, nomor_internal
# -------------------------------------------------
# 3. INSERT DISPOSISI
# -------------------------------------------------
def add_disposition(
    letter_id: int,
    from_role: str,
    from_division: str,
    to_role: str,
    to_division: str,
    note: str,
    created_by: str,
):
    """Simpan satu record disposisi ke tabel dispositions."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO dispositions (
            letter_id,
            from_role,
            from_division,
            to_role,
            to_division,
            note,
            created_by,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            letter_id,
            from_role,
            from_division,
            to_role,
            to_division,
            note,
            created_by,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    conn.commit()
    conn.close()

def get_letter_by_id(letter_id: int):
    """Ambil satu surat berdasarkan ID dari tabel letters."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM letters WHERE id = ?", (letter_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_dispositions_for_letter(letter_id: int):
    """Ambil seluruh riwayat disposisi untuk satu surat."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """
        SELECT *
        FROM dispositions
        WHERE letter_id = ?
        ORDER BY created_at ASC
        """,
        (letter_id,),
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
