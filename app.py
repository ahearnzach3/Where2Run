import streamlit as st
import psycopg2

st.set_page_config(page_title="Where2Run", layout="wide")
st.markdown("# 🏃‍♂️ Where2Run")
st.markdown("Use the sidebar to navigate to different features.")


st.title("🔌 Supabase Connection Test")

try:
    conn = psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=st.secrets["DB_PORT"],
        sslmode="require",
        connect_timeout=10
    )

    st.success("✅ Connected to Supabase PostgreSQL!")

    # Optional: run a simple query
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    st.code(f"PostgreSQL version: {version}")
    cur.close()
    conn.close()

except Exception as e:
    st.error("❌ Connection failed!")
    st.exception(e)
