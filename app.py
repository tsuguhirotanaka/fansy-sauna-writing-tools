import streamlit as st
from tools import facility_writer, totonou_writer, review_writer, sauna_sns_writer, cf_writer, newsletter_writer

st.set_page_config(
    page_title="FANSY SAUNA Writing Tools",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

TOOLS = {
    "施設紹介文生成": ("facility", facility_writer.render),
    "ととのい体験記事": ("totonou", totonou_writer.render),
    "サウナレビュー生成": ("review", review_writer.render),
    "SNS投稿文生成": ("sns", sauna_sns_writer.render),
    "クラウドファンディング文": ("cf", cf_writer.render),
    "メルマガ文生成": ("newsletter", newsletter_writer.render),
}

ICONS = {
    "施設紹介文生成": "🏠",
    "ととのい体験記事": "🌊",
    "サウナレビュー生成": "⭐",
    "SNS投稿文生成": "📱",
    "クラウドファンディング文": "💰",
    "メルマガ文生成": "📧",
}

with st.sidebar:
    st.title("🔥 FANSY SAUNA")
    st.caption("Writing Tools / Powered by Gemini")
    st.divider()

    selected_tool = st.radio(
        "ツールを選択",
        list(TOOLS.keys()),
        format_func=lambda x: f"{ICONS[x]}  {x}",
        label_visibility="collapsed",
    )

    st.divider()
    with st.expander("API設定"):
        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder=".env に設定するか、ここに入力",
        )
        if api_key_input:
            import os
            os.environ["GEMINI_API_KEY"] = api_key_input
            st.success("APIキーを設定しました")

st.markdown(
    f"<h2 style='margin-bottom:0'>{ICONS[selected_tool]} {selected_tool}</h2>",
    unsafe_allow_html=True,
)
st.divider()

try:
    _, render_fn = TOOLS[selected_tool]
    render_fn()
except ValueError as e:
    st.error(str(e))
    st.info("サイドバーの「API設定」からGemini APIキーを入力するか、プロジェクトルートに `.env` ファイルを作成して `GEMINI_API_KEY=your_key` を設定してください。")
except Exception as e:
    st.error(f"エラーが発生しました: {e}")
