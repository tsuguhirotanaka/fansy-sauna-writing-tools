import streamlit as st
from utils.gemini_client import generate_stream, generate_illustration_prompt_from_image, generate_illustration_prompt_from_upload
from utils.url_fetcher import fetch_site_text, extract_image_urls
from utils.copy_button import render_copy_button
from utils.visit_context import get_visit_context
from utils.length_options import render_length_selector

PLATFORMS = {
    "X (Twitter)": {
        "icon": "𝕏",
        "rules": "140字以内、ハッシュタグ2〜3個、改行を効果的に使う",
    },
    "Instagram": {
        "icon": "📸",
        "rules": "絵文字を適度に使い、サウナ関連ハッシュタグを10〜20個含める",
    },
    "Instagramストーリー": {
        "icon": "📖",
        "rules": "縦型（9:16）フォーマット想定。①上部：インパクトのある短いキャッチコピー（15字以内）、②中部：本文（80字以内）、③下部：CTA（「タップして詳細を見る」など）の3パートで構成する。絵文字・ハッシュタグを含める。",
    },
    "Threads": {
        "icon": "🧵",
        "rules": "500字以内、会話的なトーンでシンプルに伝える",
    },
    "note": {
        "icon": "📝",
        "rules": "制限なし、導入〜本文〜まとめの構成で読ませる文章にする",
    },
}

IMG_STYLE_MAP = {
    "ぬくもりイラスト": "旅行ガイドのような温かみのあるデジタルイラスト",
    "クール・モダンイラスト": "デザイン誌のようなクールでミニマルなベクターイラスト",
    "水彩画風": "淡い色合いの夢幻的な水彩画スタイル",
    "アニメ・漫画風": "ジブリ風の情感あるアニメ背景イラスト",
}

IMG_ASPECT_MAP = {
    "正方形 (1:1)": "1:1",
    "縦長 (4:5)": "4:5",
    "ストーリー (9:16)": "9:16",
    "横長 (16:9)": "16:9",
}


def _build_text_prompt(site_info: str, memo: str, platforms: list[str], visit_context: str, length: int) -> str:
    memo_part = f"\n追加メモ・投稿したい内容: {memo}" if memo.strip() else ""
    platform_rules = "\n".join([f"- {p}: {PLATFORMS[p]['rules']}" for p in platforms])
    platform_list = "・".join(platforms)
    separator_note = "・".join([f"「--- {p} ---」" for p in platforms])
    return f"""あなたはサウナ専門のSNSライターです。以下の施設情報をもとに、指定のプラットフォームに最適化したSNS投稿文を作成してください。

【施設サイトから取得した情報】
{site_info}
{memo_part}

【書き手の訪問経験】
{visit_context}

【生成するプラットフォーム】
{platform_list}

【各プラットフォームの条件】
{platform_rules}
（X・Instagram・Threadsは各プラットフォームの文字数制限を守ること。noteは目標文字数約{length}字を目安にすること。）

施設の雰囲気・特徴と訪問経験の深さを活かして、サウナ好きが思わず反応したくなる投稿文にしてください。
各プラットフォームを {separator_note} のように区切って出力してください。"""




