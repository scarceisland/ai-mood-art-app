import random
from urllib.parse import quote

STYLE = {
    "happiness": "bright sunny vibrant, soft bokeh, golden hour, joyful, flowers, cinematic",
    "sadness": "muted cool tones, rainy window, gentle light, reflective, soft focus",
    "anger": "high contrast, red accents, stormy sky, intense dramatic lighting",
    "disgust": "desaturated greenish palette, gritty texture, abstract expression",
    "fear": "moody low light, fog, long shadows, suspenseful, chiaroscuro",
    "surprise": "sparkles, confetti burst, bright contrast, playful whimsical",
}

def build_image_url(prompt: str, emotion: str) -> str:
    seed = random.randint(0, 10_000_000)
    full_prompt = f"{emotion} mood, {STYLE[emotion]}. Visual metaphor for: {prompt}"
    base = "https://image.pollinations.ai/prompt/"
    return f"{base}{quote(full_prompt)}?width=768&height=768&seed={seed}"
