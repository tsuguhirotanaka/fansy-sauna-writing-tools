import streamlit as st
from utils.gemini_client import generate_stream

LEVEL_MAP = {
    "軽微（誤字・脱字のみ）": "誤字・脱字・句読点の修正のみ行い、文体は極力変えない",
    "標準（読みやすさ向上）": "誤字脱字を修正し、読みやすさと流れを改善する",
    "大幅改善（内容・構成も）": "誤字脱字・文体・構成・表現を全面的に改善し、より質の高い文章にする",
}


def _build_prompt(text: str, level: str, purpose: str) -> str:
    purpose_part = f"\n文章の用途: {purpose}" if purpose.strip() else ""
    return f"""あなたはプロの編集者・校正者です。以下の文章を校正・改善してください。

【改善レベル】{LEVEL_MAP[level]}{purpose_part}

【元の文章】
{text}

以下の形式で出力してください：

## 改善後の文章
（校正・改善した文章をここに）

## 修正・改善のポイント
（主な変更点を箇条書きで説明）"""


def render():
    st.header("文章校正・改善")
    st.caption("文章を入力すると、誤字脱字の修正や表現の改善を行います。")

    text = st.text_area("校正したいテキスト", placeholder="ここに校正・改善したい文章を入力してください...", height=250)

    col1, col2 = st.columns(2)
    with col1:
        level = st.selectbox("改善レベル", list(LEVEL_MAP.keys()), index=1)
    with col2:
        purpose = st.text_input("文章の用途（任意）", placeholder="例：ビジネスメール、SNS投稿、ブログ記事")

    if st.button("校正・改善する", type="primary", disabled=not text.strip()):
        prompt = _build_prompt(text, level, purpose)
        with st.spinner("校正・改善中..."):
            result = st.write_stream(generate_stream(prompt))
        st.session_state["proof_result"] = result

    if "proof_result" in st.session_state:
        st.download_button(
            "結果をダウンロード (.txt)",
            data=st.session_state["proof_result"],
            file_name="proofread_result.txt",
            mime="text/plain",
        )
