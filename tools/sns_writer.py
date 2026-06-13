import streamlit as st
from utils.gemini_client import generate_stream

PLATFORM_MAP = {
    "X (Twitter)": {
        "limit": "140字以内",
        "note": "ハッシュタグは2〜3個、改行を効果的に使う",
    },
    "Instagram": {
        "limit": "2200字以内",
        "note": "絵文字を適度に使い、ハッシュタグは10〜20個",
    },
    "LinkedIn": {
        "limit": "1300字以内",
        "note": "プロフェッショナルなトーンで、ビジネス価値を強調する",
    },
    "Facebook": {
        "limit": "制限なし",
        "note": "エンゲージメントを促す質問や呼びかけを含める",
    },
    "Threads": {
        "limit": "500字以内",
        "note": "会話的なトーンで、シンプルに伝える",
    },
}

TONE_MAP = {
    "カジュアル・親しみやすい": "親しみやすくカジュアルなトーン",
    "プロフェッショナル": "専門的でプロフェッショナルなトーン",
    "モチベーション・インスピレーション": "読む人を鼓舞するインスピレーショナルなトーン",
    "ユーモア・エンタメ": "ユーモアを交えたエンタメ的なトーン",
    "情報提供・教育的": "有益な情報を提供する教育的なトーン",
}


def _build_prompt(topic: str, platform: str, tone: str, hashtags: bool, count: int) -> str:
    p = PLATFORM_MAP[platform]
    hashtag_note = "関連するハッシュタグを含める" if hashtags else "ハッシュタグは含めない"
    return f"""SNSマーケティングのプロとして、以下の条件でSNS投稿文を{count}パターン作成してください。

プラットフォーム: {platform}
文字数制限: {p["limit"]}
注意点: {p["note"]}
文体: {TONE_MAP[tone]}
ハッシュタグ: {hashtag_note}

【投稿テーマ・内容】
{topic}

各パターンを「--- パターン1 ---」のように区切って出力してください。"""


def render():
    st.header("SNS投稿文生成")
    st.caption("テーマを入力すると、プラットフォームに最適化した投稿文を生成します。")

    topic = st.text_area(
        "投稿したい内容・テーマ",
        placeholder="例：新しいカフェをオープンしました。こだわりのスペシャルティコーヒーと手作りケーキが楽しめます。",
        height=120,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        platform = st.selectbox("プラットフォーム", list(PLATFORM_MAP.keys()))
    with col2:
        tone = st.selectbox("トーン", list(TONE_MAP.keys()))
    with col3:
        count = st.slider("生成パターン数", min_value=1, max_value=5, value=3)
    with col4:
        hashtags = st.checkbox("ハッシュタグを含める", value=True)

    p_info = PLATFORM_MAP[platform]
    st.info(f"**{platform}** — 文字数: {p_info['limit']} / {p_info['note']}")

    if st.button("投稿文を生成", type="primary", disabled=not topic.strip()):
        prompt = _build_prompt(topic, platform, tone, hashtags, count)
        with st.spinner("投稿文を生成中..."):
            st.write_stream(generate_stream(prompt))
