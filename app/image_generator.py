import os
import requests
import base64
from flask import current_app

CLIPDROP_API_KEY = os.getenv("CLIPDROP_API_KEY")
CLIPDROP_API_URL = "https://clipdrop-api.co/text-to-image/v1"

STYLE = {
    "happiness": "in a vibrant and joyful art style, with bright sunny colors and a soft, golden hour glow.",
    "sadness": "in a muted, melancholic art style with cool tones, like a rainy day seen through a window.",
    "anger": "in a high-contrast, dramatic art style with sharp lines and stormy, intense lighting.",
    "disgust": "in a gritty, abstract expressionist style with a desaturated and slightly unsettling color palette.",
    "fear": "in a moody, low-light chiaroscuro style, with long shadows, fog, and a suspenseful atmosphere.",
    "surprise": "in a playful and whimsical art style, with bright, popping colors and a sense of wonder.",
}


def build_image_url(prompt: str, emotion: str) -> str:
    """
    Generates an image using the ClipDrop API and returns it as a Base64 Data URL.
    Returns a placeholder URL if the API call fails.
    """
    if not CLIPDROP_API_KEY:
        current_app.logger.error("ClipDrop API key not set. Cannot generate image.")
        return "/static/images/placeholder_error.png"

    full_prompt = (
        f"A digital painting expressing the emotion of '{emotion}', {STYLE.get(emotion, '')}. "
        f"The painting is a visual metaphor for the following thought: '{prompt}'"
    )

    headers = {
        'x-api-key': CLIPDROP_API_KEY
    }
    # ClipDrop uses multipart/form-data, so the prompt is sent in the 'files' parameter.
    payload = {
        'prompt': (None, full_prompt)
    }

    try:
        current_app.logger.info(f"Generating image with ClipDrop prompt: {full_prompt}")

        response = requests.post(CLIPDROP_API_URL, headers=headers, files=payload, timeout=45)

        if response.ok:
            # ClipDrop returns raw image data, which must be Base64 encoded to be used in an <img> tag.
            image_bytes = response.content
            base64_data = base64.b64encode(image_bytes).decode('utf-8')
            return f"data:image/png;base64,{base64_data}"
        else:
            error_message = response.json().get('error', response.text)
            current_app.logger.error(f"ClipDrop API Error: {response.status_code} - {error_message}")
            return "/static/images/placeholder_error.png"

    except requests.exceptions.RequestException as e:
        # Handle network-level errors like timeouts or connection issues.
        current_app.logger.error(f"A network error occurred with the ClipDrop API: {e}")
        return "/static/images/placeholder_error.png"
