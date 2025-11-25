import streamlit as st
import streamlit_authenticator as stauth
from db import init_db

# -------------------------------------------------
# 1. PAGE CONFIG — HARUS JADI STREAMLIT COMMAND PERTAMA
# -------------------------------------------------
st.set_page_config(
    page_title="TIRTAFLOW",
    page_icon="💧",
    layout="wide",
)

# -------------------------------------------------
# 2. INIT DB
# -------------------------------------------------
init_db()

# -------------------------------------------------
# 3. AMBIL KONFIGURASI AUTH DARI SECRETS
# -------------------------------------------------
# Struktur di secrets.toml:
# [auth]
# cookie_name = "tirtaflow_auth"
# cookie_key = "tirtaflow_cookie_secret"
# cookie_expiry_days = 3
#
# [credentials]
# users = [
#   {username="admin", name="IT Admin", email="admin@pdam.id", password="password", role="IT_ADMIN", division="Umum"},
#   ...
# ]

auth_cfg = st.secrets.get("auth", {})
creds_cfg = st.secrets.get("credentials", {})

user_dict = {}
for user in creds_cfg.get("users", []):
    uname = user["username"]
    user_dict[uname] = {
        "name":     user.get("name", uname),
        "password": user["password"],   # idealnya sudah HASH di produksi
        "email":    user.get("email"),
        "role":     user.get("role", "STAFF"),
        "division": user.get("division", "Umum"),
    }

credentials_for_auth = {"usernames": user_dict}

if not credentials_for_auth["usernames"]:
    st.error(
        "Tidak ada user yang terkonfigurasi.\n\n"
        "Pastikan blok `[credentials]` dan `users = [...]` sudah diisi di **Edit secrets**."
    )
    st.stop()

# -------------------------------------------------
# 4. INISIALISASI AUTHENTICATOR
# -------------------------------------------------
authenticator = stauth.Authenticate(
    credentials_for_auth,
    auth_cfg.get("cookie_name", "tirtaflow_auth"),
    auth_cfg.get("cookie_key", "tirtaflow_cookie"),
    auth_cfg.get("cookie_expiry_days", 3),
)

# -------------------------------------------------
# 5. FORM LOGIN DI SIDEBAR
# -------------------------------------------------
try:
    authenticator.login(
        location="sidebar",
        fields={
            "Form name": "Login Tirtaflow",
            "Username": "Username",
            "Password": "Password",
            "Login": "Masuk",
        },
        # jangan pakai key= karena v0.3.2 belum support
    )
except Exception as e:
    st.error(f"Error autentikasi: {e}")
    st.stop()

auth_status      = st.session_state.get("authentication_status", None)
session_username = st.session_state.get("username", None)
session_name     = st.session_state.get("name", None)

# -------------------------------------------------
# 6. LOGIKA SETELAH LOGIN
# -------------------------------------------------
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
    - 📄 **Detail Surat** – lihat 1 surat, download file asli & riwayat disposisi

    ---
    """)

elif auth_status is False:
    st.error("❌ Username atau password salah. Silakan coba lagi.")

else:
    st.info("Silakan login melalui form di sidebar untuk mengakses Tirtaflow.")
    st.stop()
