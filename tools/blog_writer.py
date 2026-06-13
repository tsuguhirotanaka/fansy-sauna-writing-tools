import streamlit as st
from utils.gemini_client import generate_stream

TONE_MAP = {
    "カジュアル": "親しみやすくカジュアルなトーン",
    "フォーマル": "丁寧でフォーマルなトーン",
    "プロフェッショナル": "専門的でプロフェッショナルなトーン",
    "エンタメ系": "楽しくエンターテインメント性の高いトーン",
}

LENGTH_MAP = {
    "短め（500〜800字）": 650,
    "標準（1000〜1500字）": 1200,
    "長め（2000〜3000字）": 2500,
}


def _build_prompt(topic: str, keywords: str, tone: str, audience: str, length: int) -> str:
    kw_part = f"キーワード: {keywords}\n" if keywords.strip() else ""
    audience_part = f"ターゲット読者: {audience}\n" if audience.strip() else ""
    return f"""あなたはプロのブログライターです。以下の条件でブログ記事を執筆してください。

テーマ: {topic}
{kw_part}{audience_part}文体: {TONE_MAP[tone]}
目標文字数: 約{length}字

【記事の構成】
- 読者を引き込む導入部
- 見出し（H2/H3）を使った本文（複数セクション）
- まとめ・行動を促すクロージング

マークダウン形式で出力してください。"""


def render():
    st.header("ブログ記事執筆")
    st.caption("テーマや条件を入力すると、構成付きのブログ記事を生成します。")

    col1, col2 = st.columns([2, 1])
    with col1:
        topic = st.text_area("テーマ・タイトル", placeholder="例：初心者向けPythonの始め方", height=80)
        keywords = st.text_input("キーワード（任意）", placeholder="例：Python, プログラミング, 入門")
        audience = st.text_input("ターゲット読者（任意）", placeholder="例：プログラミング初心者、20〜30代")
    with col2:
        tone = st.selectbox("文体・トーン", list(TONE_MAP.keys()))
        length_label = st.selectbox("記事の長さ", list(LENGTH_MAP.keys()), index=1)

    if st.button("記事を生成", type="primary", disabled=not topic.strip()):
        prompt = _build_prompt(topic, keywords, tone, audience, LENGTH_MAP[length_label])
        with st.spinner("記事を生成中..."):
            result = st.write_stream(generate_stream(prompt))
        st.session_state["blog_result"] = result

    if "blog_result" in st.session_state:
        st.download_button(
            "記事をダウンロード (.md)",
            data=st.session_state["blog_result"],
            file_name="blog_article.md",
            mime="text/markdown",
        )
