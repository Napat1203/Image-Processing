"""Send a prompt to Forge and return the generated image.

Thai prompts are translated to English first. Image size and step count stay
in this file because the page does not let the user change them.
"""

import os
import threading

import requests

# Point FORGE_URL at the notebook on presentation day without editing this file.
# This Forge serves plain http. An https URL fails the connection.
FORGE_URL = os.environ.get("FORGE_URL", "http://127.0.0.1:7860").rstrip("/")

# One drawing at a time. A second caller waits here instead of starting Forge twice.
_generate_lock = threading.Lock()

class ForgeError(Exception):
    pass


def prepare_prompt(prompt, translator=None):
    text = (prompt or "").strip()
    if not text:
        raise ForgeError("Enter a prompt first")
    if has_thai(text):
        translate = translator or opus_translate
        return translate(text)
    return text


def has_thai(text):
    # U+0E00 to U+0E7F is the Thai block. The backslash before u is required.
    return any("\u0e00" <= char <= "\u0e7f" for char in text)


def opus_translate(text):
    tokenizer = opus_translate.tokenizer
    model = opus_translate.model
    # Load once, then keep the model on this function so later calls skip the load.
    if tokenizer is None or model is None:
        from transformers import MarianMTModel, MarianTokenizer

        tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-th-en")
        model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-th-en")
        opus_translate.tokenizer = tokenizer
        opus_translate.model = model
    token = tokenizer(text, return_tensors="pt", truncation=True)
    output = model.generate(**token)
    translated = tokenizer.decode(output[0], skip_special_tokens=True).strip()
    if not translated:
        raise ForgeError("Could not translate the prompt")
    return translated


opus_translate.tokenizer = None
opus_translate.model = None


def build_txt2img_payload(prompt):
    # These match the MeinaMix settings that already worked on a 6GB card.
    return {
        "prompt": prompt,
        "negative_prompt": "low quality, bad anatomy, blurry",
        "steps": 20,
        "width": 512,
        "height": 512,
        "cfg_scale": 6,
        "sampler_name": "Euler a",
    }


def generate_image(prompt, base_url=None, session=None, translator=None):
    with _generate_lock:
        text = prepare_prompt(prompt, translator=translator)
        payload = build_txt2img_payload(text)
        url = (base_url or FORGE_URL).rstrip("/") + "/sdapi/v1/txt2img"
        http = session or requests
        try:
            response = http.post(url, json=payload, timeout=180)
        except requests.RequestException as exc:
            raise ForgeError("Start Forge first, then generate") from exc
        if response.status_code >= 400:
            raise ForgeError("Forge is not accepting requests. Launch it with --api")
        return image_from_response(response.json())


def image_from_response(data):
    images = data.get("images") if isinstance(data, dict) else None
    if not images:
        raise ForgeError("Forge did not return an image")
    return images[0]
