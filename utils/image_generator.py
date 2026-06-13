import requests
from urllib.parse import quote

ASPECT_SIZE_MAP = {
    "1:1":  (1024, 1024),
    "4:5":  (1024, 1280),
    "9:16": (1024, 1820),
    "16:9": (1820, 1024),
}


def generate_image(prompt: str, aspect_ratio: str = "1:1") -> bytes:
    w, h = ASPECT_SIZE_MAP.get(aspect_ratio, (1024, 1024))
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width={w}&height={h}&nologo=true&enhance=true&model=flux"
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    return response.content
