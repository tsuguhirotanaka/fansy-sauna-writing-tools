import streamlit as st
from utils.gemini_client import generate_stream

STYLE_MAP = {
    "キャッチー・インパクト重視": "読者の興味を引く、インパクトのあるキャッチーなタイトル",
    "SEO重視・検索向け": "検索に引っかかりやすいSEOを意識したタイトル",
    "情報提供・分かりやすさ重視": "内容が一目で分かる、情報提供型のタイトル",
    "疑問形・問題提起型": "読者に問いかける疑問形や問題提起型のタイトル",
    "数字・リスト型": "「〇選」「〇つの方法」など数字を使ったタイトル",
}


def _build_prompt(content: str, style: str, count: int, platform: str) -> str:
    platform_part = f"\n掲載媒体: {platform}" if platform.strip() else ""
    return f"""プロのコピーライターとして、以下の内容に合うタイトルを{count}個提案してください。

【タイトルスタイル】{STYLE_MAP[style]}{platform_part}

【コンテンツの内容・テーマ】
{content}

タイトル候補を番号付きリストで出力し、各タイトルに一言コメントも添えてください。"""


def render():
    st.header("タイトル・見出し生成")
    st.caption("コンテンツの概要を入力すると、複数のタイトル候補を生成します。")

    content = st.text_area(
        "コンテンツの概要・テーマ",
        placeholder="例：Pythonで機械学習を始める方法についての入門記事。初心者向けに環境構築からモデル作成まで解説する。",
        height=120,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        style = st.selectbox("タイトルスタイル", list(STYLE_MAP.keys()))
    with col2:
        count = st.slider("提案数", min_value=3, max_value=10, value=5)
    with col3:
        platform = st.text_input("掲載媒体（任意）", placeholder="例：はてなブログ、note、Qiita")

    if st.button("タイトルを生成", type="primary", disabled=not content.strip()):
        prompt = _build_prompt(content, style, count, platform)
        with st.spinner("タイトルを生成中..."):
            st.write_stream(generate_stream(prompt))
