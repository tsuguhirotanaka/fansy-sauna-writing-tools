import streamlit as st
from utils.gemini_client import generate_stream

LANGUAGES = [
    "日本語", "英語", "中国語（簡体字）", "中国語（繁体字）",
    "韓国語", "フランス語", "ドイツ語", "スペイン語",
    "ポルトガル語", "イタリア語", "ロシア語", "アラビア語",
]

STYLE_MAP = {
    "標準（自然な翻訳）": "自然で読みやすい標準的な翻訳",
    "直訳（原文に忠実）": "原文の構造に忠実な直訳",
    "意訳（ニュアンス優先）": "原文のニュアンスと意味を優先した意訳",
    "ビジネス文体": "ビジネスシーンに適したフォーマルな翻訳",
    "カジュアル文体": "日常会話に適したカジュアルな翻訳",
}


def _build_prompt(text: str, source_lang: str, target_lang: str, style: str, notes: str) -> str:
    notes_part = f"\n翻訳の注意事項: {notes}" if notes.strip() else ""
    auto_detect = source_lang == "自動検出"
    source_part = "元の言語は自動検出してください。" if auto_detect else f"元の言語: {source_lang}"
    return f"""プロの翻訳家として、以下のテキストを翻訳してください。

{source_part}
翻訳先の言語: {target_lang}
翻訳スタイル: {STYLE_MAP[style]}{notes_part}

【翻訳するテキスト】
{text}

翻訳結果のみを出力してください。説明や注釈は不要です。"""


def render():
    st.header("翻訳")
    st.caption("テキストを入力すると、指定した言語に翻訳します。")

    text = st.text_area("翻訳するテキスト", placeholder="ここに翻訳したいテキストを入力してください...", height=200)

    col1, col2, col3 = st.columns(3)
    with col1:
        source_lang = st.selectbox("元の言語", ["自動検出"] + LANGUAGES)
    with col2:
        target_lang = st.selectbox("翻訳先の言語", LANGUAGES, index=1)
    with col3:
        style = st.selectbox("翻訳スタイル", list(STYLE_MAP.keys()))

    notes = st.text_input("翻訳の注意事項（任意）", placeholder="例：固有名詞はそのまま残す、敬語を使う")

    char_count = len(text)
    if char_count > 0:
        st.caption(f"入力文字数: {char_count:,}字")

    if st.button("翻訳する", type="primary", disabled=not text.strip()):
        if source_lang != "自動検出" and source_lang == target_lang:
            st.warning("元の言語と翻訳先の言語が同じです。")
            return
        prompt = _build_prompt(text, source_lang, target_lang, style, notes)
        with st.spinner("翻訳中..."):
            result = st.write_stream(generate_stream(prompt))
        st.session_state["translate_result"] = result

    if "translate_result" in st.session_state:
        st.download_button(
            "翻訳結果をダウンロード (.txt)",
            data=st.session_state["translate_result"],
            file_name="translation.txt",
            mime="text/plain",
        )
