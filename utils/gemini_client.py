import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-2.5-flash-lite"
IMAGE_MODEL_NAME = "imagen-4.0-generate-001"


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません。.env ファイルを確認してください。")
    return genai.Client(api_key=api_key)


def generate_stream(prompt: str):
    client = _get_client()
    for chunk in client.models.generate_content_stream(model=MODEL_NAME, contents=prompt):
        if chunk.text:
            yield chunk.text


def generate(prompt: str) -> str:
    client = _get_client()
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text


def generate_image(prompt: str, aspect_ratio: str = "1:1") -> bytes:
    client = _get_client()
    response = client.models.generate_images(
        model=IMAGE_MODEL_NAME,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio,
        ),
    )
    return response.generated_images[0].image.image_bytes


def _build_illustration_prompt_response(img_bytes: bytes, mime: str, memo: str, illust_style: str, aspect_ratio: str) -> dict:
    style_guidance = {
        "ぬくもりイラスト": "warm and cozy digital illustration, soft colors, gentle lighting, like a travel guidebook illustration",
        "クール・モダンイラスト": "cool modern vector illustration, clean lines, minimalist design, like a design magazine",
        "水彩画風": "delicate watercolor painting, soft color washes, artistic brushwork, dreamy atmosphere",
        "アニメ・漫画風": "anime-style illustration, vibrant colors, detailed background art, Studio Ghibli-inspired",
    }
    memo_part = f"\n追加情報: {memo}" if memo.strip() else ""
    prompt = f"""この写真はサウナ施設の実際の写真です。
この写真の構図・空間・素材・照明・雰囲気を忠実に読み取り、{illust_style}スタイルのイラストに変換するための画像生成プロンプトを作成してください。
{memo_part}
アスペクト比: {aspect_ratio}
スタイル詳細: {style_guidance[illust_style]}

【出力形式】区切り文字を必ず使い、プロンプト本文だけを出力してください。

===ENGLISH===
（写真の構図・空間・素材・照明を詳細に描写した英語プロンプト。イラストスタイル指定を含める。人物なし・テキストなし。）
===JAPANESE===
（同内容の日本語版。）"""
    client = _get_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type=mime),
            types.Part(text=prompt),
        ],
    )
    raw = response.text
    en, ja = "", ""
    if "===ENGLISH===" in raw and "===JAPANESE===" in raw:
        en = raw.split("===ENGLISH===")[1].split("===JAPANESE===")[0].strip()
        ja = raw.split("===JAPANESE===")[1].strip()
    else:
        en = raw.strip()
    return {"en": en, "ja": ja}


def generate_illustration_prompt_from_upload(img_bytes: bytes, mime: str, memo: str, illust_style: str, aspect_ratio: str) -> dict:
    return _build_illustration_prompt_response(img_bytes, mime, memo, illust_style, aspect_ratio)


def generate_illustration_prompt_from_image(image_url: str, memo: str, illust_style: str, aspect_ratio: str) -> dict:
    import requests as req
    from utils.url_fetcher import _validate_url
    _validate_url(image_url)
    img_resp = req.get(image_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    img_resp.raise_for_status()
    img_bytes = img_resp.content
    mime = img_resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    if mime not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
        mime = "image/jpeg"
    return _build_illustration_prompt_response(img_bytes, mime, memo, illust_style, aspect_ratio)


def generate_image_prompt(site_info: str, memo: str, illust_style: str, aspect_ratio: str) -> dict:
    style_guidance = {
        "ぬくもりイラスト": "warm and cozy digital illustration, soft colors, gentle lighting, inviting atmosphere, like a travel guidebook illustration",
        "クール・モダンイラスト": "cool modern vector illustration, clean lines, minimalist design, sleek and stylish, like a design magazine spread",
        "水彩画風": "delicate watercolor painting style, soft washes of color, artistic brushwork, dreamy and atmospheric",
        "アニメ・漫画風": "anime-style illustration, vibrant colors, detailed background art, Studio Ghibli-inspired atmosphere",
    }
    memo_part = f"\n追加情報: {memo}" if memo.strip() else ""
    raw = generate(f"""あなたはサウナ施設のイラストレーターです。
以下の施設情報を読み込み、その施設の雰囲気・特徴・世界観をイラストで表現するための画像生成プロンプトを作成してください。

【施設サイトから取得した情報】
{site_info[:1000]}
{memo_part}

イラストスタイル: {illust_style}（{style_guidance[illust_style]}）
アスペクト比: {aspect_ratio}

【出力形式】以下の区切り文字を必ず使い、プロンプト本文だけを出力してください。説明文・ラベル・記号は不要です。

===ENGLISH===
（Adobe Firefly・DALL-E・Midjourney用の英語プロンプト本文のみ。イラストスタイル指定を含める。人物なし・テキストなし。）
===JAPANESE===
（Canva AI用の日本語プロンプト本文のみ。同内容の日本語版。）""")

    en, ja = "", ""
    if "===ENGLISH===" in raw and "===JAPANESE===" in raw:
        en = raw.split("===ENGLISH===")[1].split("===JAPANESE===")[0].strip()
        ja = raw.split("===JAPANESE===")[1].strip()
    else:
        en = raw.strip()
    return {"en": en, "ja": ja}

