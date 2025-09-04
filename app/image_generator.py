import random
from urllib.parse import quote
import time

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

    # Add a timestamp to prevent caching issues
    timestamp = int(time.time())

    # CHANGED FROM 768x768 TO 550x550 FOR FASTER LOADING
    return f"{base}{quote(full_prompt)}?width=150&height=150&seed={seed}&nocache={timestamp}"