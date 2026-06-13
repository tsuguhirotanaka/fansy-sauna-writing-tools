import streamlit as st
from utils.gemini_client import generate_stream
from utils.url_fetcher import fetch_site_text
from utils.visit_context import get_visit_context
from utils.length_options import render_length_selector
from utils.copy_button import render_copy_button


def _build_prompt(site_info: str, memo: str, visit_context: str, length: int) -> str:
    memo_part = f"\n追加メモ・体験の詳細: {memo}" if memo.strip() else ""
    return f"""あなたはサウナ体験の達人ライターです。以下の施設情報をもとに、臨場感あふれるととのい体験記事を執筆してください。

【施設サイトから取得した情報】
{site_info}
{memo_part}

【書き手の訪問経験】
{visit_context}

目標文字数: 約{length}字

施設の特徴（景色・水風呂・サウナ室など）と訪問経験を活かして、読んだ人がその場にいるような臨場感と、ととのいの感覚を追体験できる文章にしてください。
マークダウン形式で出力してください。"""


def render():
    st.header("ととのい体験記事")
    st.caption("施設サイトのURLを入力すると、臨場感あふれる体験記事を生成します。")

    url = st.text_input("施設サイトURL", placeholder="https://example-sauna.com")
    visits = st.number_input("この施設に行った回数", min_value=1, value=1, step=1)
    length = render_length_selector("totonou")
    memo = st.text_area("メモ（任意）", placeholder="例：夕暮れの外気浴、水風呂は16度、星が綺麗だった、など体験のメモ", height=100)

    if st.button("体験記事を生成", type="primary", disabled=not url.strip()):
        with st.spinner("サイトを読み込み中..."):
            try:
                site_info = fetch_site_text(url.strip())
            except Exception as e:
                st.error(f"URLの取得に失敗しました: {e}")
                return
        with st.spinner("体験記事を生成中..."):
            result = st.write_stream(generate_stream(_build_prompt(site_info, memo, get_visit_context(visits), length)))
        st.session_state["totonou_result"] = result

    if "totonou_result" in st.session_state:
        render_copy_button(st.session_state["totonou_result"])
        st.download_button(
            "記事をダウンロード (.md)",
            data=st.session_state["totonou_result"],
            file_name="totonou_article.md",
            mime="text/markdown",
        )
