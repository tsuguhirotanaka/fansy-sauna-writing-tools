import streamlit as st
from utils.gemini_client import generate_stream
from utils.url_fetcher import fetch_site_text
from utils.visit_context import get_visit_context
from utils.length_options import render_length_selector
from utils.copy_button import render_copy_button


def _build_prompt(site_info: str, memo: str, visit_context: str, length: int) -> str:
    memo_part = f"\n追加メモ: {memo}" if memo.strip() else ""
    return f"""あなたはサウナ施設のコピーライターです。以下の施設情報をもとに、世界観のある施設紹介文を執筆してください。

【施設サイトから取得した情報】
{site_info}
{memo_part}

【書き手の訪問経験】
{visit_context}

目標文字数: 約{length}字

【構成】
- 施設の世界観を伝えるキャッチコピー（1〜2文）
- 施設の特徴・こだわりを伝える本文
- 訪問を促すクロージング文

サイトの雰囲気やコンセプトと、書き手の訪問経験を活かした文体・トーンで執筆してください。
マークダウン形式で出力してください。"""


def render():
    st.header("施設紹介文生成")
    st.caption("施設サイトのURLを入力すると、世界観のある紹介文を生成します。")

    url = st.text_input("施設サイトURL", placeholder="https://example-sauna.com")
    visits = st.number_input("この施設に行った回数", min_value=1, value=1, step=1)
    length = render_length_selector("facility")
    memo = st.text_area("メモ（任意）", placeholder="例：外気浴が絶景、水風呂は地下水使用、など補足したい情報", height=100)

    if st.button("紹介文を生成", type="primary", disabled=not url.strip()):
        with st.spinner("サイトを読み込み中..."):
            try:
                site_info = fetch_site_text(url.strip())
            except Exception as e:
                st.error(f"URLの取得に失敗しました: {e}")
                return
        with st.spinner("紹介文を生成中..."):
            result = st.write_stream(generate_stream(_build_prompt(site_info, memo, get_visit_context(visits), length)))
        st.session_state["facility_result"] = result

    if "facility_result" in st.session_state:
        render_copy_button(st.session_state["facility_result"])
        st.download_button(
            "紹介文をダウンロード (.md)",
            data=st.session_state["facility_result"],
            file_name="facility_description.md",
            mime="text/markdown",
        )
