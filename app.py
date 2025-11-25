import streamlit as st
import streamlit_authenticator as stauth
from db import init_db

# ---------------------------
# 1. API Keys dari Secrets
# ---------------------------
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
OCR_API_KEY  = st.secrets["OCR_SPACE_API_KEY"]

# ---------------------------
# 2. Konfigurasi dasar app
# ---------------------------
init_db()
st.set_page_config(
    page_title="TIRTAFLOW",
    page_icon="💧",
    layout="wide",
)

# ---------------------------
# 3. Ambil konfigurasi AUTH dari secrets.toml
# ---------------------------

auth_cfg = st.secrets.get("auth", {})
creds_cfg = st.secrets.get("credentials", {})

# creds_cfg["users"] -> array of user objects
# kita konversi ke dict sesuai format Authenticate:
# {"usernames": {"admin": {"name":.., "password":..}, ...}}
user_dict = {}

for user in creds_cfg.get("users", []):
    uname = user["username"]

    # authenticator hanya butuh: name, password
    user_dict[uname] = {
        "name": user.get("name", uname),
        "password": user["password"],   # NOTE: sebaiknya HASH (untuk demo tak masalah)
        # meta tambahan untuk session_state
        "email": user.get("email"),
        "role": user.get("role", "STAFF"),
        "division": user.get("division", "Umum"),
    }

credentials_for_auth = {"usernames": user_dict}

# ---------------------------
# 4. Inisialisasi authenticator
# ---------------------------
authenticator = stauth.Authenticate(
    credentials_for_auth,
    auth_cfg.get("cookie_name", "tirtaflow_auth"),
    auth_cfg.get("cookie_key", "tirtaflow_cookie"),
    auth_cfg.get("cookie_expiry_days", 3),
)

# ---------------------------
# 5. Render LOGIN FORM
# ---------------------------
try:
    authenticator.login(
        location="sidebar",
        fields={
            "Form name": "Login Tirtaflow",
            "Username": "Username",
            "Password": "Password",
            "Login": "Masuk",
        },
        # HAPUS key= karena versi 0.3.2 tidak mendukung
    )
except Exception as e:
    st.error(f"Error autentikasi: {e}")

# Authentication state
auth_status = st.session_state.get("authentication_status", None)
session_username = st.session_state.get("username", None)
session_name     = st.session_state.get("name", None)

# ---------------------------
# 6. Setelah LOGIN berhasil
# ---------------------------
if auth_status:

    me = user_dict.get(session_username, {})

    st.session_state["username"]     = session_username
    st.session_state["display_name"] = me.get("name", session_name or session_username)
    st.session_state["role"]         = me.get("role", "STAFF")
    st.session_state["division"]     = me.get("division", "Umum")

    # Sidebar identity
    st.sidebar.success(f"Halo, {st.session_state['display_name']}")
    st.sidebar.caption(
        f"Role: **{st.session_state['role']}** · Divisi: **{st.session_state['division']}**"
    )

    authenticator.logout("Logout", "sidebar")

    # -----------------
    # Halaman utama
    # -----------------
    st.title("💧 TIRTAFLOW — Sistem Surat & Disposisi")
    st.caption("Sistem Surat Masuk & Disposisi PDAM Tirtamarta")

    st.markdown("""
    ### Selamat datang di Tirtaflow

    Silakan gunakan menu di **sidebar** untuk:
    - 📥 **Upload Surat** – unggah surat → OCR → analisa AI (Groq)
    - 📊 **Dashboard Surat** – daftar surat sesuai role/divisi
    - 📄 **Detail Surat** – lihat 1 surat, download CSV, disposisi via WhatsApp

    ---
    """)

# ---------------------------
# 7. Username/password salah
# ---------------------------
elif auth_status is False:
    st.error("❌ Username atau password salah. Silakan coba lagi.")

# ---------------------------
# 8. Belum login
# ---------------------------
else:
    st.info("Silakan login melalui form di sidebar untuk mengakses Tirtaflow.")
    st.stop()
