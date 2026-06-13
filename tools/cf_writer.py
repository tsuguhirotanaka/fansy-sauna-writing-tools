import streamlit as st
from utils.gemini_client import generate_stream
from utils.url_fetcher import fetch_site_text
from utils.visit_context import get_visit_context
from utils.length_options import render_length_selector
from utils.copy_button import render_copy_button


def _build_prompt(site_info: str, memo: str, visit_context: str, length: int) -> str:
    memo_part = f"\n追加メモ: {memo}" if memo.strip() else ""
    return f"""あなたはクラウドファンディングのプロライターです。以下の施設情報をもとに、支援を集めるためのクラウドファンディングページ用の本文を執筆してください。

【施設サイトから取得した情報】
{site_info}
{memo_part}

【書き手の訪問経験】
{visit_context}

目標文字数: 約{length}字

【構成】
- 読者を引き込むプロジェクトの概要
- 想い・背景ストーリー
- 施設の特徴・こだわり
- 支援のお願い・クロージング

訪問経験から生まれたリアルな魅力と熱量を込めて、読者が「支援したい」と思える文章にしてください。
マークダウン形式で出力してください。"""


def render():
    st.caption("施設サイトのURLを入力すると、支援を集めるためのCF文章を生成します。")

    url = st.text_input("施設サイトURL", placeholder="https://example-sauna.com")
    visits = st.number_input("この施設に行った回数", min_value=1, value=1, step=1)
    length = render_length_selector("cf")
    memo = st.text_area("メモ（任意）", placeholder="例：目標金額100万円、リターン内容（¥10,000→優先予約権）、ターゲット支援者など", height=100)

    if st.button("CF文を生成", type="primary", disabled=not url.strip()):
        with st.spinner("サイトを読み込み中..."):
            try:
                site_info = fetch_site_text(url.strip())
            except Exception as e:
                st.error(f"URLの取得に失敗しました: {e}")
                return
        with st.spinner("CF文を生成中..."):
            result = st.write_stream(generate_stream(_build_prompt(site_info, memo, get_visit_context(visits), length)))
        st.session_state["cf_result"] = result

    if "cf_result" in st.session_state:
        render_copy_button(st.session_state["cf_result"])
        st.download_button(
            "CF文をダウンロード (.md)",
            data=st.session_state["cf_result"],
            file_name="crowdfunding_text.md",
            mime="text/markdown",
        )
