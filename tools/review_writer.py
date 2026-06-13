import streamlit as st
from utils.gemini_client import generate_stream
from utils.url_fetcher import fetch_site_text
from utils.visit_context import get_visit_context
from utils.length_options import render_length_selector
from utils.copy_button import render_copy_button

POINT_LABELS = {
    "sauna_room": "サウナ室",
    "cold_bath": "水風呂",
    "totonou_space": "ととのいスペース",
    "staff": "スタッフ・接客",
    "cost": "コスパ",
    "atmosphere": "雰囲気・内装",
}


def _build_prompt(site_info: str, ratings: dict, overall: int, memo: str, visit_context: str, length: int) -> str:
    ratings_text = "\n".join(
        [f"- {POINT_LABELS[k]}: {'★' * v}{'☆' * (5 - v)} ({v}/5)" for k, v in ratings.items()]
    )
    memo_part = f"\n追加メモ: {memo}" if memo.strip() else ""
    return f"""あなたはサウナ愛好家です。以下の情報をもとに、リアルで参考になるサウナ施設レビューを執筆してください。

【施設サイトから取得した情報】
{site_info}

【書き手の訪問経験】
{visit_context}

総合評価: {'★' * overall}{'☆' * (5 - overall)} ({overall}/5)

【各項目評価】
{ratings_text}
{memo_part}

目標文字数: 約{length}字

訪問経験の深さを反映しながら、実際に訪れた人の視点で具体的でリアルなレビューを書いてください。良い点・改善点をバランスよく含め、次に行く人の参考になる内容にしてください。"""


def render():
    st.header("サウナレビュー生成")
    st.caption("施設サイトのURLと評価を入力すると、リアルで参考になるレビュー文を生成します。")

    url = st.text_input("施設サイトURL", placeholder="https://example-sauna.com")
    visits = st.number_input("この施設に行った回数", min_value=1, value=1, step=1)
    length = render_length_selector("review")

    st.subheader("各項目の評価")
    cols = st.columns(3)
    ratings = {}
    for i, (key, label) in enumerate(POINT_LABELS.items()):
        with cols[i % 3]:
            ratings[key] = st.slider(label, 1, 5, 4)

    overall = st.slider("総合評価", 1, 5, 4)
    memo = st.text_area("メモ（任意）", placeholder="例：水風呂が深くて最高、混んでいた、など補足したい情報", height=80)

    if st.button("レビューを生成", type="primary", disabled=not url.strip()):
        with st.spinner("サイトを読み込み中..."):
            try:
                site_info = fetch_site_text(url.strip())
            except Exception as e:
                st.error(f"URLの取得に失敗しました: {e}")
                return
        with st.spinner("レビューを生成中..."):
            result = st.write_stream(generate_stream(_build_prompt(site_info, ratings, overall, memo, get_visit_context(visits), length)))
        st.session_state["review_result"] = result

    if "review_result" in st.session_state:
        render_copy_button(st.session_state["review_result"])
        st.download_button(
            "レビューをダウンロード (.txt)",
            data=st.session_state["review_result"],
            file_name="sauna_review.txt",
            mime="text/plain",
        )
