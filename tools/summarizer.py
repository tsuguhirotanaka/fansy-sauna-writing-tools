import streamlit as st
from utils.gemini_client import generate_stream

STYLE_MAP = {
    "箇条書き": "箇条書き（・）で重要ポイントをリストアップ",
    "段落文章": "読みやすい段落形式の文章",
    "一文要約": "核心を突いた1〜2文の超短縮要約",
    "章立て": "見出しと説明を組み合わせた構造化された要約",
}

LENGTH_MAP = {
    "短め（3〜5ポイント/100字程度）": "簡潔に",
    "標準（5〜8ポイント/300字程度）": "バランス良く",
    "詳細（10ポイント以上/500字程度）": "詳細に",
}


def _build_prompt(text: str, style: str, length: str, focus: str) -> str:
    focus_part = f"\n特に注目すべきポイント: {focus}" if focus.strip() else ""
    return f"""以下のテキストを要約してください。

【要約スタイル】{STYLE_MAP[style]}
【詳細度】{LENGTH_MAP[length]}まとめる{focus_part}

【要約するテキスト】
{text}

日本語で要約してください。"""


def render():
    st.header("文章要約")
    st.caption("長い文章を入力すると、指定したスタイルで要約します。")

    text = st.text_area("要約したいテキスト", placeholder="ここに要約したい文章を貼り付けてください...", height=300)

    col1, col2, col3 = st.columns(3)
    with col1:
        style = st.selectbox("要約スタイル", list(STYLE_MAP.keys()))
    with col2:
        length = st.selectbox("詳細度", list(LENGTH_MAP.keys()), index=1)
    with col3:
        focus = st.text_input("注目ポイント（任意）", placeholder="例：コスト、リスク、結論")

    char_count = len(text)
    if char_count > 0:
        st.caption(f"入力文字数: {char_count:,}字")

    if st.button("要約する", type="primary", disabled=not text.strip()):
        prompt = _build_prompt(text, style, length, focus)
        with st.spinner("要約中..."):
            result = st.write_stream(generate_stream(prompt))
        st.session_state["summary_result"] = result

    if "summary_result" in st.session_state:
        st.download_button(
            "要約をダウンロード (.txt)",
            data=st.session_state["summary_result"],
            file_name="summary.txt",
            mime="text/plain",
        )
