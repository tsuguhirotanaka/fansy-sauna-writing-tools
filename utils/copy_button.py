import streamlit as st


def render_copy_button(text: str):
    with st.expander("📋 コピー用テキスト"):
        st.code(text, language=None)