def render():
    st.caption("使用するSNSを選んで、施設サイトのURLを入力してください。")

    url = st.text_input("施設サイトURL", placeholder="https://example-sauna.com")
    visits = st.number_input("この施設に行った回数", min_value=1, value=1, step=1)
    length = render_length_selector("sns")
    memo = st.text_area("メモ（任意）", placeholder="例：ととのい報告、施設紹介、イベント告知など投稿したい内容・シーン", height=100)

    st.write("投稿するSNSを選択")
    cols = st.columns(len(PLATFORMS))
    selected = []
    for i, (name, info) in enumerate(PLATFORMS.items()):
        with cols[i]:
            if st.checkbox(f"{info['icon']} {name}", value=False, key=f"sns_toggle_{name}"):
                selected.append(name)

    disabled = not url.strip() or len(selected) == 0
    if st.button("投稿文を生成", type="primary", disabled=disabled):
        with st.spinner("サイトを読み込み中..."):
            try:
                site_info = fetch_site_text(url.strip())
            except Exception as e:
                st.error(f"URLの取得に失敗しました: {e}")
                return
        st.session_state["sns_site_info"] = site_info
        with st.spinner("投稿文を生成中..."):
            result = st.write_stream(generate_stream(_build_text_prompt(site_info, memo, selected, get_visit_context(visits), length)))
        st.session_state["sauna_sns_result"] = result

    if "sauna_sns_result" in st.session_state:
        render_copy_button(st.session_state["sauna_sns_result"])
        st.download_button(
            "投稿文をダウンロード (.txt)",
            data=st.session_state["sauna_sns_result"],
            file_name="sauna_sns_posts.txt",
            mime="text/plain",
        )

    # イラストプロンプト生成セクション
    st.divider()
    st.subheader("🎨 施設写真からイラストプロンプトを生成（任意）")
    st.caption("サイトに掲載されている写真を選び、そのままイラストに変換するプロンプトを生成します。Adobe Firefly・Canva AI などに貼り付けて使えます。")

    col1, col2 = st.columns(2)
    with col1:
        img_style = st.selectbox("イラストスタイル", list(IMG_STYLE_MAP.keys()), key="img_style")
        st.caption(IMG_STYLE_MAP[img_style])
    with col2:
        img_aspect_label = st.selectbox("サイズ", list(IMG_ASPECT_MAP.keys()), key="img_aspect")

    if st.button("📷 施設の写真を読み込む", disabled=not url.strip()):
        with st.spinner("写真を探しています..."):
            try:
                imgs = extract_image_urls(url.strip())
                st.session_state["site_images"] = imgs
                st.session_state.pop("sns_img_prompt", None)
            except Exception as e:
                st.error(f"写真の読み込みに失敗しました: {e}")

    if "site_images" in st.session_state:
        imgs = st.session_state["site_images"]
        if not imgs:
            st.warning("このページからは写真を自動取得できませんでした（ボット対策がかかっているサイトは取得できません）。下から写真を直接アップロードしてください。")
        else:
            st.write(f"{len(imgs)} 枚の写真が見つかりました。イラストにしたい写真を選んでください。")
            cols = st.columns(3)
            for i, img_url in enumerate(imgs):
                with cols[i % 3]:
                    try:
                        st.image(img_url, use_container_width=True)
                        st.caption(f"写真 {i + 1}")
                    except Exception:
                        st.caption(f"写真 {i + 1}（表示失敗）")

            selected_idx = st.selectbox(
                "イラストにする写真を選択",
                range(len(imgs)),
                format_func=lambda i: f"写真 {i + 1}",
            )

            if st.button("選んだ写真からイラストプロンプトを生成", type="secondary"):
                with st.spinner("写真を分析してプロンプトを生成中..."):
                    try:
                        result = generate_illustration_prompt_from_image(
                            imgs[selected_idx], memo, img_style, img_aspect_label
                        )
                        st.session_state["sns_img_prompt"] = result
                    except Exception as e:
                        st.error(f"プロンプト生成に失敗しました: {e}")

    # 写真アップロード（自動取得できないサイト用）
    st.write("または")
    uploaded = st.file_uploader(
        "写真を直接アップロード",
        type=["jpg", "jpeg", "png", "webp"],
        key="img_upload",
    )
    if uploaded:
        st.image(uploaded, width=300)
        if st.button("アップロードした写真からイラストプロンプトを生成", type="secondary"):
            with st.spinner("写真を分析してプロンプトを生成中..."):
                try:
                    result = generate_illustration_prompt_from_upload(
                        uploaded.read(), uploaded.type,
                        memo, img_style, img_aspect_label,
                    )
                    st.session_state["sns_img_prompt"] = result
                except Exception as e:
                    st.error(f"プロンプト生成に失敗しました: {e}")

    if "sns_img_prompt" in st.session_state:
        prompts = st.session_state["sns_img_prompt"]
        if prompts.get("en"):
            st.caption("🇺🇸 英語プロンプト（Adobe Firefly・DALL-E・Midjourney用）")
            st.code(prompts["en"], language=None)
        if prompts.get("ja"):
            st.caption("🇯🇵 日本語プロンプト（Canva AI用）")
            st.code(prompts["ja"], language=None)
        st.info("💡 右上のコピーアイコンでコピー → **Adobe Firefly**（無料）または **Canva AI**（無料）に貼り付けてください。")
