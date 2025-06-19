import streamlit as st
from sqlalchemy import create_engine, text
import socket  # ✅ new import

st.set_page_config(page_title="Where2Run", layout="wide")
st.markdown("# 🏃‍♂️ Where2Run")
st.markdown("Use the sidebar to navigate to different features.")


