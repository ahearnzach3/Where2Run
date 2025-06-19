import streamlit as st
from sqlalchemy import create_engine, text
import socket  # ✅ new import

st.set_page_config(page_title="Where2Run", layout="wide")
st.markdown("# 🏃‍♂️ Where2Run")
st.markdown("Use the sidebar to navigate to different features.")

st.title("🔌 Supabase Connection Test")

try:
    # 🌐 Force IPv4 resolution
    ipv4_host = socket.gethostbyname(st.secrets["DB_HOST"])

    db_url = f"postgresql+psycopg2://{st.secrets['DB_USER']}:{st.secrets['DB_PASSWORD']}@" \
             f"{ipv4_host}:{st.secrets['DB_PORT']}/{st.secrets['DB_NAME']}"

    engine = create_engine(db_url, connect_args={"sslmode": "require"})

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        st.success("✅ Connected to Supabase PostgreSQL!")
        st.code(f"PostgreSQL version: {version}")

except Exception as e:
    st.error("❌ Connection failed!")
    st.exception(e)
