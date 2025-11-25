import streamlit as st
import streamlit_authenticator as stauth
from db import init_db

# ---------------------------
# Konfigurasi dasar app
# ---------------------------

# Inisialisasi database
init_db()
st.set_page_config(
    page_title="TIRTAFLOW",
    page_icon="💧",
    layout="wide",
)

# ---------------------------
# Ambil konfigurasi dari secrets.toml
# ---------------------------
auth_cfg = st.secrets.get("auth", {})
creds = st.secrets.get("credentials", {})

# Kita expect di secrets.toml:
# [credentials]
# users = [
#   {username="admin", name="IT Admin", email="admin@pdam.id", password="password", role="IT_ADMIN", division="Umum"},
#   ...
# ]

# Bentuk dict sesuai format streamlit-authenticator:
# {"usernames": {"admin": {...}, "umum": {...}, ...}}
user_dict = {}
for u in creds.get("users", []):
    username = u["username"]
    user_dict[username] = {
        "email": u.get("email", ""),
        # library terbaru pakai first_name / last_name, tapi "name" juga boleh
        "first_name": u.get("name", username),
        "last_name": "",
        "name": u.get("name", username),
        "password": u["password"],   # NOTE: untuk produksi sebaiknya sudah di-hash
        # field tambahan (custom) untuk role & division
        "role": u.get("role", "STAFF"),
        "division": u.get("division", "Umum"),
        # field internal yang nanti akan di-manage otomatis, tapi kita isi awal
        "failed_login_attempts": 0,
        "logged_in": False,
    }

credentials_for_auth = {"usernames": user_dict}

# ---------------------------
# Buat authenticator object
# ---------------------------
authenticator = stauth.Authenticate(
    credentials_for_auth,
    auth_cfg.get("cookie_name", "tirtaflow_auth"),
    auth_cfg.get("cookie_key", "secret"),
    auth_cfg.get("cookie_expiry_days", 3),
)

# ---------------------------
# Render login widget di sidebar (VERSI BARU)
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
        key="tirtaflow-login",
    )
except Exception as e:
    st.error(f"Error autentikasi: {e}")

auth_status = st.session_state.get("authentication_status", None)
session_name = st.session_state.get("name", None)
session_username = st.session_state.get("username", None)

# ---------------------------
# Logika setelah login
# ---------------------------

if auth_status:
    # Ambil profil user dari user_dict (berdasarkan username)
    me = user_dict.get(session_username or "", {})

    # Simpan ke session_state supaya bisa dipakai di pages/*
    st.session_state["username"] = session_username
    st.session_state["display_name"] = me.get("name", session_name or session_username)
    st.session_state["role"] = me.get("role", "STAFF")
    st.session_state["division"] = me.get("division", "Umum")

    # Sidebar info + logout
    st.sidebar.success(f"Halo, {st.session_state['display_name']}")
    st.sidebar.caption(
        f"Role: **{st.session_state['role']}** · Divisi: **{st.session_state['division']}**"
    )
    authenticator.logout("Logout", "sidebar", key="tirtaflow-logout")

    # Halaman utama
    st.title("💧 TIRTAFLOW — Sistem Surat & Disposisi")
    st.caption("Sistem Surat Masuk & Disposisi PDAM Tirtamarta (demo internal)")

    st.markdown(
        """
        ### Selamat datang di Tirtaflow

        Silakan gunakan menu di **sidebar** untuk:
        - 📥 *Upload Surat*: unggah surat baru → OCR otomatis → analisa AI (Groq).
        - 📊 *Dashboard*: melihat daftar surat (otomatis difilter berdasarkan role/divisi).
        - 📄 *Detail Surat*: lihat 1 surat, unduh CSV, dan kirim disposisi via WhatsApp.

        ---
        """
    )

elif auth_status is False:
    # Username/password salah
    st.error("❌ Username atau password salah. Silakan coba lagi.")

else:
    # Belum submit / belum login
    st.info("Silakan login melalui form di sidebar untuk mengakses Tirtaflow.")
    # Penting: stop supaya pages/* tidak dieksekusi tanpa login
    st.stop()
