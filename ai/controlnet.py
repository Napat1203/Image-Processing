"""Generate an image that follows a pose.

A photo is sent with openpose so Forge extracts the pose.
A skeleton from the camera is sent with none so Forge does not
extract the pose a second time. The ControlNet model is used either way.
"""

import base64

import requests

from ai.forge_client import (
    FORGE_URL,
    ForgeError,
    _generate_lock,
    build_txt2img_payload,
    image_from_response,
    prepare_prompt,
)

CONTROLNET_MODEL = "control_v11p_sd15_openpose"
CONTROL_MODULE = "openpose"


def generate_from_pose(
    prompt,
    pose_image,
    already_skeleton=False,
    base_url=None,
    session=None,
    translator=None,
):
    """Return a base64 image whose pose follows pose_image."""
    if not pose_image:
        raise ForgeError("Pose image is empty")
    module = "none" if already_skeleton else CONTROL_MODULE
    with _generate_lock:
        text = prepare_prompt(prompt, translator=translator)
        payload = build_txt2img_payload(text)
        payload["alwayson_scripts"] = {
            "ControlNet": {
                "args": [
                    {
                        "enabled": True,
                        "module": module,
                        "model": CONTROLNET_MODEL,
                        "weight": 1.0,
                        "image": base64.b64encode(pose_image).decode("ascii"),
                    }
                ]
            }
        }
        url = (base_url or FORGE_URL).rstrip("/") + "/sdapi/v1/txt2img"
        http = session or requests
        try:
            response = http.post(url, json=payload, timeout=600)
        except requests.RequestException as exc:
            raise ForgeError("Start Forge first, then generate") from exc
        if response.status_code >= 400:
            raise ForgeError("Forge is not accepting requests. Launch it with --api")
        return image_from_response(response.json())