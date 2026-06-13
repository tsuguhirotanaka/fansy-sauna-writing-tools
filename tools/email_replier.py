import streamlit as st
from utils.gemini_client import generate_stream

TONE_MAP = {
    "丁寧・敬語": "丁寧で敬語を使ったビジネスメールのトーン",
    "フレンドリー": "親しみやすいフレンドリーなトーン",
    "簡潔・ビジネスライク": "簡潔でビジネスライクなトーン",
    "お詫び・謝罪": "誠実にお詫びするトーン",
}


def _build_prompt(original: str, intent: str, tone: str, sender_name: str, my_name: str) -> str:
    sender_part = f"差出人名: {sender_name}\n" if sender_name.strip() else ""
    my_name_part = f"自分の名前: {my_name}\n" if my_name.strip() else ""
    return f"""あなたはビジネスメールのプロライターです。以下の元メールへの返信文を作成してください。

【元のメール】
{original}

【返信の意図・ポイント】
{intent}

{sender_part}{my_name_part}文体: {TONE_MAP[tone]}

件名と本文を含む完全な返信メールを作成してください。"""


def render():
    st.header("メール返信文生成")
    st.caption("元のメールを貼り付けると、適切な返信文を生成します。")

    original = st.text_area("元のメール本文", placeholder="ここに返信したいメールの内容を貼り付けてください...", height=200)

    col1, col2 = st.columns(2)
    with col1:
        intent = st.text_area("返信の意図・要点", placeholder="例：承諾する、日程を別日に変更したい、追加情報を求める", height=100)
        tone = st.selectbox("文体・トーン", list(TONE_MAP.keys()))
    with col2:
        sender_name = st.text_input("差出人名（任意）", placeholder="例：田中様")
        my_name = st.text_input("自分の名前（任意）", placeholder="例：山田太郎")

    if st.button("返信文を生成", type="primary", disabled=not (original.strip() and intent.strip())):
        prompt = _build_prompt(original, intent, tone, sender_name, my_name)
        with st.spinner("返信文を生成中..."):
            result = st.write_stream(generate_stream(prompt))
        st.session_state["email_result"] = result

    if "email_result" in st.session_state:
        st.download_button(
            "返信文をダウンロード (.txt)",
            data=st.session_state["email_result"],
            file_name="email_reply.txt",
            mime="text/plain",
        )
