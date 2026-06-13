import streamlit as st

LENGTH_MAP = {
    "短め": 400,
    "標準": 900,
    "長め": 1800,
}


def render_length_selector(key: str, default: str = "標準") -> int:
    label = st.radio(
        "文字数",
        list(LENGTH_MAP.keys()),
        index=list(LENGTH_MAP.keys()).index(default),
        horizontal=True,
        key=f"length_{key}",
    )
    return LENGTH_MAP[label]
